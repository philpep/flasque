# -*- coding: utf8 -*-

import uuid
import json
import time
from .app import db


class Queue(object):

    def __init__(self, name):
        self.name = name
        self.qkey = "queue:%s" % (name,)
        self.mkey = self.qkey + ":message:"
        self.skey = self.qkey + ":stream"
        super(Queue, self).__init__()

    def put(self, data):
        msgid = uuid.uuid4().hex
        db.set(self.mkey + msgid, data)
        db.rpush(self.qkey, msgid)
        db.publish(self.skey, json.dumps({
            "msgid": msgid,
            "q": self.name,
            "data": data,
        }))
        return msgid

    @staticmethod
    def get(qs, timeout=1):
        keys = ["queue:%s" % (q,) for q in qs]
        return db.blpop(keys, timeout=timeout)

    @staticmethod
    def get_message(qs, **kwargs):
        elm = Queue.get(qs, **kwargs)
        if elm is not None:
            q, msgid = elm
            db.lpush(q, msgid)
            data = db.get(q + ":message:" + msgid)
            return {
                "msgid": msgid,
                "q": q.split(":")[1],
                "data": data,
            }

    def delete_message(self, msgid):
        db.lrem(self.qkey, msgid)
        db.delete(self.mkey + msgid)

    @staticmethod
    def pubsub_get_message(pubsub):
        message = pubsub.get_message()
        if message is not None and message["type"] == "message":
            return json.loads(message["data"])
        elif message is None:
            time.sleep(1)

    @staticmethod
    def listen(qs):
        pubsub = db.pubsub()
        pubsub.subscribe([
            "queue:%s:stream" % (q,) for q in qs])
        return pubsub
