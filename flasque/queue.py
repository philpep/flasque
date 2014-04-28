# -*- coding: utf8 -*-

import uuid
import json
import time
from .app import db


class Queue(object):

    def __init__(self):
        self._pubsub = None
        super(Queue, self).__init__()

    def put(self, name, data):
        msgid = uuid.uuid4().hex
        prefix = "queue:" + name
        db.pipeline().\
            sadd("queues", name).\
            set(prefix + ":message:" + msgid, data).\
            rpush(prefix, msgid).\
            publish(prefix + ":stream", json.dumps({
                "msgid": msgid,
                "q": name,
                "data": data,
            })).\
            incr(prefix + ":count").\
            publish("queues:status", name).\
            execute()
        return msgid

    def get(self, names, timeout=1):
        return db.blpop(["queue:" + name for name in names], timeout=timeout)

    def get_message(self, names, pubsub=False, timeout=1):
        if pubsub:
            self.subscribe([
                "queue:" + name + ":stream" for name in names])
            return self.get_message_pubsub(timeout=timeout)
        else:
            elm = self.get(names, timeout=timeout)
            if elm is not None:
                prefix, msgid = elm
                name = prefix.split(":", 1)[1]
                _, data, _ = db.pipeline().\
                    lpush(prefix, msgid).\
                    get(prefix + ":message:" + msgid).\
                    publish("queues:status", name).\
                    execute()
                return {
                    "msgid": msgid,
                    "q": name,
                    "data": data,
                }

    def delete_message(self, name, msgid):
        prefix = "queue:" + name
        db.pipeline().\
            lrem(prefix, msgid).\
            delete(prefix + ":message:" + msgid).\
            incr(prefix + ":total").\
            decr(prefix + ":count").\
            publish("queues:status", name).\
            execute()

    def subscribe(self, keys):
        if self._pubsub is None:
            self._pubsub = db.pubsub()
            self._pubsub.subscribe(keys)

    def get_message_pubsub(self, timeout=1):
        sleep_time = 0
        while sleep_time < timeout:
            message = self._pubsub.get_message()
            if message is not None and message["type"] == "message":
                return message["data"]
            elif message is None:
                time.sleep(0.1)
                sleep_time += 0.1

    def get_status(self, name=None):
        if name is None:
            names = db.smembers("queues")
        else:
            names = [name]

        if not names:
            # no queues
            return []

        keys = []
        for name in names:
            keys.extend([
                "queue:" + name + ":count",
                "queue:" + name + ":total",
            ])
        values = db.mget(keys)
        i = 0
        status = []
        for name in names:
            status.append((name, values[i], values[i+1]))
            i += 2
        return status

    def iter_status(self):
        self.subscribe(["queues:status"])
        yield self.get_status()
        while True:
            name = self.get_message_pubsub()
            if name is not None:
                yield self.get_status(name)
            else:
                yield
