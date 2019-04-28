# shopify-ebay-updater
_A quick and dirty sync tool between Shopify items and eBay_

## Building and running

### Running locally
To build and run the application locally, make sure you have Docker installed on your local machine. Then all you should need to do (_after you have set up your .env file -- see "Environment variables" below_) is:

```
docker build -t ebay-sync -f Dockerfile.flask .
docker run -it -p 5000:5000 ebay-sync
```

When you do this, the application will be available at http://localhost:5000/ .

#### Environment variables
The application's sensitive configuration information is stored in environment variables. If you don't set them properly, the app won't work correctly (for example, Shopify requests won't work because the Shopify API key won't be set.)

To conveniently set all of the environment variables, you can place them in a file called `.env` at the root level of the repository, in `VARIABLENAME=VARIABLEVALUE` format, one var per line.

At a minimum, your `.env` file should have the following:

```
APP_SECRET_KEY=(value)
EBAY_APP_RUNAME=(value)
EBAY_OAUTH_CLIENT_ID=(value)
EBAY_OAUTH_CLIENT_SECRET=(value)
SHOPIFY_API_KEY=(value)
SHOPIFY_API_PW=(value)
STATIC_FILE_DIR=/static
```

Some hints on setting these values:

* `APP_SECRET_KEY`: This is used to encrypt the client session variables when they are stored in a cookie. You can set it to any string, its length and value are not critical for local development.
* `EBAY_APP_RUNAME`: This is the "RuName (eBay Redirect URL name)" value that you've given eBay. You can find it under the "Get a Token from eBay via Your Applicaton" header on the [https://developer.ebay.com/my/auth?env=production&index=0 User Tokens] eBay Developer page. Make sure to select the eBay environment you want to run in (sandbox vs. production).
* `EBAY_OAUTH_CLIENT_ID`: Get this from the eBay Developer [https://developer.ebay.com/my/keys Application Keys] page. This is the value labeled "App ID (Client ID)".
* `EBAY_OAUTH_CLIENT_SECRET`: Get this from the same Application Keys page as `EBAY_OAUTH_CLIENT_ID`. This is the value labeled "Cert ID (Client Secret)".
* `SHOPIFY_API_KEY`: Since we're running as a Shopify "Private App" right now, you can get this from the "Private apps" page at https://<storename>.myshopify.com/admin/apps/private/. Click the app name you want to use. This value is labeled "API key" on that page.
* `SHOPIFY_API_PW`: Same page as `SHOPIFY_API_KEY`, this value is labeled "Password" on that page.
* `STATIC_FILE_DIR`: Leave this alone.

**Never commit your .env file to source control. Your `.gitignore` file should include `.env` to avoid doing so.**

#### Client session variables and eBay tokens
Because your eBay session token is fetched by the server in response to a callback from eBay that only goes to the production endpoint, eBay API access won't work when you're running the application locally.

**TODO: Add a method for copying session variables from the production application to a local instance, to allow for eBay API debugging when running locally.**

## Contributing
### Static files (HTML interface)
These files are served by Flask out of the `static/` directory. Just add or edit files in this directory and they will be available in the webroot.

### Backend (API requests)
Flask handles all of the HTTP requests that come in. The API endpoints should all be kept under the `/api/` path for clarity's sake.

The Python path is set to the `app/` directory, so any Python modules you save there can be imported from the main Flask module (`synctool.py`). 

When the container starts, it launches the Flask app in `synctool.py`.

### Logging
If you add a new module and want to log things from it to the main application log, all you need to do is add the following to the top of your module:

```
"""Logging setup"""
logger = logging.getLogger('io.glitchlab.YOUR-MODULE-NAME-HERE')
logger.setLevel(logging.DEBUG)
```

Then when you want to log something, you just do

`logger.debug("This message will be printed at the DEBUG log level")`

`logger.info("This message will be printed at the INFO log level")`

`logger.warning("This message will be printed at the WARNING log level")`

`logger.error("This message will be printed at the ERROR log level")`

No need to include timestamps or origin location, it'll all get formatted by the logger.

Fun!
