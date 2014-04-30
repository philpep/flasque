# -*- coding: utf8 -*-

from .views import QueueApi, ChannelApi, index, stream_status
from flask import request
from .app import app

queue_view = QueueApi.as_view("queue")
channel_view = ChannelApi.as_view("channel")

app.add_url_rule(
    "/queue/",
    defaults={"channel": None},
    view_func=queue_view,
    methods=["GET"],
)
app.add_url_rule(
    "/queue/<string:channel>",
    view_func=queue_view,
    methods=["GET", "POST", "DELETE"],
)
app.add_url_rule(
    "/channel/",
    defaults={"channel": None},
    view_func=channel_view,
    methods=["GET"],
)
app.add_url_rule(
    "/channel/<string:channel>",
    view_func=channel_view,
    methods=["GET", "POST"],
)
app.add_url_rule("/", view_func=index, methods=["GET"])
app.add_url_rule("/status", view_func=stream_status, methods=["GET"])


@app.before_request
def handle_stream_post():
    # workaround https://github.com/mitsuhiko/flask/issues/367
    if request.method == "POST" and request.path[:9] == "/channel/":
        return ChannelApi.post(request.path[9:] or None)
