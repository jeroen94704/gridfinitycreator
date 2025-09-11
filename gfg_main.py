import importlib
import logging
import logging.handlers
import os
import sys
import waitress

from contextlib import contextmanager

from flask import Flask, make_response, request, jsonify
from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template
from werkzeug.middleware.proxy_fix import ProxyFix

import grid_constants
from grid_constants import *
from version import __version__
from preview_generator import PreviewGenerator

app = Flask(__name__)

# Flask-WTF requires an encryption key - the string can be anything
app.config['SECRET_KEY'] = 'hPqPfz!y=moJ!MVO{*tqQO$_Itoo:'

# Apply proxy fix
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Globals
generators = []
logger = None

# Constants
GEN_FOLDER = "./generators"
MAIN_MODULE = "main.py"

def inner_render(value, context):
    return Template(value).render(context)

def render_index(form_list, constants, message):
    jinja_env = Environment(loader=FileSystemLoader(["./", os.path.realpath(__file__)]), undefined=StrictUndefined)
    jinja_env.filters["inner_render"] = inner_render

    index_template = jinja_env.get_template("templates/index.html")
    return index_template.render(version=__version__, forms=form_list, message=message, gridsize_x=constants.GRID_UNIT_SIZE_X_MM,
                            gridsize_y=constants.GRID_UNIT_SIZE_Y_MM, gridsize_z=constants.HEIGHT_UNITSIZE_MM)

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

    response = make_response(render_index(form_list, constants, ''))

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
            logger.info("Generating {0} for: {1}".format(f.get_title(), request.remote_addr))
            return gen.process(f, constants)
    
    response = make_response(render_index(form_list, constants, message))
    response.set_cookie('gridspec', str('{0},{1},{2}').format(constants.GRID_UNIT_SIZE_X_MM, constants.GRID_UNIT_SIZE_Y_MM, constants.HEIGHT_UNITSIZE_MM))
    return response

# Handle preview requests
@app.route('/preview', methods=['POST'])
def preview():
    """Generate a lightweight 3D preview for real-time visualization"""
    try:
        data = request.get_json()
        logger.info(f"Preview request data: {data}")
        
        # Get grid constants
        constants = grid_constants.Grid()
        if 'gridSpec' in data:
            constants.GRID_UNIT_SIZE_X_MM = float(data['gridSpec'].get('x', 42))
            constants.GRID_UNIT_SIZE_Y_MM = float(data['gridSpec'].get('y', 42))
            constants.HEIGHT_UNITSIZE_MM = float(data['gridSpec'].get('z', 7))
            constants.recalculate()
        
        # Find the appropriate generator
        generator_id = data.get('generator')
        form_data = data.get('formData', {})
        
        logger.info(f"Looking for generator: {generator_id}")
        logger.info(f"Available generators: {[gen.get_form().id for gen in generators]}")
        
        for gen in generators:
            form = gen.get_form()
            if form.id == generator_id:
                try:
                    # Import the specific generator and settings modules
                    import sys
                    import importlib
                    
                    # The generator modules are already loaded by the main app
                    # We need to access the classes from the imported modules
                    generator_module = gen
                    
                    # Import the generator and settings modules directly
                    generator_spec = importlib.util.spec_from_loader(
                        f'{generator_id}_generator',
                        importlib.machinery.SourceFileLoader(
                            f'{generator_id}_generator',
                            f'./generators/{generator_id}/{generator_id}_generator.py'
                        )
                    )
                    generator_module_obj = importlib.util.module_from_spec(generator_spec)
                    generator_spec.loader.exec_module(generator_module_obj)
                    
                    settings_spec = importlib.util.spec_from_loader(
                        f'{generator_id}_settings', 
                        importlib.machinery.SourceFileLoader(
                            f'{generator_id}_settings',
                            f'./generators/{generator_id}/{generator_id}_settings.py'
                        )
                    )
                    settings_module_obj = importlib.util.module_from_spec(settings_spec)
                    settings_spec.loader.exec_module(settings_module_obj)
                    
                    # Get the classes
                    generator_class = getattr(generator_module_obj, 'Generator')
                    settings_class = getattr(settings_module_obj, 'Settings')
                    
                    # Create settings object with form data
                    settings = settings_class()
                    for key, value in form_data.items():
                        if hasattr(settings, key):
                            # Convert to appropriate type
                            field_type = type(getattr(settings, key))
                            if field_type == int:
                                setattr(settings, key, int(value))
                            elif field_type == float:
                                setattr(settings, key, float(value))
                            elif field_type == bool and isinstance(value, str):
                                setattr(settings, key, value.lower() == 'true')
                            else:
                                setattr(settings, key, value)
                    
                    logger.info(f"Created settings: {settings}")
                    
                    # Generate the model
                    generator_instance = generator_class(settings, constants)
                    model = generator_instance.generate_model()
                    
                except Exception as e:
                    logger.error(f"Error creating generator instance: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
                
                # Generate preview STL
                preview_data = PreviewGenerator.generate_stl_preview(model, simplify=True)
                
                if preview_data:
                    return jsonify({
                        'success': True,
                        'data': preview_data,
                        'type': 'stl'
                    })
                else:
                    return jsonify({'success': False, 'error': 'Failed to generate preview'}), 500
        
        return jsonify({'success': False, 'error': 'Generator not found'}), 404
        
    except Exception as e:
        logger.error(f"Preview generation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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

        logger.debug("Loading generator {0}".format(entry))
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

class serverFilter():
    """Filter records coming from the server out of the access log"""
    def filter(self, record):
        return (record.name != 'werkzeug') and (record.name != 'waitress')

if __name__ == "__main__":
    portNum = 5000 if 'FLASK_PORT' not in os.environ else os.environ['FLASK_PORT']
    debugMode = False if 'FLASK_DEBUG' not in os.environ else (os.environ['FLASK_DEBUG'] == 'True')

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Configure console logger        
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    console.addFilter(serverFilter())
    root.addHandler(console)

    # Configure rotating file logger
    fh = logging.handlers.RotatingFileHandler('logs/access.log', maxBytes=1000000, backupCount=10)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    fh.setFormatter(formatter)
    fh.addFilter(serverFilter())
    root.addHandler(fh)

    logger = logging.getLogger('GFG')

    generators = load_generators()

    if debugMode:
        logger.info("Started in debug mode")
        port = int(os.environ.get('PORT', portNum))
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        logger.info("Started in production mode")
        waitress.serve(app, listen='*:' + str(portNum), threads=6)