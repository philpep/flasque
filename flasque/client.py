# -*- coding: utf8 -*-

import json
import time
import Queue
import requests
import threading


class ThreadQueue(threading.Thread):

    def __init__(self, api, qname, *args, **kwargs):
        super(ThreadQueue, self).__init__(*args, **kwargs)
        self.api = api
        self.qname = qname
        self.q = Queue.Queue()
        self.daemon = True
        self._stop = threading.Event()

    def run(self):
        while True:
            self.loop()

    @staticmethod
    def make_request(func, *args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException:
                time.sleep(1)

    def get(self, *args, **kwargs):
        return self.q.get(*args, **kwargs)

    def put(self, *args, **kwargs):
        return self.q.put(*args, **kwargs)

    def task_done(self):
        return self.q.task_done()

    def stop(self):
        self._stop.set()

    def close(self):
        self._stop()
        self.join()


class Producer(ThreadQueue):

    def loop(self):
        try:
            data = self.get(timeout=1)
        except Queue.Empty:
            pass
        else:
            self.make_request(
                requests.post,
                self.api + "/queue/" + self.qname,
                data=data,
            )
        if self._stop.is_set():
            return


class Consumer(ThreadQueue):

    def loop(self):
        res = self.make_request(
            requests.get,
            self.api + "/queue/",
            params={"q": self.qname},
            stream=True,
        )
        for line in res.iter_lines(chunk_size=1):
            if self._stop.is_set():
                return
        res = json.loads(line)
        self.q.put(res["data"])
        self.q.join()
        self.make_request(
            requests.delete,
            self.api + "/queue/" + res["q"],
            params={"msgid": res["msgid"]},
        )


class Connection(object):

    def __init__(self, api="http://localhost:5000"):
        self.api = api
        self.threads = []
        super(Connection, self).__init__()

    def Producer(self, qname):
        producer = Producer(self.api, qname)
        producer.start()
        self.threads.append(producer)
        return producer

    def Consumer(self, *qname):
        consumer = Consumer(self.api, qname)
        consumer.start()
        self.threads.append(consumer)
        return consumer

    def close(self):
        for th in self.threads:
            th.stop()
        for th in self.threads:
            th.join()
        self.threads = []

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
