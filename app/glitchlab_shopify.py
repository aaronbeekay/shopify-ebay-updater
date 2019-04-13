import os
import shopify
import logging
import pystache

# create logger with 'spam_application'
logger = logging.getLogger('glitchlab_shopify.slirp.aaronbeekay')
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
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
		