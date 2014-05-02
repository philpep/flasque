import json
import unittest
import fakeredis
import mock

from flasque.main import app


class Test(unittest.TestCase):

    def setUp(self):
        self.db = app._db = fakeredis.FakeRedis()
        self.publish = app._db.publish = mock.Mock()
        self.pubsub = app._db.pubsub = mock.Mock()
        self.app = app.test_client()
        self.get_uuid = mock.patch("flasque.queue.get_uuid")
        uuid = self.get_uuid.start()
        uuid.side_effect = (str(x) for x in xrange(10))

    def tearDown(self):
        app._db.flushall()
        self.get_uuid.stop()

    def assertSseEqual(self, response, expected):
        for i, data in enumerate(response):
            self.assertEqual(data[:6], "data: ")
            self.assertEqual(data[-2:], "\n\n")
            if data[6:-2]:
                self.assertEqual(json.loads(data[6:-2]), expected[i])
            else:
                self.assertIsNone(expected[i])
            self.assertEqual(i < len(expected) + 1, True)

    def post(self, queue, data):
        res = self.app.post("/queue/" + queue, data=data)
        return json.loads(res.data)["id"]

    def delete(self, queue, msgid):
        res = self.app.delete("/queue/" + queue + "?id=" + msgid)
        self.assertEqual(json.loads(res.data), {})

    def assertGetEqual(self, queue, expected, pending=False):
        if pending:
            res = self.app.get("/queue/" + queue + "?pending=1")
        else:
            res = self.app.get("/queue/" + queue)
        expected.setdefault("channel", queue)
        self.assertEqual(json.loads(res.data[6:]), expected)

    def test_get_delete(self):
        msgid = self.post("foo", "bar")
        self.assertGetEqual("foo", {
            "id": msgid,
            "data": "bar",
        })
        self.delete("foo", msgid)

    def test_get_pending(self):
        foo_msgid = self.post("foo", "foo")
        bar_msgid = self.post("foo", "bar")
        self.assertGetEqual("foo", {
            "id": foo_msgid,
            "data": "foo",
        })
        self.assertGetEqual("foo", {
            "id": foo_msgid,
            "data": "foo",
        }, pending=True)
        self.delete("foo", foo_msgid)
        self.assertGetEqual("foo", {
            "id": bar_msgid,
            "data": "bar",
        })

    def test_wait_queue(self):
        self.app.post("/queue/foo", data="bar")
        self.db.blpop = mock.Mock(side_effect=[None, ("queue:foo", "0")])
        res = self.app.get("/queue/foo")
        self.assertSseEqual(res.response, [
            None,
            {"id": "0", "channel": "foo", "data": "bar"},
        ])

    def test_wait_channel(self):
        message = {
            "id": "0",
            "channel": "foo",
            "data": "bar",
        }
        with mock.patch("flasque.queue.Queue.get_message_pubsub") as m:
            m.side_effect = [
                None,
                json.dumps(message),
            ]
            res = self.app.get("/channel/foo")
            self.assertSseEqual(res.response, [
                None,
                message,
            ])

    def test_publish(self):
        self.app.post("/channel/foo", data="bar")
        self.publish.assert_called_with("channel:foo", json.dumps({
            "id": None,
            "channel": "foo",
            "data": "bar"}
        ))
