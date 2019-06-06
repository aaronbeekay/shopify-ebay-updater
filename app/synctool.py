import logging
import json
from flask import Flask, render_template, request, abort, send_from_directory, session, redirect, url_for, jsonify
import os
import requests
import datetime
from flask_cors import CORS
import re

"""Flask app setup"""
app = Flask(__name__)
CORS(app, supports_credentials=True)
# CORS(app,
# 	origins = [ 'http://ui.ebay-sync.slirp.aaronbeekay.info',
# 				'https://ui.ebay-sync.slirp.aaronbeekay.info',
# 				'https://ebay-sync.slirp.aaronbeekay.info' ,
# 				'http://ebay-sync.slirp.aaronbeekay.info',
# 				'http://glorious-pail.glitch.me',
# 				'https://glorious-pail.glitch.me',
# 				'http://glitch.com',
# 				'https://glitch.com'			],
# 	supports_credentials = True 			)

"""Pick up data from env vars"""
if os.path.exists('.env'):
	from dotenv import load_dotenv
	load_dotenv(verbose=True)
	
app.config['STATIC_FILE_DIR'] 			= os.getenv('STATIC_FILE_DIR', 
											 '/static'			)
app.config['APP_SECRET_KEY'] 				= os.getenv('APP_SECRET_KEY',	# for encrypting sesh
											 None 				)
app.config['EBAY_OAUTH_CLIENT_ID']		= os.getenv('EBAY_OAUTH_CLIENT_ID',
											 None 				)
app.config['EBAY_OAUTH_CLIENT_SECRET']	= os.getenv('EBAY_OAUTH_CLIENT_SECRET',
											 None				)
app.config['EBAY_OAUTH_TOKEN_ENDPOINT'] = os.getenv('EBAY_OAUTH_TOKEN_ENDPOINT',
											 'https://api.ebay.com/identity/v1/oauth2/token' )	# this is the prod URL
app.config['EBAY_APP_RUNAME'] 			= os.getenv('EBAY_APP_RUNAME',
											 None )
app.config['EBAY_SCOPES'] 				= os.getenv('EBAY_SCOPES',
											'https://api.ebay.com/oauth/api_scope ' 						+
											'https://api.ebay.com/oauth/api_scope/sell.inventory ' 			+
											'https://api.ebay.com/oauth/api_scope/sell.account.readonly' )
app.config['EBAY_OAUTH_CONSENT_URL'] 	= os.getenv('EBAY_OAUTH_CONSENT_URL',
											 'https://auth.ebay.com/oauth2/authorize?' 						+
											 	'client_id={}'.format(app.config['EBAY_OAUTH_CLIENT_ID']) 	+
											 	'&response_type=code' 										+
											 	'&redirect_uri={}'.format(app.config['EBAY_APP_RUNAME']) 	+
											 	'&scope={}'.format(app.config['EBAY_SCOPES']) ) # also the prod URL
app.config['SHOPIFY_API_KEY'] 			= os.getenv('SHOPIFY_API_KEY',
											 None )
app.config['SHOPIFY_API_PW'] 			= os.getenv('SHOPIFY_API_PW',
											 None )
app.config['SHOPIFY_STORE_DOMAIN'] 		= os.getenv('SHOPIFY_STORE_DOMAIN',
											 'glitchlab.myshopify.com' )
											 
app.config['SESSION_COOKIE_DOMAIN'] 	= '.aaronbeekay.info'
app.config['SESSION_COOKIE_HTTPONLY'] 	= False
app.config['SESSION_COOKIE_SAMESITE'] 	= 'Lax'
											 
"""Constants"""
app.config['EBAY_INVENTORYITEM_URL'] = 'https://api.ebay.com/sell/inventory/v1/inventory_item/{}'
app.config['EBAY_INVENTORYITEMGROUP_URL'] = 'https://api.ebay.com/sell/inventory/v1/inventory_item_group/{}'
app.config['EBAY_INVENTORYOFFERS_URL'] = 'https://api.ebay.com/sell/inventory/v1/offer?sku={}'
app.config['EBAY_INVENTORYOFFER_URL'] = 'https://api.ebay.com/sell/inventory/v1/offer/{}'
app.config['constants'] = {	
	'EBAY_ERROR_SKU_NOT_FOUND': 		25702,
	'EBAY_ERROR_ENTITY_NOT_FOUND':		25710,
	'EBAY_ERROR_INVALID_ACCESS_TOKEN': 	1001,
	'EBAY_ERROR_MISSING_ACCESS_TOKEN': 	1002,
	'EBAY_ERROR_ACCESS_DENIED': 		1100
	}


# Set up app secret key										 
app.secret_key = app.config['APP_SECRET_KEY']

# need to do this after setting up app for the time being because glitchlab_shopify.py relies on global object `app`
import glitchlab_shopify

def crossdomain(origin=None, methods=None, headers=None, max_age=21600,
                attach_to_all=True, automatic_options=True):
    """Decorator function that allows crossdomain requests.
      Courtesy of
      https://blog.skyred.fi/articles/better-crossdomain-snippet-for-flask.html
    """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    # use str instead of basestring if using Python 3.x
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    # use str instead of basestring if using Python 3.x
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        """ Determines which methods are allowed
        """
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        """The decorator function
        """
        def wrapped_function(*args, **kwargs):
            """Caries out the actual cross domain code
            """
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Allow-Headers'] = \
                "Origin, X-Requested-With, Content-Type, Accept, Authorization"
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


"""Debug URLLib requests"""
if 'DEBUG_URLLIB_REQS' in os.environ and int(os.environ['DEBUG_URLLIB_REQS']) is 1:
	from http.client import HTTPConnection
	HTTPConnection.debuglevel = 1
	logging.basicConfig()
	logging.getLogger().setLevel(logging.DEBUG)
	requests_log = logging.getLogger("requests.packages.urllib3")
	requests_log.setLevel(logging.DEBUG)
	requests_log.propagate = True



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

@app.route('/api/shopify/test-auth')
def test_shopify_auth():
	"""Do a test call to the Shopify API to make sure we have good credentials"""
	response = requests.get(
		'https://' + app.config['SHOPIFY_STORE_DOMAIN'] + '/admin/api/2019-04/products/count.json',
		auth=(app.config['SHOPIFY_API_KEY'],app.config['SHOPIFY_API_PW'])
	)
	
	try:
		j = response.json()
	except json.JSONDecodeError:
		logger.warning('Got a weird response from Shopify when trying to check creds: {}'.format(response.text))
		return jsonify({'shopify_auth_success': False})
		
	if 'count' in j:
		return jsonify({'shopify_auth_success': True})
	else:
		import pdb; pdb.set_trace()
		return jsonify({'shopify_auth_success': False})
	
@app.route('/api/ebay/test-auth')
def test_ebay_auth():
	"""Do a test call to the eBay API to make sure we have good credentials"""
	
	#logger.debug('/api/ebay/test-auth: Session variables are => {}'.format(json.dumps(dict(session))))
	
	if 'access_token' not in session:
		return jsonify({'ebay_auth_success': False, 'error': 'ebay_auth_missing', 'ebay_consent_url': app.config['EBAY_OAUTH_CONSENT_URL']})
		
	if session.get('access_token_expiry') < datetime.datetime.utcnow():
	
		if 'refresh_token' in session:
			refresh_access_token(session.get('refresh_token'))		
			return jsonify({'ebay_auth_success': False, 'error': 'ebay_auth_refreshed', 'message': 'eBay token has been refreshed, try reloading'})
		else:	
			return jsonify({'ebay_auth_success': False, 'error': 'ebay_auth_expired'})
	
	response = requests.get(
		'https://api.ebay.com/sell/inventory/v1/inventory_item?limit=1',
		headers={'Authorization': 'Bearer {}'.format(session['access_token'])})
	
	try:
		j = response.json()
	except json.JSONDecodeError:
		logger.warning("Got a weird response from eBay when checking auth credentials: {}".format(response.text))
		
	if "errors" not in j and "inventoryItems" in j:
		return jsonify({'ebay_auth_success': True})
	else:
		logger.warning('Failed eBay auth verification in a way that is not handled... eBay said: {}'.format(response.text))
		return jsonify({'ebay_auth_success': False, 'error': 'lazy_programmer_error'})
	
@app.route('/api/shopify/product', methods=['GET', 'POST'])
@crossdomain(origin='*')
def shopify_product_endpoint():
	if 'id' not in request.args:
		return("You need to supply the id parameter", 400)
	
	if request.method == 'GET':
		with app.app_context():
			p = glitchlab_shopify.get_shopify_product( request.args['id'] )	
		try:
			json.dumps(p)
			return jsonify(p)
		except TypeError:
			return jsonify({})
	
	if request.method == 'POST':
		try:
			glitchlab_shopify.set_shopify_attributes( request.args['id'], request.json )
		except json.JSONDecodeError as e:
			logger.warning("Bad (non-JSON) request sent to shopify product update endpoint: " + e)
			return("Invalid JSON body", 400)
			
		return('', 204)
		
@app.route('/api/shopify/product-metafield', methods=['GET', 'POST'])
def shopify_product_metafield():
	if request.method == 'GET':
		raise NotImplementedError('sorry')
		
	if request.method == 'POST':
		try:
			req = request.get_json()
			try:
				if 'variant_id' in req:
					glitchlab_shopify.set_metafield( 
						req['product_id'], 
						req['key'], 
						req['value'], 
						variant_id=req['variant_id']	)
				else:
					glitchlab_shopify.set_metafield( 
						req['product_id'], 
						req['key'], 
						req['value'] 					)
			except:
				return(500)
				raise
			return('', 204)
			
		except json.JSONDecodeError as e:
			logger.info('Got a POST request to /api/shopify/product-metafield but it wasn\'t valid JSON: {}'.format(e))
			return('Not valid JSON', 400)
		except KeyError as e:
			logger.info('POST request to /api/shopify/product-metafield was missing key: {}'.format(e))
			return('Missing a key or two', 400)
		
	
@app.route('/api/ebay-oauth-callback', methods=['GET'])
def handle_ebay_callback():
	logger.debug('/api/ebay-oauth-callback hit with code: {}'.format(request.args.get('code')))
	
	if 'code' in request.args:
		try:
			authdict = get_access_token(request.args['code'])
			
			return redirect('http://ui.ebay-sync.slirp.aaronbeekay.info/')
		except RuntimeError as e:
			return 'fuckin ebay problem: ' + e
	else:
		logger.error("Didn't get a code back from eBay oauth callback. Possibly user declined. eBay says: " + json.dumps(request.get_json()))
		
@app.route('/api/dev/session-keys', methods=['GET','POST'])
def set_session_keys():
	"""
	Debug/dev use: take any parameter we get in a POSTed form, and blindly set the corresponding session key.
	
	Probably ought to be disabled unless somebody actually thinks about what security implications this has.
	"""
	
	if len(request.form) > 0:
		for k,v in request.form.items():
			if k == 'access_token_expiry':
				logger.debug('setting datetime version of key {}'.format(k))
				session[k] = datetime.datetime.fromisoformat(v)			
			else:
				session[k] = v
		return jsonify({'changed': 'yes' }  )
	if len(request.args) > 0:
		for k,v in request.args.items():
			if k == 'access_token_expiry':
				logger.debug('setting datetime version of key {}'.format(k))
				session[k] = datetime.datetime.fromisoformat(v)			
			else:
				session[k] = v
		return jsonify( {'changed': 'yes' }  )
	try:
		for k,v in request.json():
			if k == 'access_token_expiry':
				logger.debug('setting datetime version of key {}'.format(k))
				session[k] = datetime.datetime.fromisoformat(v)			
			else:
				session[k] = v
		return jsonify( {'changed': 'yes' }  )
	except json.JSONDecodeError:
		return jsonify( {'changed': 'no' } )
	else:
		return jsonify( {'changed': 'no' } )
		
@app.route('/api/test-ebay-call')
def test_ebay_api_call():
	if 'access_token' in session and datetime.datetime.utcnow() < session.get('access_token_expiry'):
		response = requests.get(
			'https://api.ebay.com/sell/inventory/v1/inventory_item',
			headers={'Authorization': 'Bearer {}'.format(session['access_token'])})
			
		# Return tokens in JSON so that we can grab them for dev use
		return jsonify({'access_token': session['access_token'], 'access_token_expiry': session['access_token_expiry'], 'refresh_token': session['refresh_token']})
	elif 'refresh_token' in session:
		# access token is expired, go refresh it
		logger.debug('User access token expired, refreshing it...')
		new_auth = refresh_access_token( session['refresh_token'] )
		
		# Return tokens in JSON so that we can grab them for dev use
		return jsonify({'access_token': session['access_token'], 'access_token_expiry': session['access_token_expiry'], 'refresh_token': session['refresh_token']})
	else:
		logger.debug('User access token or user refresh token not present, redirecting to eBay consent thing: {}'.format(app.config['EBAY_OAUTH_CONSENT_URL']))
		return redirect(app.config['EBAY_OAUTH_CONSENT_URL'])
		
@app.route('/api/ebay/product', methods=['GET','POST'])
def ebay_product_endpoint():
	"""
	Get an eBay inventory item by its SKU (GET), or update an existing item with new attributes (POST).
	"""
	if request.method == 'GET':
		
		return get_ebay_product( request.args.get('sku') )
		
	elif request.method == 'POST':
		if 'sku' not in request.args:
			return(jsonify({'error': 'No SKU provided'}), 400)
		try:
			new = request.json
			
			if 'offers' in new and len(new['offers']) > 0:
				# We need to update each of the associated offers too
				for offer in new['offers']:
					glitchlab_shopify.update_ebay_offer( offer['offerId'], offer )
		
			# Now update the product too
			glitchlab_shopify.set_ebay_attributes( request.args.get('sku'), request.json )
			
			return('{}')
		except json.JSONDecodeError as e:
			logger.info('Bad request body sent to /api/ebay/product endpoint. Error: {}'.format(e))
			logger.debug('Request body in question was {}'.format(request.text))
			
def get_ebay_product(sku):
	"""Retrieve an item"""
	if sku is None:
		logger.info("This request doesn't have a sku attached to it")
		return 'Try again with a "sku" parameter'
	
	if 'access_token' not in session or session.get('access_token_expiry') < datetime.datetime.utcnow():
		# The client side will need to handle logging back in
		return jsonify({'error': 'ebay_auth_invalid'})
	
	try:
		# Get the product details from the InventoryItem API
		inventory_item = glitchlab_shopify.get_ebay_product( session['access_token'], request.args.get('sku') )
		
		# Get any associated Offers and merge them into the response
		offers = glitchlab_shopify.get_ebay_offers( request.args.get('sku')  )
		inventory_item['offers'] = offers
		
		return jsonify(inventory_item)
	except glitchlab_shopify.AuthenticationError as e:
		return jsonify({'error': 'ebay_auth_invalid', 'message': e.message})
	except glitchlab_shopify.ItemNotFoundError as e:
		"""
		Check if this is an InventoryItemGroup - eBay will return item not found if you search for 
			an inventoryItemGroup SKU using getInventoryItem().
		"""
		try:
			logger.debug("eBay returned 404 for SKU {} using getInventoryItem(), checking if it is an inventoryItemGroup...".format(request.args.get('sku')))
			inventory_item_group = glitchlab_shopify.get_ebay_inventoryitemgroup( session['access_token'], request.args.get('sku') )
			
			# If we got a good response and there are variant SKUs in the InventoryItemGroup, fetch the details for those as well...
			if 'variantSKUs' in inventory_item_group:
				inventory_item_group['variants'] = {}
				for vsku in inventory_item_group['variantSKUs']:
					v = glitchlab_shopify.get_ebay_product( session['access_token'], vsku )
					if 'sku' in v:
						inventory_item_group['variants'][v['sku']] = v
					else:
						logger.warning("eBay sent us a variant that doesn't seem to have a SKU attribute... expected SKU {}, not adding it to the inventoryItemGroup.".format(vsku))
			
			return jsonify(inventory_item_group)
				
		except glitchlab_shopify.ItemNotFoundError as e:
			return jsonify({'error': 'ebay_item_not_found', 'message': e.message})

# Serve static files using send_from_directory()	
@app.route('/<path:file>')
def serve_root(file):
	logger.debug('Request for file {}'.format(file))
	return send_from_directory(app.config['STATIC_FILE_DIR'], file)
		
@app.route('/')
def index():
	return redirect('http://ui.ebay-sync.slirp.aaronbeekay.info')
	logger.debug('Got a request for root, trying to serve {}'.format(os.path.join(app.config['STATIC_FILE_DIR'], 'index.html')))
	return send_from_directory(app.config['STATIC_FILE_DIR'], 'index.html')
	
def get_access_token(auth_code):
	"""
	Given an authorization code provided by eBay (`auth_code`), ping eBay and exchange it
		for a user access token. Set the session params accordingly.
	"""
	
	# Build request body
	body = {
		'grant_type': 'authorization_code',
		'code': auth_code,
		'redirect_uri': app.config['EBAY_APP_RUNAME']
	}
	response = requests.post(
		app.config['EBAY_OAUTH_TOKEN_ENDPOINT'],
		data=body,
		auth=(app.config['EBAY_OAUTH_CLIENT_ID'],app.config['EBAY_OAUTH_CLIENT_SECRET'])
	)
	authDict = response.json()
	
	if 'access_token' not in authDict:
		logger.error('No access token in eBay response when we tried to get one. Probably bad creds somewhere. eBay says: {}'.format(json.dumps(response.json())))
		raise glitchlab_shopify.AuthenticationError('No access token in response from eBay. Probably some kind of fucking stupid auth problem.')
		
	# Set session params
	session['access_token'] = authDict['access_token']
	session['access_token_expiry'] = datetime.datetime.utcnow() + datetime.timedelta(seconds=authDict['expires_in'])
	session['refresh_token'] = authDict['refresh_token']	
		
	return authDict

def refresh_access_token(refresh_token):
	"""Go to eBay and get a new access token from the refresh token we already have"""
	# Build request body
	body = {
		'grant_type': 'refresh_token',
		'refresh_token': refresh_token,
		'scope': app.config['EBAY_SCOPES']
	}
	response = requests.post(
		app.config['EBAY_OAUTH_TOKEN_ENDPOINT'],
		data=body,
		auth=(app.config['EBAY_OAUTH_CLIENT_ID'],app.config['EBAY_OAUTH_CLIENT_SECRET'])
	)
	authDict = response.json()
	
	if 'access_token' not in authDict:
		logger.error('No access token in eBay response when we tried to get one. Probably bad creds somewhere. eBay says: {}'.format(json.dumps(response.json())))
		raise glitchlab_shopify.AuthenticationError('No access token in response from eBay. Probably some kind of fucking stupid auth problem.')
	
	# Set session params
	session['access_token'] = authDict['access_token']
	session['access_token_expiry'] = datetime.datetime.utcnow() + datetime.timedelta(seconds=authDict['expires_in'])
	
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
