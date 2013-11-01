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


class ChatWebSocketServer(websocket.WebSocketHandler):

    def open(self):
        # we should get all the items for this page
        # and dump them down the pipe when this opens.
        # how to tell
        print "Websocket Opened"

    def on_message(self, message):
        try:
            obj = json.loads(message)
            if 'urlhash' not in obj:
                raise ValueError(
                    "Invalid Type - IncomingMessage must have urlhash."
                )
            if 'email' not in obj:
                raise ValueError(
                    "Invalid Type - IncomingMessage must have email."
                )
            if 'message' not in obj:
                raise ValueError(
                    "Invalid Type - IncomingMessage must have message."
                )
            obj['timestamp'] = datetime.datetime.now().isoformat('-')
            msg = json.dumps(message)
            self.write_message(msg)
            print "wrote %s"%msg
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
