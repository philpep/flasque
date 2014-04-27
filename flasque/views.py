# -*- coding: utf8 -*-

import json
from flask import request, Response, jsonify
from flask.views import MethodView
from .queue import Queue


def stream(func, *args, **kwargs):
    while True:
        data = func(*args, **kwargs)
        if data is None:
            yield
        else:
            yield data


def stream_forever(func, *args, **kwargs):
    for data in stream(func, *args, **kwargs):
        if data is None:
            # keep alive
            yield "\n\n"
        else:
            yield "%s\n\n" % (json.dumps(data),)


def stream_once(func, *args, **kwargs):
    for data in stream(func, *args, **kwargs):
        if data is None:
            # keep alive
            yield "\n\n"
        else:
            yield "%s" % (json.dumps(data),)
            raise StopIteration


class BaseApi(MethodView):

    @staticmethod
    def get_qs(q):
        if q is None:
            qs = request.args.getlist("q")
        else:
            qs = [q]
        return qs


class QueueApi(BaseApi):

    def get(self, q):
        return Response(
            stream_once(Queue.get_message, self.get_qs(q)),
            content_type="text/event-stream")

    def post(self, q):
        return jsonify({
            "msgid": Queue(q).put(request.data),
        })

    def delete(self, q):
        msgid = request.args.get("msgid")
        Queue(q).delete_message(msgid)
        return jsonify({})


class StreamApi(BaseApi):

    def get(self):
        pubsub = Queue.listen(self.get_qs(None))
        return Response(
            stream_forever(Queue.pubsub_get_message, pubsub),
            content_type="text/event-stream")
