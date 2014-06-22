# -*- coding: utf8 -*-

from __future__ import unicode_literals
from __future__ import print_function

from flask.ext.script import Manager

from flasque.urls import app


manager = Manager(app)


@manager.command
def runserver(host="127.0.0.1", port="5000", debug=False):
    from gevent import monkey
    from gevent.wsgi import WSGIServer
    monkey.patch_all()
    app.debug = debug
    print(" * Running on http://%s:%s" % (host, port))
    WSGIServer((host, int(port)), app).serve_forever()


def main():
    manager.run()

if __name__ == "__main__":
    main()
