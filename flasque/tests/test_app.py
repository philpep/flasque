# -*- coding: utf8 -*-

from __future__ import unicode_literals
import json
import unittest
import mock


from flasque.main import app


class Test(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.get_uuid = mock.patch("flasque.queue.get_uuid")
        uuid = self.get_uuid.start()
        uuid.side_effect = (str(x) for x in range(10))

    def tearDown(self):
        app._db.flushall()
        self.get_uuid.stop()

    def assertSseEqual(self, response, expected):
        for i, data in enumerate(response):
            data = data.decode()
            self.assertEqual(data[:6], "data: ")
            self.assertEqual(data[-2:], "\n\n")
            if data[6:-2]:
                self.assertEqual(json.loads(data[6:-2]), expected[i])
            else:
                self.assertIsNone(expected[i])
            self.assertEqual(i < len(expected) + 1, True)

    def post(self, queue, data):
        res = self.app.post("/queue/?channel=" + queue, data=data)
        data = res.data.decode()
        return json.loads(data)["id"]

    def delete(self, queue, msgid):
        res = self.app.delete("/queue/?channel=" + queue + "&id=" + msgid)
        data = res.data.decode()
        self.assertEqual(json.loads(data), {})

    def assertGetEqual(self, queue, expected, pending=False):
        if pending:
            res = self.app.get("/queue/?channel=" + queue + "&pending=1")
        else:
            res = self.app.get("/queue/?channel=" + queue)
        expected.setdefault("channel", queue)
        data = res.data.decode()
        self.assertEqual(json.loads(data[6:]), expected)

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
        message = {
            "id": "0",
            "channel": "foo",
            "data": "bar",
        }
        with mock.patch("flasque.queue.get_message") as m:
            m.side_effect = [
                None,
                message,
            ]
            res = self.app.get("/queue/?channel=foo")
            self.assertSseEqual(res.response, [
                None,
                {"id": "0", "channel": "foo", "data": "bar"},
            ])
