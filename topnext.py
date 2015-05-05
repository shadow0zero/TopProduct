#!usr/bin/env python
#-*-coding:utf-8-*-

import os.path

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define,options

from pymongo import MongoClient,DESCENDING

define("port",default=8002,help="run on the given port",type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/",MainHandler),
            ]
        settings = dict(
                template_path = os.path.join(os.path.dirname(__file__),"templates"),
                static_path = os.path.join(os.path.dirname(__file__),"static"),
                debug = True,
                )
        conn = MongoClient("localhost",27017)
        #数据库名字topnext
        self.db = conn["topnext"]
        tornado.web.Application.__init__(self,handlers,**settings)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        #Collection名字prod_next
        coll = self.application.db.prod_next
        posts = coll.find().sort("date",DESCENDING)
        self.render(
                    "index.html",
                    posts = posts,
                )
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()

