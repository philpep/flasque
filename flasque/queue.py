# -*- coding: utf8 -*-

import uuid
import json
import time
from .app import db


def get_uuid():
    return uuid.uuid4().hex


class Queue(object):

    def __init__(self):
        self._pubsub = None
        super(Queue, self).__init__()

    def put(self, channel, data):
        msgid = get_uuid()
        prefix = "queue:" + channel
        db.pipeline().\
            sadd("queues", channel).\
            set(prefix + ":message:" + msgid, data).\
            rpush(prefix, msgid).\
            publish("stream:" + channel, json.dumps({
                "id": msgid,
                "channel": channel,
                "data": data,
            })).\
            incr(prefix + ":count").\
            publish("queues:status", channel).\
            execute()
        return msgid

    def get(self, channels, timeout=1):
        return db.blpop(
            ["queue:" + channel for channel in channels],
            timeout=timeout
        )

    def get_message(self, channels, pubsub=False, timeout=1):
        if pubsub:
            self.subscribe([
                "stream:" + channel for channel in channels])
            return self.get_message_pubsub(timeout=timeout)
        else:
            elm = self.get(channels, timeout=timeout)
            if elm is not None:
                prefix, msgid = elm
                channel = prefix.split(":", 1)[1]
                _, data, _ = db.pipeline().\
                    lpush(prefix, msgid).\
                    get(prefix + ":message:" + msgid).\
                    publish("queues:status", channel).\
                    execute()
                return {
                    "id": msgid,
                    "channel": channel,
                    "data": data,
                }

    def iter_messages(self, *args, **kwargs):
        while True:
            yield self.get_message(*args, **kwargs)

    def delete_message(self, channel, msgid):
        prefix = "queue:" + channel
        db.pipeline().\
            lrem(prefix, msgid).\
            delete(prefix + ":message:" + msgid).\
            incr(prefix + ":total").\
            decr(prefix + ":count").\
            publish("queues:status", channel).\
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

    def publish(self, channel, data):
        db.publish("stream:" + channel, json.dumps({
            "id": None,
            "channel": channel,
            "data": data,
        }))

    def get_status(self, channel=None):
        if channel is None:
            channels = db.smembers("queues")
        else:
            channels = [channel]

        if not channel:
            # no queues
            return []

        keys = []
        for channel in channels:
            keys.extend([
                "queue:" + channel + ":count",
                "queue:" + channel + ":total",
            ])
        values = db.mget(keys)
        i = 0
        status = []
        for channel in channels:
            status.append((channels, values[i], values[i+1]))
            i += 2
        return status

    def iter_status(self):
        self.subscribe(["queues:status"])
        yield self.get_status()
        while True:
            channel = self.get_message_pubsub()
            if channel is not None:
                yield self.get_status(channel)
            else:
                yield
