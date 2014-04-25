# -*- coding: utf8 -*-

from werkzeug.local import LocalProxy
from flask import current_app

db = LocalProxy(lambda: current_app.db)
