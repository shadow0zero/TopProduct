import os
from tornado import ioloop,web
from pymongo import MongoClient
import json
from bson import json_util
from bson.objectid import ObjectId

class IndexHandler(web.RequestHandler):
    def get(self):
        self.write("Hello World!!")

settings = {
        "template_path": os.path.join(os.path.dirname(__file__), "templates"),
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
        "debug" : True
        }

application = web.Application([
    (r'/', IndexHandler),
    (r'/index', IndexHandler),
],**settings)

if __name__ == "__main__":
    application.listen(8000)
    ioloop.IOLoop.instance().start()
