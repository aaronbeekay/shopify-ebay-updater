// slirp-shopify.js

// the product (and its variants) that we're currently considering
var p = null;
var vs = [];
var ep = null;

function loadShopifyProduct(product_id){
	var pid = product_id.toString();
	shopify_product_fields_enabled(false);
	$.ajax({
		type: "GET",
		url: '/api/shopify/product?id=' + pid,
		success: function(data){ populateShopifyProductInfo(data) }
		//headers: { 'Authorization': 'Basic ' + btoa(SHOPIFY_ADMIN_APIKEY + ':' + SHOPIFY_ADMIN_APIPW)}
	});
}

/* Given an object representing one Shopify product, populate the form fields with its details. */
function populateShopifyProductInfo(product){	
	p = product.product;
	vs = p.variants;
	
	$('input#shopify-title').val(p.title);
	$('textarea#shopify-description').val(p.body_html);
	
	// Verify that the "Option 1" field is being used to describe product condition
	if( p.options[0].name != 'Condition'){
		condition_field_structure_warning(true);
	} else {
		condition_field_structure_warning(false);
	}
	
	// Loop over all the variants (all products have at least one variant)
	$('select#shopify-variants-list').empty();
	for (var i = 0; i < vs.length; i++){
		var v = vs[i];
		$('select#shopify-variants-list').append(
			'<option value="' + v.id + '">' + v.id + ' (' + v.option1 + ')' + '</option>'
			);
	}
	$('input#shopify-weight').val('??');
	$('input#shopify-condition').val('??');
	
	shopify_product_fields_enabled(true);
}

/* Request a single eBay product from the backend by its SKU, then pass it to populateEbayProductInfo() */
function loadEbayProduct( ebay_sku ){
	//var sku = ebay_sku.to_string();
	ebay_product_fields_enabled(false);
	$.ajax({
		type: "GET",
		url: '/api/ebay/product?id=' + ebay_sku,
		success: function(data){ populateEbayProductInfo(data) }
	});
}

/* Given an object representing one eBay product, populate the eBay form fields with its details. */
function populateEbayProductInfo(product){	
	ep = product;
	
	$('input#ebay-title').val(ep.product.title);
	if('description' in ep.product){
		$('textarea#ebay-description').val(ep.product.description);
	} else {
		// set the hint text to the desc field to indicate there is no desc
		$('textarea#ebay-description').attr('placeholder', 'No eBay description set');
	}
	
	if (('weight' in ep.packageWeightAndSize) & ('value' in ep.packageWeightAndSize.weight)){
		$('input#ebay-weight').val(ep.packageWeightAndSize.weight.value);
		// TODO: show unit
	} else {
		// set hint text in weight field to indicate there is no weight set
		$('input#ebay-weight').attr('placeholder', 'No eBay weight set');
	}
	
	$('input#ebay-condition').val(ep.condition);
	
	ebay_product_fields_enabled(true);
}

/* Display or hide the condition field warning on the page.
 * 	This warning should appear when the active Shopify product's first option
 * 	is *not* being used to describe the item condition.
 */
function condition_field_structure_warning(display){
	if (display === true){
		$('#condition-structure-warning').show();
	} else {
		$('#condition-structure-warning').hide();
	}
}

/* Disable (lock out) the eBay product fields while stuff is loading/saving from backend
 * 	Also displays/hides the spinner in the eBay SKU box
 */
function ebay_product_fields_enabled(state){
 	if(state===false){ 	
		// Show spinner
		$('#ebay-loading-spinner').show()
	
		// Disable all of the input elements
		$('.ebay-product-property').attr('disabled', true);
	} else {
		// Hide spinner
		$('#ebay-loading-spinner').hide()
	
		// Disable all of the input elements
		$('.ebay-product-property').removeAttr('disabled');
	}
 }

/* Disable (lock out) the Shopify product fields while the stuff is loading from backend
 * 	Also displays/hides the spinner in the Shopify ID box
 */
function shopify_product_fields_enabled(state){
 	if(state===false){ 	
		// Show spinner
		$('#shopify-loading-spinner').show()
	
		// Disable all of the input elements
		$('.shopify-product-property').attr('disabled', true);
	} else {
		// Hide spinner
		$('#shopify-loading-spinner').hide()
	
		// Disable all of the input elements
		$('.shopify-product-property').removeAttr('disabled');
	}
 }
 
/* Set the state of the auth badge at the top of the page. */
const login_status = {"checking": 1, "ok": 2, "fail": 3};
function set_shopify_login_status(state){
	switch(state){
		case login_status.checking:
			// Set the badge to "checking" state
			$('#shopify-auth-status').removeClass('badge-danger');
			$('#shopify-auth-status').removeClass('badge-success');
			$('#shopify-auth-status').addClass('badge-light');
			
			$('span#shopify-auth-status-ok').attr('hidden', true);
			$('span#shopify-auth-status-fail').attr('hidden', true);
			$('span#shopify-auth-status-checking').removeAttr('hidden');
			
			$('div#shopify-auth-status-spinner').removeAttr('hidden');
			break;
		case login_status.ok:
			// Set the badge to "OK" state
			$('#shopify-auth-status').removeClass('badge-danger');
			$('#shopify-auth-status').addClass('badge-success');
			$('#shopify-auth-status').removeClass('badge-light');
			
			$('span#shopify-auth-status-ok').removeAttr('hidden');
			$('span#shopify-auth-status-fail').attr('hidden', true);
			$('span#shopify-auth-status-checking').attr('hidden', true);
			
			$('div#shopify-auth-status-spinner').attr('hidden', true);
			break;
		case login_status.fail:
			// Set the badge to the failed state
			$('#shopify-auth-status').addClass('badge-danger');
			$('#shopify-auth-status').removeClass('badge-success');
			$('#shopify-auth-status').removeClass('badge-light');
			
			$('span#shopify-auth-status-ok').attr('hidden', true);
			$('span#shopify-auth-status-fail').removeAttr('hidden');
			$('span#shopify-auth-status-checking').attr('hidden', true);
			
			$('div#shopify-auth-status-spinner').attr('hidden', true);
	}
}

function set_ebay_login_status(state){
	switch(state){
		case login_status.checking:
			// Set the badge to "checking" state
			$('#ebay-auth-status').removeClass('badge-danger');
			$('#ebay-auth-status').removeClass('badge-success');
			$('#ebay-auth-status').addClass('badge-light');
			
			$('span#ebay-auth-status-ok').attr('hidden', true);
			$('span#ebay-auth-status-fail').attr('hidden', true);
			$('span#ebay-auth-status-checking').removeAttr('hidden');
			
			$('div#ebay-auth-status-spinner').removeAttr('hidden');
			break;
		case login_status.ok:
			// Set the badge to "OK" state
			$('#ebay-auth-status').removeClass('badge-danger');
			$('#ebay-auth-status').addClass('badge-success');
			$('#ebay-auth-status').removeClass('badge-light');
			
			$('span#ebay-auth-status-ok').removeAttr('hidden');
			$('span#ebay-auth-status-fail').attr('hidden', true);
			$('span#ebay-auth-status-checking').attr('hidden', true);
			
			$('div#ebay-auth-status-spinner').attr('hidden', true);
			break;
		case login_status.fail:
			// Set the badge to the failed state
			$('#ebay-auth-status').addClass('badge-danger');
			$('#ebay-auth-status').removeClass('badge-success');
			$('#ebay-auth-status').removeClass('badge-light');
			
			$('span#ebay-auth-status-ok').attr('hidden', true);
			$('span#ebay-auth-status-fail').removeAttr('hidden');
			$('span#ebay-auth-status-checking').attr('hidden', true);
			
			$('div#ebay-auth-status-spinner').attr('hidden', true);
	}
}

$('input#shopify-id').change(function(){
	loadShopifyProduct($('input#shopify-id').val());
});
$('input#ebay-sku').change(function(){
	loadEbayProduct($('input#ebay-sku').val());
});