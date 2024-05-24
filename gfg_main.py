from flask import Flask, render_template, send_file, after_this_request, request
from flask_bootstrap import Bootstrap4
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, BooleanField
from wtforms.widgets import NumberInput
from waitress import serve
from grid_constants import *
from werkzeug.middleware.proxy_fix import ProxyFix
from contextlib import contextmanager

import logging
import os
import importlib
import sys

app = Flask(__name__)

# Flask-WTF requires an encryption key - the string can be anything
app.config['SECRET_KEY'] = 'hPqPfz!y=moJ!MVO{*tqQO$_Itoo:'
app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'flatly'

# Apply proxy fix
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Flask-Bootstrap requires this line
Bootstrap4(app)

generators = []
logger = None

# Constants
GEN_FOLDER = "./generators"
MAIN_MODULE = "main.py"

# Handle POST and GET requests for "/"
@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""

    form_list = []

    for gen in generators:
        # Create a list of forms to pass to Jinja for rendering
        f = gen.get_form()
        form_list.append(f)
        # Check if this POST request comes from the form of this generator
        if gen.handles(request, f):
            # Generate an STL with the provided settings
            return gen.process(f)

    return render_template('index.html', forms=form_list, message=message)

# From this StackOverflow answer: https://stackoverflow.com/a/41904558
@contextmanager
def add_to_path(p):
    import sys
    old_path = sys.path
    sys.path = sys.path[:]
    sys.path.insert(0, p)
    try:
        yield
    finally:
        sys.path = old_path

def load_generators():
    """Scan for generators and load any generators found """

    generators = []
    
    # Each generator is contained in its own subdir 
    possible_generators = sorted(os.listdir(GEN_FOLDER))
    for entry in possible_generators:
        location = os.path.join(GEN_FOLDER, entry)

        # It should be a dir and contain the 
        if not os.path.isdir(location) or not MAIN_MODULE in os.listdir(location):
            continue

        logger.info("Loading generator {0}".format(entry))
        fname = "{0}/{1}".format(location, MAIN_MODULE)

        # Temporarily expand the search path for modules, so the (sub-)modules needed
        # by each generator can be found
        with add_to_path(location):
            # importlib magic. Loads the module and makes it available to call
            spec = importlib.util.spec_from_loader(
                entry,
                importlib.machinery.SourceFileLoader(entry, fname)
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[entry] = module
            generators.append(module)

    return generators

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
    logger = logging.getLogger('GFG')
    portNum = 5000 if 'FLASK_PORT' not in os.environ else os.environ['FLASK_PORT']
    debugMode = False if 'FLASK_DEBUG' not in os.environ else (os.environ['FLASK_DEBUG'] == 'True')

    generators = load_generators()
    
    if debugMode:
        logger.info("Started in debug mode")
        port = int(os.environ.get('PORT', portNum))
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        logger.info("Started in production mode")
        serve(app, listen='*:' + str(portNum))