import os
import json
import logging
import logging.handlers
import traceback
import pymongo
from based_latex import get_latex_svg_data
from bottle import run, get, post, request, response, static_file, ServerAdapter, default_app
from cheroot import wsgi
from cheroot.ssl.builtin import BuiltinSSLAdapter
import ssl
from urllib.parse import urlsplit
from utils import random_string

log_file_name = "logs.txt"

def add_log(text):
	with open(log_file_name, "a+") as file: file.write(f"{text}\n")


# Tips from https://github.com/nickbabcock/bottle-ssl/blob/master/main.py

# handler = logging.handlers.RotatingFileHandler("logs/python.log", mode = "a", maxBytes = 5000000, backupCount = 0)
# handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)
# logger.addHandler(handler)

client = pymongo.MongoClient()
db = client['latex']
expressions = db["expressions"]

with open("config.json", "r") as file: config = json.load(file)
server_name = config["server"]
certfile_path = config["certfile"]
keyfile_path = config["keyfile"]
origins = config["origins"]

def new_image_path(ext):
	add_log("Creating new image path...")
	if not os.path.isdir("images"): os.makedirs("images")
	path = None
	while path is None or os.path.isfile(path):
		path = os.path.join("images", random_string() + ext)
	add_log(f"Created new image path {path}")
	return path

def get_referer_origin(referer):
	add_log("Getting referer origin...")
	if referer is None: return None
	split = urlsplit(referer)
	add_log(f"Got referer origin {split.scheme}://{split.netloc}")
	return split.scheme + "://" + split.netloc

def ensure_origin(request, response):
	add_log("Ensuring origin...")
	origin = request.headers.get('Origin')
	referer = request.headers.get('Referer')
	if origin not in origins and get_referer_origin(referer) not in origins: return
	response.headers['Access-Control-Allow-Origin'] = origin
	response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
	response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
	add_log("Added origin headers.")

def static_file_with_origin(filename, root = "./"):
	add_log(f"Getting static file {filename} at root {root}...")
	res = static_file(filename, root = root)
	ensure_origin(request, res)
	add_log("Got requested static file.")
	return res

@get('/quit')
def quit():
	tokens = None
	try:
		with open("action_tokens.json", "r") as file: tokens = json.load(file)
	except: pass
	if tokens is None or tokens["quit"] != request.query["token"]: return {"error": "Bad token."}
	exit()

@get('/latex')
def latex():
	add_log("GET /latex")
	ensure_origin(request, response)
	try:
		expression = request.query['expression']
		print(expression)
		add_log(f"Requested expression {expression}...")
		is_math = int(request.query.get('is_math', '0')) != 0
		_id = ("" if is_math else "<non-math>") + expression
		element = expressions.find_one({"_id": _id})
		if element is None:
			# path = new_image_path(".svg")
			add_log(f"Getting svg data...")
			data = get_latex_svg_data(expression, is_math = is_math)
			add_log("Got svg data.")
			element = {
				"_id": _id,
				"data": data#,
				#"path": path
			}
			add_log("Inserting into expressions.")
			expressions.insert(element)
			add_log("Inserted into expressions.")
		return element
	except:
		tb = traceback.format_exc()
		add_log(f"Got error\n{tb}")
		return {"error": tb}

@get('/assets/<filename>')
def get_image(filename): return static_file_with_origin(filename, root = 'assets')

@get('/images/<filename>')
def get_image(filename): return static_file_with_origin(filename, root = 'images')

# @get('/fonts.css')
# def get_fonts_css():
# 	ensure_origin(request, response)
# 	response.headers['Content-Type'] = "text/css"
# 	font_names = [os.path.splitext(name)[0] for name in os.listdir("fonts") if os.path.splitext(name)[1] == ".ttf"]
# 	css = [f"""
# @font-face {{
#   font-family:{name.upper()};
#   src:url(https://api.interoper.io/fonts/{name}.ttf);
# }}
# 	""" for name in font_names]
# 	return "\n".join(css)

@get('/fonts/<filename>')
def get_font(filename): return static_file_with_origin(filename, root = 'fonts')


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
