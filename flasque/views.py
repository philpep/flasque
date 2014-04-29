# -*- coding: utf8 -*-

import json
from flask import request, Response, jsonify, render_template
from flask.views import MethodView
from .queue import Queue


def sse_response(iterator, once=False, json_data=False):
    def _sse():
        # partial sse implementation
        for data in iterator:
            if data is None:
                # keep alive
                yield "data: \n\n"
            else:
                if json_data:
                    data = json.dumps(data)
                yield "data: %s\n\n" % (data,)
                if once:
                    raise StopIteration
    return Response(_sse(), content_type="text/event-stream")


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
        return sse_response(
            Queue().iter_messages(names), once=True, json_data=True)

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
        return sse_response(Queue().iter_messages(names, pubsub=True))


def stream_status():
    return sse_response(Queue().iter_status(), json_data=True)


def index():
    return render_template("index.html")
