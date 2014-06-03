# -*- coding: utf8 -*-

from __future__ import unicode_literals

import json
import os

from flask import request, Response, jsonify, make_response
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
    def get_channels(channel=None):
        if channel is None:
            channels = request.args.getlist("channel")
        else:
            channels = [channel]
        return channels


class QueueApi(BaseApi):

    def get(self, channel):
        channels = self.get_channels(channel)
        if request.args.get("pending", "0") == "1":
            pending = True
        else:
            pending = False
        return sse_response(
            Queue().iter_messages(channels, pending=pending),
            once=True, json_data=True)

    def post(self, channel):
        return jsonify({
            "id": Queue().put(channel, request.data.decode()),
        })

    def delete(self, channel):
        msgid = request.args.get("id")
        Queue().delete_message(channel, msgid)
        return jsonify({})


class ChannelApi(BaseApi):

    def get(self, channel):
        return sse_response(
            Queue().iter_messages(self.get_channels(channel), pubsub=True))

    @staticmethod
    def post(channel):
        channel = ChannelApi.get_channels(channel)[0]
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
