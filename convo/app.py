import tornado
from tornado import websocket
from tornado import httpserver
import json
import datetime


"""
Incoming Message:
{
   urlhash: <<md5 of url>>
   email: "kmooney@gmail.com",
   message: "Hey, this is a test of the comment system.  Convo."
}

Message to client:
{
   urlhash: <<md5 of url>>
   email: "kmooney@gmail.com",
   message: "Hey, this is a test of the comment system.  Convo.",
   timestamp: "2013-10-31T20:30:00"
}
"""


CLIENTS = []


class ChatWebSocketServer(websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):
        self.message_handlers = {}
        super(ChatWebSocketServer, self).__init__(*args, **kwargs)

    def open(self):
        # we should get all the items for this page
        # and dump them down the pipe when this opens.
        # how to tell
        CLIENTS.append(self)

    def handle_message(self, obj):
        message = obj.get('message', None)
        if message is None:
            raise TypeError("Message is required")
        obj['timestamp'] = datetime.datetime.now().isoformat('-')
        msg = json.dumps(message)
        self.broadcast(msg)

    def handle_gimme(self, obj):
        self.write_message("Ok, here are comments for page.")

    def broadcast(self, msg):
        for c in CLIENTS:
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
        print "Socket Closed"

app = tornado.web.Application([
    (r'/chat', ChatWebSocketServer),
])

if __name__ == '__main__':
    http_server = httpserver.HTTPServer(app)
    http_server.listen(8686)
    tornado.ioloop.IOLoop.instance().start()
