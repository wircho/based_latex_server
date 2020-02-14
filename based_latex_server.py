import os
import json
import logging
import random
import string
import logging.handlers
import traceback
import pymongo
from based_latex import save_latex_image
from bottle import run, get, post, request, static_file

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

@get('/latex')
def latex():
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
def server_static(filename):
	return static_file(filename, root='images')

run(host = "0.0.0.0", port = 443, server = server_name, certfile = certfile_path, keyfile = keyfile_path)
