# -*- coding: utf8 -*-

from __future__ import unicode_literals

import six

from flask import request

from flasque.views import QueueApi, ChannelApi, LogsApi, index, stream_status
from flasque.app import app

# Workaround TypeError: __name__ must be set to a string object
if six.PY3:
    queue_view = QueueApi.as_view("queue")
    channel_view = ChannelApi.as_view("channel")
    logs_view = LogsApi.as_view("logs")
else:
    queue_view = QueueApi.as_view(b"queue")
    channel_view = ChannelApi.as_view(b"channel")
    logs_view = LogsApi.as_view(b"logs")

app.add_url_rule(
    "/queue/",
    view_func=queue_view,
    methods=["GET", "POST", "DELETE"],
)
app.add_url_rule(
    "/channel/",
    view_func=channel_view,
    methods=["GET", "POST"],
)
app.add_url_rule(
    "/log/",
    view_func=logs_view,
    methods=["GET", "POST"],
)
app.add_url_rule("/", view_func=index, methods=["GET"])
app.add_url_rule("/status", view_func=stream_status, methods=["GET"])


@app.before_request
def handle_stream_post():
    # workaround https://github.com/mitsuhiko/flask/issues/367
    if request.method == "POST":
        path = request.path[:9]
        if path == "channel":
            return ChannelApi.post(ChannelApi.PREFIX)
        elif path == "/log/":
            return LogsApi.post(LogsApi.PREFIX)
