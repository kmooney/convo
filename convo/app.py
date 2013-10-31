import tornado
from tornado import websocket
from tornado import httpserver


class ChatWebSocketServer(websocket.WebSocketHandler):

    def open(self):
        print "Websocket Opened"

    def on_message(self, message):
        print "on message: %s" % message
        self.write_message(message)

    def on_close(self):
        print "Socket Closed"

app = tornado.web.Application([
    (r'/chat', ChatWebSocketServer),
])

if __name__ == '__main__':
    http_server = httpserver.HTTPServer(app)
    http_server.listen(8686)
    tornado.ioloop.IOLoop.instance().start()
