# -*- coding: utf8 -*-

import json
import time
import Queue
import requests
import threading


class StopThreadException(Exception):
    pass


class Message(object):

    def __init__(self, msgid, channel, data):
        self.id = msgid
        self.channel = channel
        self.data = data
        super(Message, self).__init__()

    def __str__(self):
        return self.data


class ThreadQueue(threading.Thread):

    def __init__(self, conn, api, qname, *args, **kwargs):
        super(ThreadQueue, self).__init__(*args, **kwargs)
        self.conn = conn
        self.api = api
        self.qname = qname
        self.q = Queue.Queue()
        self.daemon = True
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

    def get(self, *args, **kwargs):
        js = self.q.get(*args, **kwargs)
        if js is not None:
            return Message(js["id"], js["channel"], js["data"])

    def put(self, *args, **kwargs):
        return self.q.put(*args, **kwargs)

    def task_done(self):
        return self.q.task_done()

    def stop(self):
        self._stop.set()

    def close(self):
        self.conn.threads.remove(self)
        self.stop()
        self.join()


class Producer(ThreadQueue):

    def loop(self):
        try:
            data = self.q.get(timeout=1)
        except Queue.Empty:
            pass
        else:
            self.make_request(
                requests.post,
                self.api + "/queue/" + self.qname,
                data=data,
            )
        if self._stop.is_set():
            raise StopThreadException


class Consumer(ThreadQueue):

    def loop(self):
        res = self.make_request(
            requests.get,
            self.api + "/queue/",
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
        self.make_request(
            requests.delete,
            self.api + "/queue/" + msg["channel"],
            params={"id": msg["id"]},
        )


class ChannelConsumer(ThreadQueue):

    def loop(self):
        res = self.make_request(
            requests.get,
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
                yield "data: %s\n\n" % (data,)
            if self._stop.is_set():
                raise StopThreadException

    def loop(self):
        self.make_request(
            requests.post,
            self.api + "/channel/" + self.qname,
            data=self.generate(),
        )


class Connection(object):

    def __init__(self, api="http://localhost:5000"):
        self.api = api
        self.threads = []
        super(Connection, self).__init__()

    def register(self, thread):
        thread.start()
        self.threads.append(thread)
        return thread

    def Producer(self, qname):
        return self.register(Producer(self, self.api, qname))

    def Consumer(self, *qname):
        return self.register(Consumer(self, self.api, qname))

    def ChannelConsumer(self, *qname):
        return self.register(ChannelConsumer(self, self.api, qname))

    def ChannelProducer(self, qname):
        return self.register(ChannelProducer(self, self.api, qname))

    def close(self):
        for th in self.threads:
            th.stop()
        for th in self.threads:
            th.join()
        self.threads = []

    def remove(self, thread):
        self.threads.remove(thread)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
