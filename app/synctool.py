import logging
import json
from flask import Flask, render_template, request, abort, send_file
import os
import base64

app = Flask(__name__)
#CORS(app, resources=r'/api/*')		# Allow any origin for requests to paths starting with /api/

"""Get sensitive data from env vars"""
EBAY_OAUTH_CLIENT_ID = os.environ.get('EBAY_OAUTH_CLIENT_ID')
EBAY_OAUTH_CLIENT_SECRET = os.environ.get('EBAY_OAUTH_CLIENT_SECRET')

if None in [EBAY_OAUTH_CLIENT_ID, EBAY_OAUTH_CLIENT_SECRET]:
	raise RuntimeError("Missing one or more environment variables")

"""Logging setup"""
# create logger
logger = logging.getLogger('io.glitchlab.ebay-sync-tool')
logger.setLevel(logging.DEBUG)

# create console handler 
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)

if __name__ != '__main__':	# only do this when running w gunicorn
	glogs = logging.getLogger('gunicorn.error')
	# don't need to put time in logs because it's already there
	formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
	
	ch.setFormatter(formatter)
	for h in glogs.handlers:
		h.setFormatter(formatter)
		#logger.setLevel(logging.DEBUG, h)
		logger.addHandler(h)
		

""" Endpoints """
@app.route('/api/hello-world', methods=['GET'])
def create_system():
	logger.debug('Got a GET request to /api/hello-world')
	
	return("Hello from Flask!")
	
@app.route('/api/oauth-callback')
def handle_oauth_callback():
	oauth_credentials = base64.b64encode(EBAY_OAUTH_CLIENT_ID + ':' + EBAY_OAUTH_CLIENT_SECRET)
	
	
if __name__ == "__main__":
	app.run(host='0.0.0.0')
