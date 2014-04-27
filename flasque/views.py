# -*- coding: utf8 -*-

import json
from flask import request, Response, jsonify
from flask.views import MethodView
from .queue import Queue


class QueueApi(MethodView):

    def stream_view(self, func, *args, **kwargs):
        def stream():
            while True:
                data = func(*args, **kwargs)
                if data is None:
                    # keep alive
                    yield "\n\n"
                else:
                    yield json.dumps(data)
                    raise StopIteration
        return Response(stream(), content_type="text/event-stream")

    @staticmethod
    def get_qs(q):
        if q is None:
            qs = request.args.getlist("q")
        else:
            qs = [q]
        return qs

    def get(self, q):
        return self.stream_view(Queue.get_message, self.get_qs(q))

    def post(self, q):
        return jsonify({
            "msgid": Queue(q).put(request.data),
        })

    def delete(self, q):
        msgid = request.args.get("msgid")
        Queue(q).delete_message(msgid)
        return jsonify({})
