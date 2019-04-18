import logging
import json
from flask import Flask, render_template, request, abort, send_from_directory
import os

app = Flask(__name__)
#CORS(app, resources=r'/api/*')		# Allow any origin for requests to paths starting with /api/

"""Pick up data from env vars"""
STATIC_FILE_DIR 			= os.environ.get('STATIC_FILE_DIR', 
											 '/static'			)
EBAY_OAUTH_CLIENT_ID 		= os.environ.get('EBAY_OAUTH_CLIENT_ID',
											 None 				)
EBAY_OAUTH_CLIENT_SECRET 	= os.environ.get('EBAY_OAUTH_CLIENT_SECRET',
											 None				)
EBAY_OAUTH_TOKEN_ENDPOINT 	= os.environ.get('EBAY_OAUTH_TOKEN_ENDPOINT',
											 'https://api.ebay.com/identity/v1/oauth2/token' )	# this is the prod URL
EBAY_OAUTH_CONSENT_ENDPOINT = os.environ.get('EBAY_OAUTH_CONSENT_ENDPOINT',
											 'https://auth.ebay.com/oauth2/authorize' ) 		# also the prod URL
EBAY_APP_RUNAME 			= os.environ.get('EBAY_APP_RUNAME',
											 None )
EBAY_SCOPES 				= os.environ.get('EBAY_SCOPES',
											'https://api.ebay.com/oauth/api_scope ' +
											'https://api.ebay.com/oauth/api_scope/sell.inventory ' +
											'https://api.ebay.com/oauth/api_scope/sell.account.readonly' )

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
	
@app.route('/api/ebay-oauth-callback' methods=['GET'])
def handle_ebay_callback():
	logger.debug('/api/ebay-oauth-callback')
	return json.dumps(request.args) + json.dumps(request.headers) + json.dumps(request.host)

# Serve static files using send_from_directory()	
@app.route('/<path:file>')
def serve_root(file):
	logger.debug('Request for file {}'.format(file))
	return send_from_directory(STATIC_FILE_DIR, file)
		
@app.route('/')
def index():
	logger.debug('Got a request for root')
	return send_from_directory(STATIC_FILE_DIR, 'index.html')
	
if __name__ == "__main__":
	app.run(host='0.0.0.0')
