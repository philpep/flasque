import json
import unittest
import fakeredis

from flasque.main import get_app
app = get_app()


def publish(*args, **kwargs):
    return


class Test(unittest.TestCase):

    def setUp(self):
        app._db = fakeredis.FakeRedis()
        app._db.publish = publish
        self.app = app.test_client()

    def tearDown(self):
        fakeredis.DATABASES = {}

    def test_queue(self):
        res = self.app.post("/queue/foo", data="foo")
        msgid = json.loads(res.data)["msgid"]
        self.app.post("/queue/foo", data="bar")
        for x in range(2):
            res = self.app.get("/queue/foo")
            self.assertEqual(json.loads(res.data)["data"], "foo")
        res = self.app.delete("/queue/foo?msgid=%s" % msgid)
        res = self.app.get("/queue/foo")
        self.assertEqual(json.loads(res.data)["data"], "bar")
