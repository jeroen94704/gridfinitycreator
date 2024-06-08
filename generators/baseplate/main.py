from flask import send_file, Flask, after_this_request

import baseplate_generator as generator
import baseplate_form as form
import baseplate_settings as settings
import grid_constants

import uuid
import os
import logging

logger = logging.getLogger('BPG')

def process(form, constants):
    # Copy the settings from the form
    s = settings.Settings()
    
    # Copy the settings from the form
    s.sizeUnitsX = form.sizeUnitsX.data
    s.sizeUnitsY = form.sizeUnitsY.data

    # Default grid (Gridfinity)
    if not constants:
        g = grid_constants.Grid()
    else:
        g = constants

    # Construct the names for the temporary and downloaded file
    filename = "/tmpfiles/" + str(uuid.uuid4()) + "." + form.exportFormat.data

    # Generate the STL file
    gen = generator.Generator(s, g)
    gen.generate_stl(filename)

    # Delete the temp file after it was downloaded
    @after_this_request
    def delete_image(response):
        try:
            os.remove(filename)
            logger.debug("Removed temp file {0}".format(filename))
        except Exception as ex:
            logger.critical(ex)
        return response

    logger.info(s)

    # Send the generated STL file to the client
    downloadName = "Baseplate {0}x{1}.{2}".format(s.sizeUnitsX, s.sizeUnitsY, form.exportFormat.data)
    return send_file(filename, as_attachment=True, download_name=downloadName)

def get_form():
    return form.Form()

def handles(request, form):
    if form.id in request.form and form.validate_on_submit():
        return True
    
    return False