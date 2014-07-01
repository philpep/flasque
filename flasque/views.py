# -*- coding: utf8 -*-

from __future__ import unicode_literals

import json
import os

from flask import request, Response, jsonify, make_response
from flask.views import MethodView

import flasque.queue


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
            flasque.queue.iter_messages(channels, pending=pending),
            once=True, json_data=True)

    def post(self):
        return jsonify({
            "id": flasque.queue.put(self.get_channel(), request.data.decode()),
        })

    def delete(self):
        msgid = request.args.get("id")
        flasque.queue.delete_message(self.get_channel(), msgid)
        return jsonify({})


class ChannelApi(BaseApi):
    PREFIX = "channel"

    def get(self):
        return sse_response(
            flasque.queue.iter_messages_pubsub(
                self.get_channel(), prefix=self.PREFIX))

    @staticmethod
    def post(prefix):
        channel = ChannelApi.get_channel()
        for item in request.environ["wsgi.input"]:
            for line in item.splitlines():
                if line:
                    flasque.queue.publish(
                        channel, line.decode(), prefix=prefix)
        return jsonify({})


class LogsApi(ChannelApi):
    PREFIX = "log"


def stream_status():
    return sse_response(flasque.queue.iter_status(), json_data=True)


def index():
    filename = os.path.join(os.path.dirname(__file__), "static",
                            "flasque.html")
    return make_response(open(filename).read())
