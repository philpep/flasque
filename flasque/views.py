# -*- coding: utf8 -*-

import json
from flask import request, Response, jsonify, render_template
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
            yield "%s\n\n" % (data,)


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
    def get_names(q=None):
        if q is None:
            names = request.args.getlist("q")
        else:
            names = [q]
        return names


class QueueApi(BaseApi):

    def get(self, q):
        names = self.get_names(q)
        return Response(
            stream_once(Queue().get_message, names),
            content_type="text/event-stream")

    def post(self, q):
        return jsonify({
            "msgid": Queue().put(q, request.data),
        })

    def delete(self, q):
        msgid = request.args.get("msgid")
        Queue().delete_message(q, msgid)
        return jsonify({})


class StreamApi(BaseApi):

    def get(self):
        names = self.get_names()
        return Response(
            stream_forever(Queue.get_message, names, pubsub=True),
            content_type="text/event-stream")


def stream_status():
    def stream():
        for status in Queue().iter_status():
            if status is not None:
                yield "data: %s\n\n" % (json.dumps(status),)
            else:
                yield "data: \n\n"
    return Response(stream(), content_type="text/event-stream")


def index():
    return render_template("index.html")
