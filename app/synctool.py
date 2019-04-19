import logging
import json
from flask import Flask, render_template, request, abort, send_from_directory, session, redirect, url_for, jsonify
import os
import requests
import datetime
import glitchlab_shopify
from flask_cors import CORS

"""Debug URLLib requests"""
if os.environ.get('DEBUG_URLLIB_REQS') is True:
	from http.client import HTTPConnection
	HTTPConnection.debuglevel = 1
	logging.basicConfig()
	logging.getLogger().setLevel(logging.DEBUG)
	requests_log = logging.getLogger("requests.packages.urllib3")
	requests_log.setLevel(logging.DEBUG)
	requests_log.propagate = True

"""Pick up data from env vars"""
if os.path.exists('.env'):
	from dotenv import load_dotenv
	load_dotenv()
	
STATIC_FILE_DIR 			= os.environ.get('STATIC_FILE_DIR', 
											 '/static'			)
APP_SECRET_KEY 				= os.environ.get('APP_SECRET_KEY',									# for encrypting sesh
											 None 				)
EBAY_OAUTH_CLIENT_ID 		= os.environ.get('EBAY_OAUTH_CLIENT_ID',
											 None 				)
EBAY_OAUTH_CLIENT_SECRET 	= os.environ.get('EBAY_OAUTH_CLIENT_SECRET',
											 None				)
EBAY_OAUTH_TOKEN_ENDPOINT 	= os.environ.get('EBAY_OAUTH_TOKEN_ENDPOINT',
											 'https://api.ebay.com/identity/v1/oauth2/token' )	# this is the prod URL
EBAY_APP_RUNAME 			= os.environ.get('EBAY_APP_RUNAME',
											 None )
EBAY_SCOPES 				= os.environ.get('EBAY_SCOPES',
											'https://api.ebay.com/oauth/api_scope ' +
											'https://api.ebay.com/oauth/api_scope/sell.inventory ' +
											'https://api.ebay.com/oauth/api_scope/sell.account.readonly' )
EBAY_OAUTH_CONSENT_URL 		= os.environ.get('EBAY_OAUTH_CONSENT_URL',
											 'https://auth.ebay.com/oauth2/authorize?' +
											 	'client_id={}'.format(EBAY_OAUTH_CLIENT_ID) +
											 	'&redirect_uri={}'.format(EBAY_APP_RUNAME) +
											 	'&scope={}'.format(EBAY_SCOPES) ) 		# also the prod URL
SHOPIFY_API_KEY 			= os.environ.get('SHOPIFY_API_KEY',
											 None )
SHOPIFY_API_PW 				= os.environ.get('SHOPIFY_API_PW',
											 None )
SHOPIFY_STORE_DOMAIN 		= os.environ.get('SHOPIFY_STORE_DOMAIN',
											 'glitchlab.myshopify.com' )
											
"""Flask app setup"""
app = Flask(__name__)
app.secret_key = APP_SECRET_KEY
CORS(app)

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
	
@app.route('/api/shopify/product')
def get_shopify_product():
	if 'id' in request.args:
		url = 'https://' + SHOPIFY_STORE_DOMAIN + '/admin/api/2019-04/products/' + request.args['id'] + '.json'
		logger.debug("Trying to GET the Shopify product {} by hitting {}".format(request.args['id'], url))
		logger.debug("Using auth: {}:{}".format(SHOPIFY_API_KEY,SHOPIFY_API_PW))
		response = requests.get(
			url,
			auth=(SHOPIFY_API_KEY,SHOPIFY_API_PW)
		)
		try:
			return jsonify(response.json())
		except json.JSONDecodeError:
			logger.debug('Shopify said: ' + response.text)
			return 'Shopify said...' + response.text
	else:
		return "You gotta supply a Shopify product ID in the 'id' GET param"
	
@app.route('/api/ebay-oauth-callback', methods=['GET'])
def handle_ebay_callback():
	logger.debug('/api/ebay-oauth-callback hit with code: {}'.format(request.args.get('code')))
	
	if 'code' in request.args:
		try:
			authdict = get_access_token(request.args['code'])
			session['access_token'] = authdict['access_token']
			session['access_token_expiry'] = datetime.datetime.utcnow() + datetime.timedelta(seconds=authdict['expires_in'])
			session['refresh_token'] = authdict['refresh_token']
			return redirect(url_for('test_ebay_api_call'))
		except RuntimeError as e:
			return 'fuckin ebay problem: ' + e
	else:
		logger.error("Didn't get a code back from eBay oauth callback. Possibly user declined. eBay says: " + json.dumps(request.json()))
		
@app.route('/api/test-ebay-call')
def test_ebay_api_call():
	if 'access_token' in session and datetime.datetime.utcnow() < session.get('access_token_expiry'):
		response = requests.get(
			'https://api.ebay.com/sell/inventory/v1/inventory_item',
			headers={'Authorization': 'Bearer {}'.format(session['access_token'])})
		return json.dumps(response.json())
	elif 'refresh_token' in session:
		# access token is expired, go refresh it
		logger.debug('User access token expired, refreshing it...')
		# TODO refresh the token here
		return "your access token is expired"
	else:
		logger.debug('User access token or user refresh token not present, redirecting to eBay consent thing: {}'.format(EBAY_OAUTH_CONSENT_URL))
		return redirect(EBAY_OAUTH_CONSENT_URL)
		
@app.route('/api/ebay/product', methods=['GET'])
def get_ebay_product():
	if 'id' not in request.args:
		logger.info("This request doesn't have an id attached to it")
		return 'Try again with an "id" parameter'
		
	if 'access_token' not in session or session.get('access_token_expiry') < datetime.datetime.utcnow():
		# The client side will need to handle logging back in
		return jsonify({'error': 'ebay_auth_invalid'})
	
	try:
		p = glitchlab_shopify.get_ebay_product( session['access_token'], request.args['id'] )
		return jsonify(p)
	except glitchlab_shopify.AuthenticationError as e:
		return jsonify({'error': 'ebay_auth_invalid', 'message': e.message})
	except glitchlab_shopify.ItemNotFoundError as e:
		return jsonify({'error': 'ebay_item_not_found', 'message': e.message})

# Serve static files using send_from_directory()	
@app.route('/<path:file>')
def serve_root(file):
	logger.debug('Request for file {}'.format(file))
	return send_from_directory(STATIC_FILE_DIR, file)
		
@app.route('/')
def index():
	logger.debug('Got a request for root')
	return send_from_directory(STATIC_FILE_DIR, 'index.html')
	
def get_access_token(auth_code):
	"""
	Given an authorization code provided by eBay (`auth_code`), ping eBay and exchange it
		for a user access token.
	"""
	
	# Build request body
	body = {
		'grant_type': 'authorization_code',
		'code': auth_code,
		'redirect_uri': EBAY_APP_RUNAME
	}
	response = requests.post(
		EBAY_OAUTH_TOKEN_ENDPOINT,
		data=body,
		auth=(EBAY_OAUTH_CLIENT_ID,EBAY_OAUTH_CLIENT_SECRET)
	)
	authDict = response.json()
	
	if 'access_token' not in authDict:
		logger.error('No access token in eBay response when we tried to get one. Probably bad creds somewhere. eBay says: {}'.format(json.dumps(response.json())))
		raise RuntimeError('No access token in response from eBay. Probably some kind of fucking stupid auth problem.')
	return authDict
	
"""Exceptions"""
# class InvalidRequest(Exception):
# 	status_code = 400
# 	
# 	def __init__(self, message, status_code=None, payload=None)
# 		Exception.__init__(self)
# 		self.message = message
# 		if status_code is not None:
# 			self.status_code = status_code
# 		self.payload = payload
	
if __name__ == "__main__":
	app.run(host='0.0.0.0')
