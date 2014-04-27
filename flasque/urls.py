# -*- coding: utf8 -*-

from .views import QueueApi
from .app import app

queue_view = QueueApi.as_view("queue")

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
