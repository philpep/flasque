# -*- coding: utf8 -*-

from .views import QueueApi, StreamApi, index, stream_status
from .app import app

queue_view = QueueApi.as_view("queue")
stream_view = StreamApi.as_view("stream")

app.add_url_rule(
    "/queue/",
    defaults={"q": None},
    view_func=queue_view,
    methods=["GET"],
)
app.add_url_rule(
    "/queue/<string:q>",
    view_func=queue_view,
    methods=["GET", "POST", "DELETE"],
)
app.add_url_rule("/stream/", view_func=stream_view, methods=["GET"])
app.add_url_rule("/", view_func=index, methods=["GET"])
app.add_url_rule("/status", view_func=stream_status, methods=["GET"])
