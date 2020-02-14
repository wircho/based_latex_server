import os
import json
import logging
import random
import string
import logging.handlers
import traceback
import pymongo
from based_latex import save_latex_image
from bottle import run, get, post, request, response, static_file, ServerAdapter, default_app
from cheroot import wsgi
from cheroot.ssl.builtin import BuiltinSSLAdapter
import ssl

# Tips from https://github.com/nickbabcock/bottle-ssl/blob/master/main.py

handler = logging.handlers.RotatingFileHandler("logs/python.log", mode = "a", maxBytes = 5000000, backupCount = 0)
handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

client = pymongo.MongoClient()
db = client['latex']
expressions = db["expressions"]

with open("config.json", "r") as file: config = json.load(file)
server_name = config["server"]
certfile_path = config["certfile"]
keyfile_path = config["keyfile"]
origins = config["origins"]

def random_string(length = 10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

if not os.path.isdir("images"): os.makedirs("images")

def new_image_path():
	path = None
	while path is None or os.path.isfile(path):
		path = os.path.join("images", random_string() + ".png")
	return path

def ensure_origin(request, response):
	origin = request.get('origin')
	if origin not in origins: return
	response.headers['Access-Control-Allow-Origin'] = origin
	response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
	response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

@get('/latex')
def latex():
	ensure_origin(request, response)
	try:
		expression = request.query['expression']
		element = expressions.find_one({"_id": expression})
		if element is not None:
			return element
		else:
			path = new_image_path()
			prefix, suffix = save_latex_image(expression, path)
			element = {"_id": expression, "prefix": prefix, "suffix": suffix, "path": path}
			expressions.insert(element)
			return element
	except:
		return {"error": traceback.format_exc()}

@get('/images/<filename>')
def get_image(filename):
	ensure_origin(request, response)
	return static_file(filename, root='images')

# Create our own sub-class of Bottle's ServerAdapter
# so that we can specify SSL. Using just server='cherrypy'
# uses the default cherrypy server, which doesn't use SSL
class SSLCherryPyServer(ServerAdapter):
	def run(self, handler):
		server = wsgi.Server((self.host, self.port), handler)
		server.ssl_adapter = BuiltinSSLAdapter(certfile_path, keyfile_path)

		# By default, the server will allow negotiations with extremely old protocols
		# that are susceptible to attacks, so we only allow TLSv1.2
		server.ssl_adapter.context.options |= ssl.OP_NO_TLSv1
		server.ssl_adapter.context.options |= ssl.OP_NO_TLSv1_1

		try: server.start()
		finally: server.stop()

# # define beaker options
# # -Each session data is stored inside a file located inside a
# #  folder called data that is relative to the working directory
# # -The cookie expires at the end of the browser session
# # -The session will save itself when accessed during a request
# #  so save() method doesn't need to be called
# session_opts = {
#     "session.type": "file",
#     "session.cookie_expires": True,
#     "session.data_dir": "./data",
#     "session.auto": True,
# }

# # Create the default bottle app and then wrap it around
# # a beaker middleware and send it back to bottle to run
# app = SessionMiddleware(default_app(), session_opts)

if __name__ == "__main__":
    # run(app=app, host="0.0.0.0", port=443, server=SSLCherryPyServer)
    run(host = "0.0.0.0", port = 443, server = SSLCherryPyServer)

# # old:
# run(host = "0.0.0.0", port = 443, server = server_name, certfile = certfile_path, keyfile = keyfile_path)
