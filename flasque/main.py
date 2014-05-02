# -*- coding: utf8 -*-

import argparse
from .urls import app


def server(args):
    from gevent import monkey
    from gevent.wsgi import WSGIServer
    monkey.patch_all()
    host, port = args.bind.split(":")
    print("listen on " + args.bind)
    WSGIServer((host, int(port)), app).serve_forever()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bind", nargs="?", help="bind address",
                        default="127.0.0.1:5000")
    args = parser.parse_args()
    server(args)


if __name__ == "__main__":
    main()
