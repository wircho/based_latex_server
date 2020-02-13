import json
import logging
import traceback
from based_latex import save_latex_image
from bottle import run, get, post, request

handler = logging.handlers.RotatingFileHandler("../logs/python.log", mode = "a", maxBytes = 5000000, backupCount = 0)
handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

@get('/latex')
def latex():
	try:
  	expression = request.query['expression']
  	prefix, suffix = save_latex_image(expression, "test.png")
  	return {"prefix": prefix, "suffix": suffix}
  except:
  	return {"error": traceback.format_exc()}

run(host = "0.0.0.0", port = 80)
