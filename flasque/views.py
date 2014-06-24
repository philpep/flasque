# -*- coding: utf8 -*-

from __future__ import unicode_literals

import json
import os

from flask import request, Response, jsonify, make_response
from flask.views import MethodView

from flasque.queue import Queue


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
    def get_channels():
        # TODO: validation
        return request.args.getlist("channel")

    @staticmethod
    def get_channel():
        # TODO: validation
        return request.args.get("channel")


class QueueApi(BaseApi):

    def get(self):
        channels = self.get_channels()
        if request.args.get("pending", "0") == "1":
            pending = True
        else:
            pending = False
        return sse_response(
            Queue().iter_messages(channels, pending=pending),
            once=True, json_data=True)

    def post(self):
        return jsonify({
            "id": Queue().put(self.get_channel(), request.data.decode()),
        })

    def delete(self):
        msgid = request.args.get("id")
        Queue().delete_message(self.get_channel(), msgid)
        return jsonify({})


class ChannelApi(BaseApi):

    def get(self):
        return sse_response(
            Queue().iter_messages(self.get_channel(), pubsub=True))

    @staticmethod
    def post():
        channel = ChannelApi.get_channel()
        q = Queue()
        for item in request.environ["wsgi.input"]:
            for line in item.splitlines():
                if line:
                    q.publish(channel, line.decode())
        return jsonify({})


def stream_status():
    return sse_response(Queue().iter_status(), json_data=True)


def index():
    filename = os.path.join(os.path.dirname(__file__), "static",
                            "flasque.html")
    return make_response(open(filename).read())
