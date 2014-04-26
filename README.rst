=====================
flasque - HTTP queues
=====================


.. image:: https://travis-ci.org/philpep/flasque.svg?branch=master   :target: https://travis-ci.org/philpep/flasque


`flasque` is a `flask`_ application exposing `redis`_ based queues and a
client API using `requests`_.


Installation
============

To install using `pip`,::

    $ pip install git+https://github.com/philpep/flasque


Hello world
===========

launch `flasque` server::

    $ flasque

::

    from flasque.client import Connection
    with Connection() as conn:
        producer = conn.Producer("my_queue")
        consumer = conn.Consumer("my_queue")
        producer.put("hello world")
        message = consumer.get()
        print(message)
        consumer.task_done()


.. _`flask`: http://flask.pocoo.org/
.. _`redis`: http://redis.io/
.. _`requests`: http://docs.python-requests.org/en/latest/
