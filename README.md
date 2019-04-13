# shopify-ebay-updater
_A quick and dirty sync tool between Shopify items and eBay_

## Building and running
To build and run the application locally, make sure you have Docker installed on your local machine. Then all you should need to do is:

```
docker-compose build
docker-compose up
```

**TODO:** Later, when the app actually talks to things, you'll need to set local environment keys for your eBay and Shopify API keys. **Don't commit API keys to source control.**

## Contributing
### Static files (HTML interface)
These files are served by Nginx out of the `static/` directory. Just add or edit files in this directory and they will be available in the webroot.

### Backend (API requests)
Nginx will automatically redirect any request under the `<hostname>/api/` path to Flask.

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
