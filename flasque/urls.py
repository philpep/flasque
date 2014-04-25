# -*- coding: utf8 -*-

from .views import QueueApi
from .app import app

app.add_url_rule("/queue/<string:name>", view_func=QueueApi.as_view("queue"))
