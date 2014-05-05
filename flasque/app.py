# -*- coding: utf8 -*-

import redis
from flask import Flask
from werkzeug.local import LocalProxy

app = Flask(__name__)
app._db = redis.Redis(decode_responses=True)
app.db = db = LocalProxy(lambda: app._db)
app.secret_key = "polichinelle"
