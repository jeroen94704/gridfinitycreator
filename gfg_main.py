from flask import Flask, render_template, session, make_response, request
from flask_bootstrap import Bootstrap4
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, BooleanField
from wtforms.widgets import NumberInput
from waitress import serve
from grid_constants import *
from werkzeug.middleware.proxy_fix import ProxyFix
from contextlib import contextmanager
from dataclasses import dataclass

import grid_constants
from version import __version__

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

# Handle GET requests for "/"
@app.route('/', methods=['GET'])
def index_get():

    constants = grid_constants.Grid()

    # If a grid spec cookie is found, set the values contained in it
    if request.cookies.get('gridspec'):
        values = request.cookies.get('gridspec').split(',')
        constants.GRID_UNIT_SIZE_X_MM = float(values[0])
        constants.GRID_UNIT_SIZE_Y_MM = float(values[1])
        constants.HEIGHT_UNITSIZE_MM = float(values[2])

    constants.recalculate() # Recalculate derived measures

    form_list = []

    # Create a list of forms to pass to Jinja for rendering
    for gen in generators:
        form_list.append(gen.get_form())

    response = make_response(render_template('index.html', version=__version__, forms=form_list, message='', gridsize_x=constants.GRID_UNIT_SIZE_X_MM,
                                             gridsize_y=constants.GRID_UNIT_SIZE_Y_MM, gridsize_z=constants.HEIGHT_UNITSIZE_MM))

    if not request.cookies.get('gridspec'):
        response.set_cookie('gridspec', str('{0},{1},{2}').format(constants.GRID_UNIT_SIZE_X_MM, constants.GRID_UNIT_SIZE_Y_MM, constants.HEIGHT_UNITSIZE_MM))
    
    return response

# Handle POST requests for "/"
@app.route('/', methods=['POST'])
def index_post():
    # Default gridspec
    constants = grid_constants.Grid()

    message = ""

    # Use the saved grid size if it was overridden
    if request.cookies.get('gridspec'):
        c = request.cookies.get('gridspec')
        values = c.split(',')
        constants.GRID_UNIT_SIZE_X_MM = float(values[0])
        constants.GRID_UNIT_SIZE_Y_MM = float(values[1])
        constants.HEIGHT_UNITSIZE_MM = float(values[2])
        constants.recalculate()  # Recalculate derived measures


    # If the request is from the form that specifies the grid size, override these values
    if 'advanced_settings' in request.form:
        # Save settings
        constants.GRID_UNIT_SIZE_X_MM = float(request.form['gridSizeX'])
        constants.GRID_UNIT_SIZE_Y_MM = float(request.form['gridSizeY'])
        constants.HEIGHT_UNITSIZE_MM = float(request.form['gridSizeZ'])
        constants.recalculate()  # Recalculate derived measures

    form_list = []

    for gen in generators:
        # Find the generator for this request
        f = gen.get_form()
        form_list.append(f)
        if gen.handles(request, f):
            # Generate an STL with the provided settings
            return gen.process(f, constants)

    response = make_response(render_template('index.html', version=__version__, forms=form_list, message=message, gridsize_x=constants.GRID_UNIT_SIZE_X_MM,
                                             gridsize_y=constants.GRID_UNIT_SIZE_Y_MM, gridsize_z=constants.HEIGHT_UNITSIZE_MM))
    response.set_cookie('gridspec', str('{0},{1},{2}').format(constants.GRID_UNIT_SIZE_X_MM, constants.GRID_UNIT_SIZE_Y_MM, constants.HEIGHT_UNITSIZE_MM))
    return response

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