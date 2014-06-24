# -*- coding: utf8 -*-

from __future__ import unicode_literals

import json
import time
import Queue
import requests
import threading
import logging


class StopThreadException(Exception):
    pass


class FlasqueHandler(logging.Handler):

    def __init__(self, channel, api="http://localhost:5000"):
        self.producer = ChannelProducer(api, channel)
        self.producer.start()
        logging.Handler.__init__(self)

    def close(self):
        self.producer.stop()
        self.producer.join()

    def emit(self, record):
        self.producer.put(self.format(record))


class Message(object):

    def __init__(self, msgid, channel, data):
        self.id = msgid
        self.channel = channel
        self.data = data
        super(Message, self).__init__()

    def __str__(self):
        return self.data


class ThreadQueue(threading.Thread):

    def __init__(self, api, qname):
        super(ThreadQueue, self).__init__()
        self.api = api
        self.qname = qname
        self.q = Queue.Queue()
        self.daemon = True
        self.session = requests.Session()
        self._stop = threading.Event()

    def run(self):
        while True:
            try:
                self.loop()
            except StopThreadException:
                break
            except requests.exceptions.RequestException:
                continue

    def make_request(self, func, *args, **kwargs):
        while True:
            try:
                res = func(*args, **kwargs)
            except requests.exceptions.RequestException:
                pass
            else:
                if res.status_code == 200:
                    return res
            if self._stop.is_set():
                raise StopThreadException
            time.sleep(1)

    def get(self, timeout=None):
        if timeout is None:
            while True:
                try:
                    js = self.q.get(timeout=1)
                except Queue.Empty:
                    pass
                else:
                    break
        else:
            js = self.q.get(timeout=timeout)
        if js is not None:
            return Message(js["id"], js["channel"], js["data"])

    def put(self, *args, **kwargs):
        return self.q.put(*args, **kwargs)

    def task_done(self):
        return self.q.task_done()

    def stop(self):
        self._stop.set()


class Producer(ThreadQueue):

    def loop(self):
        try:
            data = self.q.get(timeout=1)
        except Queue.Empty:
            pass
        else:
            self.make_request(
                self.session.post,
                self.api + "/queue/",
                params={"channel": self.qname},
                data=data,
            )
        if self._stop.is_set():
            raise StopThreadException


class Consumer(ThreadQueue):

    def __init__(self, api, qname, pending=False):
        super(Consumer, self).__init__(api, qname)
        self.params = {"channel": self.qname}
        if pending:
            self.params["pending"] = "1"

    def loop(self):
        res = self.make_request(
            self.session.get,
            self.api + "/queue/",
            params=self.params,
            stream=True,
        )
        for line in res.iter_lines(chunk_size=1):
            if self._stop.is_set():
                raise StopThreadException
            if line and line[6:]:
                msg = json.loads(line[6:])
        self.q.put(msg)
        self.q.join()
        self.make_request(
            self.session.delete,
            self.api + "/queue/",
            params={
                "id": msg["id"],
                "channel": msg["channel"],
            },
        )


class ChannelConsumer(ThreadQueue):

    def loop(self):
        res = self.make_request(
            self.session.get,
            self.api + "/channel/",
            params={"channel": self.qname},
            stream=True,
        )
        for line in res.iter_lines(chunk_size=1):
            if self._stop.is_set():
                raise StopThreadException
            if line and line[6:]:
                msg = json.loads(line[6:])
                self.q.put(msg)
                self.q.join()


class ChannelProducer(ThreadQueue):

    def generate(self):
        while True:
            try:
                data = self.q.get(timeout=1)
            except Queue.Empty:
                pass
            else:
                yield "%s\n\n" % (data,)
            if self._stop.is_set():
                raise StopThreadException

    def loop(self):
        self.make_request(
            self.session.post,
            self.api + "/channel/",
            params={"channel": self.qname},
            data=self.generate(),
        )


class Connection(object):

    def __init__(self, api="http://localhost:5000"):
        self.api = api
        self.threads = set()
        super(Connection, self).__init__()

    def register(self, thread):
        thread.start()
        self.threads.add(thread)
        return thread

    def Producer(self, qname):
        return self.register(Producer(self.api, qname))

    def Consumer(self, qname, pending=False):
        return self.register(Consumer(self.api, qname, pending=pending))

    def ChannelConsumer(self, qname):
        return self.register(ChannelConsumer(self.api, qname))

    def ChannelProducer(self, qname):
        return self.register(ChannelProducer(self.api, qname))

    def close(self):
        for thread in self.threads:
            thread.stop()
        for thread in self.threads:
            thread.join()
        self.threads = set()

    def remove(self, thread):
        self.threads.remove(thread)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
