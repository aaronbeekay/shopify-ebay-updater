import os
import shopify
import logging
import pystache
import requests
import json

"""Constants"""
EBAY_GETINVENTORYITEM_URL = 'https://api.ebay.com/sell/inventory/v1/inventory_item/{}'
EBAY_ERROR_SKU_NOT_FOUND = 25702
EBAY_ERROR_INVALID_ACCESS_TOKEN = 1001
EBAY_ERROR_MISSING_ACCESS_TOKEN = 1002
EBAY_ERROR_ACCESS_DENIED = 1100

"""Logging setup"""
logger = logging.getLogger('glitchlab_shopify.slirp.aaronbeekay')
logger.setLevel(logging.DEBUG)
# Create console handler to dump messages to console
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# Create formatter and add it to the console handler - omit time because it's handled elsewhere
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# Add the handler to the logger
logger.addHandler(ch)

def render_product_template(template, product):
	"""make the HTML description for a product. template is a file path"""
	with open(template) as f:
		t = f.read()
	
	fields = {	'item_name': 			product.title,
				'item_description': 	product.body_html
				}
	
	return pystache.render(t, fields)
		

def set_shopify_attributes(product_id, attributes):
	"""Set Shopify product attributes from a dict."""
	raise NotImplementedError("sorry")
	
def set_ebay_attributes(product_id, attributes):
	"""Set eBay inventory item attributes from a dict."""
	raise NotImplementedError("sorry")
	
def get_ebay_product(auth_token, product_sku):
	"""
	Fetch the eBay product details for product with sku `product_sku`. Return them as a dict.
	
	Raises AuthenticationError if not authenticated.
	
	Raises ItemNotFoundError if item doesn't exist.
	"""
	url = EBAY_GETINVENTORYITEM_URL.format(product_sku)
	auth = {'Authorization': 'Bearer {}'.format(auth_token)}
	logger.debug('Trying to fetch eBay SKU {}...'.format(product_sku))
	response = requests.get( url, headers=auth )
	
	try:
		j = response.json()
	except json.JSONDecodeError:
		logger.debug('Got a weird reply from eBay: {}'.format(response.text))
		
	if 'errors' in j:
		for e in j['errors']:
			if e['errorId'] == EBAY_ERROR_SKU_NOT_FOUND:
				raise ItemNotFoundError(e['message'])
			elif (	e['errorId'] == EBAY_ERROR_INVALID_ACCESS_TOKEN 	\
				or 	e['errorId'] == EBAY_ERROR_MISSING_ACCESS_TOKEN 	\
				or 	e['errorId'] == EBAY_ERROR_ACCESS_DENIED		    ):
				raise AuthenticationError(e['message'])
				
	return j
				
	
def shopify_authenticate(api_key=None, api_password=None):
	"""Authenticate with the Shopify API given a certain API key and password. If none given, check the env
		variables SHOPIFY_API_KEY and SHOPIFY_API_PASSWORD.""" 
	
	if api_key is None:
		try:
			api_key = os.environ['SHOPIFY_API_KEY']
		except KeyError:
			raise RuntimeError("Didn't find a Shopify API key in the SHOPIFY_API_KEY environment variable")
		
	if api_password is None:
		try:
			api_password = os.environ['SHOPIFY_API_PASSWORD']
		except KeyError:
			raise RuntimeError("Didn't find a Shopify API password in the SHOPIFY_API_PASSWORD environment variable")

	shop_url = "https://%s:%s@glitchlab.myshopify.com/admin" % (api_key, api_password)
	shopify.ShopifyResource.set_site(shop_url)
	
def get_metafields(product):
	"""Return a dict of metafields and values for a Shopify product"""
	d = {}
	for m in product.metafields():
		k = m.key
		
		if m.value_type == 'integer':
			v = int(m.value)
		else:
			v = m.value
		
		d[k] = v
	return d
	
def set_metafields(product, metafields):
	"""Given a dict of metafield keys and values, set a product metafield for each key. If a metafield exists
		with that metafield key, it will be updated with the value provided. If a metafield does not exist
		with that metafield key, it will be created. """
		
	existing = get_metafields(product)
		
	for k,v in metafields.items():
		mf = shopify.Metafield({	"key": k,
				"value": v,
				"value_type": "string",		# TODO do this right
				"namespace": "global"})
		product.add_metafield(mf)			# this will update the metafield if the key exists
			
		if product.save() is False:
			message = 'Couldn\'t save product {}. Error messages: {}...'.format(
					product['Handle'],
					product.errors.full_messages()	)
			logger.error(message)
			raise RuntimeError(message)
		else:
			logger.info('Successfully updated product id {} with metafield {} = {}'.format(product.id, k, v))
			
"""Error classes"""
class Error(Exception):
	"""Base class for exceptions"""
	pass

class AuthenticationError(Error):
	"""Raised when an external service rejects our credentials for one reason or another"""
	
	def __init__(self, message):
		self.message = message
		
class ItemNotFoundError(Error):
	"""Raised when we try to look up an item and we don't find it."""

	def __init__(self, message):
		self.message = message		