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
	});
}

/* Given an object representing one Shopify product, populate the form fields with its details. */
function populateShopifyProductInfo(product){	
	p = product.product;
	vs = p.variants;
	
	$('input#shopify-title').val(p.title);
	$('#shopify-description').summernote('reset');
	$('#shopify-description').summernote('pasteHTML', p.body_html);
	
	
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
	
	autoresize_descriptions();
	
	shopify_product_fields_enabled(true);
	
	// Update the eBay fields
	update_ebay_fields_from_shopify();
	autoresize_descriptions();
}

/* Request a single eBay product from the backend by its SKU, then pass it to populateEbayProductInfo() */
function loadEbayProduct( ebay_sku ){
	//var sku = ebay_sku.to_string();
	ebay_product_fields_enabled(false);
	$.ajax({
		type: "GET",
		url: '/api/ebay/product?sku=' + ebay_sku,
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
	
	autoresize_descriptions();
	
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
	
		// Enable all of the input elements
		$('.shopify-product-property').removeAttr('disabled');
	}
 }
 
/* Hit the backend eBay login status endpoint to see if we have good creds. Update the indicator as we go */
function check_ebay_auth(){
	set_ebay_login_status(login_status.checking);
	$.ajax({
		type: "GET",
		url: "/api/ebay/test-auth",
		success: function(data){
			if (data.ebay_auth_success === true){
				set_ebay_login_status(login_status.ok);
			} else {
				if(data.error == 'ebay_auth_refreshed'){
					check_ebay_auth();
				} else if('ebay_consent_url' in data) {
					$('a#ebay-auth-status-fail').attr('href', data.ebay_consent_url)
					set_ebay_login_status(login_status.fail);
				} else {
					$('a#ebay-auth-status-fail > small').remove()
					set_ebay_login_status(login_status.fail);
				}
			}
		}
	})
}

/* Hit the backend Shopify login status endpoint to see if we have good creds. Update the indicator as we go */
function check_shopify_auth(){
	set_shopify_login_status(login_status.checking);
	$.ajax({
		type: "GET",
		url: "/api/shopify/test-auth",
		success: function(data){
			if (data.shopify_auth_success === true){
				set_shopify_login_status(login_status.ok);
			} else {
				set_shopify_login_status(login_status.fail);
			}
		}
	})
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

/* Load the eBay item template from the static page */
var ebay_desc_template = null;
function load_ebay_template(){
	$.ajax({
		url: "/item-template.html",
		success: function(data){ ebay_desc_template = data; }
	});
}

/* Update the eBay item fields from the Shopify item fields */
function update_ebay_fields_from_shopify(){
	// Title
	$('input#ebay-title').val( $('input#shopify-title').val() );
	
	// Description
	apply_ebay_template();
	
	// Weight
	// 	TODO: update weight appropriately
	
	// Condition
	// 	TODO: map Shopify condition to eBay condition
	
	// Manufacturer
	$('input#ebay-manufacturer').val( $('input#shopify-manufacturer').val() );
	
	// MPN
	$('input#ebay-mpn').val( $('input#shopify-mpn').val() );
}

/* Render the Shopify item description (from the "Description" <textarea>) and dump it into the eBay
 * 	description <textarea> 
 */
function apply_ebay_template(){
	var sdesc = $('textarea#shopify-description').val();
	var stitle = $('input#shopify-title').val();
	var edesc = Mustache.render( ebay_desc_template, {
					item_name: stitle,
					item_description: sdesc			});
	$('#ebay-description-iframe').attr('srcdoc', edesc);
	autoresize_descriptions();
}

function set_ebay_login_status(state){
	switch(state){
		case login_status.checking:
			// Set the badge to "checking" state
			$('#ebay-auth-status').removeClass('badge-danger');
			$('#ebay-auth-status').removeClass('badge-success');
			$('#ebay-auth-status').addClass('badge-light');
			$('#ebay-auth-status').removeAttr('hidden');
			
			$('span#ebay-auth-status-ok').attr('hidden', true);
			$('span#ebay-auth-status-fail').attr('hidden', true);
			$('a#ebay-auth-status-fail').attr('hidden', true);
			$('span#ebay-auth-status-checking').removeAttr('hidden');
			
			$('div#ebay-auth-status-spinner').removeAttr('hidden');
			break;
		case login_status.ok:
			// Set the badge to "OK" state
			$('#ebay-auth-status').removeClass('badge-danger');
			$('#ebay-auth-status').addClass('badge-success');
			$('#ebay-auth-status').removeClass('badge-light');
			$('#ebay-auth-status').removeAttr('hidden');
			
			$('span#ebay-auth-status-ok').removeAttr('hidden');
			$('span#ebay-auth-status-fail').attr('hidden', true);
			$('a#ebay-auth-status-fail').attr('hidden', true);
			$('span#ebay-auth-status-checking').attr('hidden', true);
			
			$('div#ebay-auth-status-spinner').attr('hidden', true);
			break;
		case login_status.fail:
			// Set the badge to the failed state
			$('#ebay-auth-status').addClass('badge-danger');
			$('#ebay-auth-status').attr('hidden', true);
			$('#ebay-auth-status').removeClass('badge-success');
			$('#ebay-auth-status').removeClass('badge-light');
			
			$('span#ebay-auth-status-ok').attr('hidden', true);
			$('a#ebay-auth-status-fail').removeAttr('hidden');
			$('span#ebay-auth-status-checking').attr('hidden', true);
			
			$('div#ebay-auth-status-spinner').attr('hidden', true);
	}
}

/* Set up the rich text editors (Quill.js) for the description fields */
var q_sdesc = null;
var q_edesc = null;
function init_desc_richtext_editors(){

	var sn_toolbar = [
		['style', ['bold', 'italic', 'underline', 'clear']],
		['para', ['ul', 'ol']]
		];
	var sn_opts = {
		toolbar: sn_toolbar,
		height: 200				};

	$('#shopify-description').summernote( sn_opts );
	
	
	$('#shopify-description').on('summernote.change',  );
	
	// Set textarea and iframe height to match content height when edits get made
	$('#shopify-description').on('summernote.change', function(){
		// Update eBay desc with rendered template
		apply_ebay_template();
		
		autoresize_descriptions();
	} );
}

/* Update the size of the description boxes (textarea and iframe) to match their contents */
function autoresize_descriptions(){
	$('#shopify-description').height( $("#shopify-description")[0].scrollHeight + 'px' );
	$('#ebay-description-iframe').height( 
		$("#ebay-description-iframe")[0].contentWindow.document.body.offsetHeight + 10 + 'px' 
		);
}


$(document).ready(function(){
	load_ebay_template();
	
	$('input#shopify-id').change(function(){
		loadShopifyProduct($('input#shopify-id').val());
	});
	
	$('input#ebay-sku').change(function(){
		loadEbayProduct($('input#ebay-sku').val());
	});
	
	// Set radio button appearance based on state
	// 	TODO: This can probably be done trivially in CSS
	$('.ebay-toggle').click( function(){
		$(this).addClass('btn-secondary');
		$(this).removeClass('btn-outline-secondary');
		$(this).addClass('active');
		$(this).attr('checked', true);
		
		// Remove btn-secondary class from other labels so they look un-selected
		$(this).siblings().removeClass('btn-secondary');
		$(this).siblings().addClass('btn-outline-secondary');
		$(this).siblings().removeClass('active');
		$(this).siblings().removeAttr('checked')
	});
	
	init_desc_richtext_editors();
	check_ebay_auth();
	check_shopify_auth();
})
