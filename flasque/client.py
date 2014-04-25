# -*- coding: utf8 -*-

from __future__ import print_function

import json
import uuid
import random
import Queue
import requests
import threading


class ThreadQueue(threading.Thread):

    def __init__(self, api, qname, *args, **kwargs):
        super(ThreadQueue, self).__init__(*args, **kwargs)
        self.url = api + "/queue/" + qname
        self.q = Queue.Queue()
        self.daemon = True

    def run(self):
        raise NotImplementedError

    def get(self, *args, **kwargs):
        return self.q.get(*args, **kwargs)

    def get_nowait(self, *args, **kwargs):
        return self.q.get_nowait(*args, **kwargs)

    def put(self, *args, **kwargs):
        return self.q.put(*args, **kwargs)

    def task_done(self):
        return self.q.task_done()


class Producer(ThreadQueue):

    def run(self):
        while True:
            data = self.q.get()
            requests.post(self.url, data=data)


class Consumer(ThreadQueue):

    def run(self):
        while True:
            res = requests.get(self.url, stream=True)
            for line in res.iter_lines():
                continue
            res = json.loads(line)
            self.q.put(res["data"])
            self.q.join()
            requests.delete(self.url + "?msgid=" + res["msgid"])


def main(api, queue_in, queue_out):
    consumer = Consumer(api, queue_in)
    producer = Producer(api, queue_out)
    producer.start()
    consumer.start()
    while True:
        try:
            data = consumer.get_nowait()
        except Queue.Empty:
            pass
        else:
            print("recv", data)
            consumer.task_done()
        if random.randint(0, 100000) == 1:
            data = uuid.uuid4().hex
            print("send", data)
            producer.put(data)
