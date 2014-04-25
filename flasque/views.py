# -*- coding: utf8 -*-

import json
from flask.views import MethodView, Response, request, jsonify
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

    def get(self, name):
        queue = Queue(name)
        return self.stream_view(queue.get_message)

    def post(self, name):
        return jsonify({
            "msgid": Queue(name).put(request.data),
        })

    def delete(self, name):
        msgid = request.args.get("msgid")
        Queue(name).delete_message(msgid)
        return jsonify({})
