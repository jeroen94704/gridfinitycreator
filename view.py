from flask import Flask, render_template, send_file, after_this_request, request
from flask_bootstrap import Bootstrap4, SwitchField
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, BooleanField
from wtforms.widgets import NumberInput
from waitress import serve
from gridfinity import *
from werkzeug.middleware.proxy_fix import ProxyFix

import logging
import os
import dividerbin as dividerbin
import lightbin as lightbin
import solidbin as solidbin
import uuid

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

class GridfinityBinForm(FlaskForm):
    sizeUnitsX     = IntegerField("Width of the bin in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
    sizeUnitsY     = IntegerField("Length of the brick in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
    sizeUnitsZ     = IntegerField("Height of the brick in height-units", widget=NumberInput(min = 1, max = MAX_HEIGHT_UNITS), default=6)
    compartmentsX  = IntegerField("Number of compartments in the width direction", widget=NumberInput(min = 1, max = MAX_COMPARTMENTS_PER_GRID_UNIT*MAX_GRID_UNITS), default=3)
    compartmentsY  = IntegerField("Number of compartments in the length direction", widget=NumberInput(min = 1, max = MAX_COMPARTMENTS_PER_GRID_UNIT*MAX_GRID_UNITS), default=3)
    addStackingLip = BooleanField("Add a stacking lip", default="True")
    addMagnetHoles = BooleanField("Add holes for magnets", default="True")
    addScrewHoles  = BooleanField("Add holes for screws", default="True")
    addGrabCurve   = BooleanField("Add a curved scoop surface", default="True")
    addLabelRidge  = BooleanField("Add a label tab", default="True")
    multiLabel     = BooleanField("Add label tab for each compartment row", default="")
    submit         = SubmitField('Generate STL', id="cassicbin", name="classicbin")

class LightBinForm(FlaskForm):
    sizeUnitsX     = IntegerField("Width of the bin in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
    sizeUnitsY     = IntegerField("Length of the brick in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
    sizeUnitsZ     = IntegerField("Height of the brick in height-units", widget=NumberInput(min = 1, max = MAX_HEIGHT_UNITS), default=6)
    addStackingLip = BooleanField("Add a stacking lip", default="True")
    submit         = SubmitField('Generate STL', id="lightbin", name="lightbin")

class SolidBinForm(FlaskForm):
    sizeUnitsX     = IntegerField("Width of the bin in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
    sizeUnitsY     = IntegerField("Length of the brick in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
    sizeUnitsZ     = IntegerField("Height of the brick in height-units", widget=NumberInput(min = 1, max = MAX_HEIGHT_UNITS), default=6)
    addStackingLip = BooleanField("Add a stacking lip", default="True")
    addMagnetHoles = BooleanField("Add holes for magnets", default="True")
    addScrewHoles  = BooleanField("Add holes for screws", default="True")
    submit         = SubmitField('Generate STL', id="solidbin", name="solidbin")

def generateGridfinityBin(binform):
    # Copy the settings from the form
    settings = dividerbin.Settings()
    settings.sizeUnitsX = binform.sizeUnitsX.data
    settings.sizeUnitsY = binform.sizeUnitsY.data
    settings.sizeUnitsZ = binform.sizeUnitsZ.data
    settings.compartmentsX = binform.compartmentsX.data
    settings.compartmentsY = binform.compartmentsY.data
    settings.addStackingLip = binform.addStackingLip.data
    settings.addMagnetHoles = binform.addMagnetHoles.data
    settings.addScrewHoles = binform.addScrewHoles.data
    settings.addGrabCurve = binform.addGrabCurve.data
    settings.addLabelRidge = binform.addLabelRidge.data
    settings.multiLabel = binform.multiLabel.data

    # Construct the names for the temporary and downloaded file
    filename = "/tmpfiles/" + str(uuid.uuid4()) + ".stl"
    downloadName = "Divider Bin {0}x{1}x{2} {3}x{4} Compartments.stl".format(settings.sizeUnitsX, settings.sizeUnitsY, settings.sizeUnitsZ, settings.compartmentsX, settings.compartmentsY)

    # Generate the STL file
    gen = dividerbin.DividerbinGenerator(settings)
    gen.generate_stl(filename)
    
    # Delete the temp file after it was downloaded
    @after_this_request
    def delete_image(response):
        try:
            os.remove(filename)
        except Exception as ex:
            print(ex)
        return response

    # Send the generated STL file to the client
    return send_file(filename, as_attachment=True, download_name=downloadName)

def generateLightBin(lightform):
    # Copy the settings from the form
    settings = lightbin.Settings()
    settings.sizeUnitsX = lightform.sizeUnitsX.data
    settings.sizeUnitsY = lightform.sizeUnitsY.data
    settings.sizeUnitsZ = lightform.sizeUnitsZ.data
    settings.addStackingLip = lightform.addStackingLip.data

    # Construct the names for the temporary and downloaded file
    filename = "/tmpfiles/" + str(uuid.uuid4()) + ".stl"
    downloadName = "Light divider bin {0}x{1}x{2}.stl".format(settings.sizeUnitsX, settings.sizeUnitsY, settings.sizeUnitsZ)

    # Generate the STL file
    gen = lightbin.LightbinGenerator(settings)
    gen.generate_stl(filename)

    # Delete the temp file after it was downloaded
    @after_this_request
    def delete_image(response):
        try:
            os.remove(filename)
        except Exception as ex:
            print(ex)
        return response

    # Send the generated STL file to the client
    return send_file(filename, as_attachment=True, download_name=downloadName)

def generateSolidBin(solidform):
    # Copy the settings from the form
    settings = solidbin.Settings()
    settings.sizeUnitsX = solidform.sizeUnitsX.data
    settings.sizeUnitsY = solidform.sizeUnitsY.data
    settings.sizeUnitsZ = solidform.sizeUnitsZ.data
    settings.addStackingLip = solidform.addStackingLip.data
    settings.addMagnetHoles = solidform.addMagnetHoles.data
    settings.addScrewHoles = solidform.addScrewHoles.data

    # Construct the names for the temporary and downloaded file
    filename = "/tmpfiles/" + str(uuid.uuid4()) + ".stl"
    downloadName = "Solid Bin {0}x{1}x{2}.stl".format(settings.sizeUnitsX, settings.sizeUnitsY, settings.sizeUnitsZ)

    # Generate the STL file
    gen = solidbin.SolidbinGenerator(settings)
    gen.generate_stl(filename)
    
    # Delete the temp file after it was downloaded
    @after_this_request
    def delete_image(response):
        try:
            os.remove(filename)
        except Exception as ex:
            print(ex)
        return response

    # Send the generated STL file to the client
    return send_file(filename, as_attachment=True, download_name=downloadName)

@app.route('/', methods=['GET', 'POST'])
def index():
    # you must tell the variable 'form' what you named the class, above
    # 'form' is the variable name used in this template: index.html
    binform = GridfinityBinForm()
    lightform = LightBinForm()
    solidform = SolidBinForm()
    message = ""

    # Handle form submissions
    if "classicbin" in request.form and binform.validate_on_submit():
        return generateGridfinityBin(binform)

    if "lightbin" in request.form and lightform.validate_on_submit():
        return generateLightBin(lightform)

    if "solidbin" in request.form and solidform.validate_on_submit():
        return generateSolidBin(solidform)

    return render_template('index.html', binform=binform, lightform=lightform, solidform=solidform, message=message)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
    logger = logging.getLogger('waitress')
    portNum = 5000 if 'FLASK_PORT' not in os.environ else os.environ['FLASK_PORT']
    debugMode = False if 'FLASK_DEBUG' not in os.environ else (os.environ['FLASK_DEBUG'] == 'True')

    if debugMode:
        logger.info("GFG started in debug mode")
        port = int(os.environ.get('PORT', portNum))
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        logger.info("GFG started in production mode")
        serve(app, listen='*:' + str(portNum))