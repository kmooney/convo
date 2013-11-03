import tornado
from tornado import gen
from tornado import websocket
from tornado import httpserver
import json
import datetime
from tornado.web import asynchronous
import tornadoredis


"""
Incoming Message:
{
   urlhash: <<md5 of url>>
   emailhash: "xyz123abczzz", // used for gravatar - original email not stored.
   message: "Hey, this is a test of the comment system.  Convo."
}

Message to client:
{
   urlhash: <<md5 of url>>
   emailhash: "xyz123abczzz",
   message: "Hey, this is a test of the comment system.  Convo.",
   timestamp: "2013-10-31T20:30:00"
}
"""


CLIENTS = {}

class ChatWebSocketServer(websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        self.redis = tornadoredis.Client()
        self.message_handlers = {}
        super(ChatWebSocketServer, self).__init__(*args, **kwargs)

    def open(self):
        # we should get all the items for this page
        # and dump them down the pipe when this opens.
        # how to tell
        self.redis.connect()
        print self.redis.connection

        CLIENTS[self] = self

    @gen.engine
    def handle_message(self, obj, callback=None):
        message = obj.get('message', None)
        urlhash = obj.get('urlhash', None)
        if message is None:
            raise TypeError("Message is required")
        if urlhash is None:
            raise TypeError("Urlhash is required")
        obj['timestamp'] = datetime.datetime.now().isoformat('-')
        # stash the message, too.
        msg = json.dumps(obj)
        args = (urlhash, msg)
        yield gen.Task(self.redis.rpush, *args)
        self.broadcast(msg)

    @gen.engine
    def handle_gimme(self, obj, callback=None):
        urlhash = obj.get('urlhash', None)
        if urlhash is None:
            raise TypeError("Urlhash is required")
        args = (urlhash, 0, -1)
        response = yield gen.Task(self.redis.lrange, *args)
        # There has to be a better way...
        response = json.dumps({"type": 'haidouzo', "objects": [json.loads(r) for r in response]})
        self.write_message(response)


    def broadcast(self, msg):
        for c in CLIENTS:
            if c is not None:
                c.write_message(msg)

    def on_message(self, message):
        try:
            obj = json.loads(message)
            msg_type = obj.get('type', None)
            if msg_type is None:
                raise TypeError("All message must have type.")
            handler_func = getattr(self, 'handle_%s' % msg_type, None)
            if handler_func is None:
                raise TypeError("No handler for %s type " % msg_type)
            handler_func(obj)
        except ValueError, ve:
            print ve

    def on_close(self):
        del CLIENTS[self]
        self.redis.disconnect()

app = tornado.web.Application([
    (r'/chat', ChatWebSocketServer),
])

if __name__ == '__main__':
    http_server = httpserver.HTTPServer(app)
    http_server.listen(8686)
    tornado.ioloop.IOLoop.instance().start()
