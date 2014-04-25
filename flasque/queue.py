# -*- coding: utf8 -*-

from flasque import db

class Queue(object):

    def __init__(self, name):
        self.qkey = "queue:%s" % (name,)
        self.mkey = self.qkey + ":message:"
        super(Queue, self).__init__()

    def put(self, data):
        msgid = uuid.uuid4().hex
        db.set(self.mkey + msgid, data)
        db.lpush(self.qkey, msgid)
        return msgid

    def get(self, timeout=1):
        elm = db.blpop(self.qkey, timeout=timeout)
        if elm is not None:
            return elm[1]

    def get_message(self, msgid=None, timeout=1):
        if msgid is not None:
            return {
                "msgid": msgid,
                "data": db.get(self.mkey + msgid),
            }
        else:
            msgid = self.get(timeout=timeout)
            if msgid is not None:
                db.lpush(self.qkey, msgid)
                data = db.get(self.mkey + msgid)
                return {
                    "msgid": msgid,
                    "data": data,
                }

    def delete_message(self, msgid):
        db.lrem(self.qkey, msgid)
        db.delete(self.mkey + msgid)
