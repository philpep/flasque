# -*- coding: utf8 -*-

from __future__ import unicode_literals

import json
import time

from flasque.app import db
from flasque.utils import get_uuid


def put(channel, data):
    msgid = get_uuid()
    prefix = "queue:" + channel
    db.pipeline().\
        sadd("queues", channel).\
        sadd("channels", channel).\
        set(prefix + ":message:" + msgid, data).\
        rpush(prefix, msgid).\
        publish("channel:" + channel, json.dumps({
            "id": msgid,
            "channel": channel,
            "data": data,
        })).\
        incr(prefix + ":count").\
        publish("queues:status", channel).\
        execute()
    return msgid


def get_message(channels, pending=False, timeout=1):
    queues = []
    for channel in channels:
        if pending:
            queues.extend([
                "queue:" + channel + ":pending",
                "queue:" + channel,
            ])
        else:
            queues.append("queue:" + channel)

    elm = db.blpop(queues, timeout=1)
    if elm is not None:
        queue, msgid = elm
        channel = queue.split(":")[1]
        pending = "queue:" + channel + ":pending"
        pipe = db.pipeline().\
            get("queue:" + channel + ":message:" + msgid).\
            lpush(pending, msgid).\
            publish("queues:status", channel)
        if queue != pending:
            pipe = pipe.\
                decr(queue + ":count").\
                incr(pending + ":count")
        data = pipe.execute()[0]
        return {
            "id": msgid,
            "channel": channel,
            "data": data,
        }


def iter_messages(*args, **kwargs):
    while True:
        yield get_message(*args, **kwargs)


def delete_message(channel, msgid):
    prefix = "queue:" + channel
    pending, _ = db.pipeline().\
        lrem(prefix + ":pending", msgid).\
        delete(prefix + ":message:" + msgid).\
        execute()
    if pending:
        db.pipeline().\
            incr(prefix + ":total").\
            decr(prefix + ":pending:count").\
            publish("queues:status", channel).\
            execute()


def publish(channel, data, prefix="channel"):
    db.pipeline().\
        sadd("%ss" % (prefix), channel).\
        publish("%s:%s" % (prefix, channel), json.dumps({
            "id": None,
            "channel": channel,
            "data": data,
        })).\
        execute()


def get_status(channel=None):
    if channel is None:
        channels = db.smembers("queues")
    else:
        channels = [channel]

    if not channels:
        # no queues
        return []

    keys = []
    for channel in channels:
        keys.extend([
            "queue:" + channel + ":count",
            "queue:" + channel + ":pending:count",
            "queue:" + channel + ":total",
        ])
    values = db.mget(keys)
    i = 0
    status = []
    for channel in channels:
        status.append((
            channel, values[i] or 0, values[i+1] or 0, values[i+2] or 0))
        i += 3
    return status


def get_message_pubsub(pub, timeout=1):
    sleep_time = 0
    while sleep_time < timeout:
        message = pub.get_message()
        if message is not None and message["type"] in ("message", "pmessage"):
            return message["data"]
        elif message is None:
            time.sleep(0.1)
            sleep_time += 0.1


def iter_messages_pubsub(channels, prefix="channel", timeout=1):
    pub = db.pubsub()
    if channels:
        pub.subscribe(["%s:%s" (prefix, channel) for channel in channels])
    else:
        pub.psubscribe(["%s:*" % (prefix)])
    while True:
        yield get_message_pubsub(pub, timeout=timeout)


def iter_status():
    pub = db.pubsub()
    pub.subscribe(["queues:status"])
    yield get_status()
    while True:
        channel = get_message_pubsub(pub)
        if channel is not None:
            yield get_status(channel)
        else:
            yield
