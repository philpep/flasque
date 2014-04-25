# -*- coding: utf8 -*-

import argparse


def get_app():
    from .urls import *
    from .app import app
    return app


def server(args):
    from gevent import monkey
    from gevent.wsgi import WSGIServer
    monkey.patch_all()
    host, port = args.bind.split(":")
    WSGIServer((host, int(port)), get_app()).serve_forever()


def client(args):
    from .client import main
    main(args.api, args.queue_in, args.queue_out)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_server = subparsers.add_parser("server")
    parser_server.set_defaults(func=server)
    parser_server.add_argument("--bind", help="bind address",
                               default="127.0.0.1:5000")

    parser_client = subparsers.add_parser("client")
    parser_client.set_defaults(func=client)
    parser_client.add_argument("--api", help="API url",
                               default="http://127.0.0.1:5000")
    parser_client.add_argument("queue_in", default="queue_in")
    parser_client.add_argument("queue_out", default="queue_out")

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
