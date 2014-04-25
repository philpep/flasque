# -*- coding: utf8 -*-

import redis
from gevent import monkey
from gevent.wsgi import WSGIServer
from flask import Flask
from .views import QueueApi

monkey.patch_all()
app = Flask(__name__)
app.db = redis.Redis()
app.add_url_rule("/queue/<string:name>", view_func=QueueApi.as_view("queue"))


def main():
    app.debug = True
    WSGIServer(('', 5000), app).serve_forever()

if __name__ == "__main__":
    main()
