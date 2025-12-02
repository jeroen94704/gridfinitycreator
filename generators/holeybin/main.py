from flask import send_file, Flask, after_this_request

import generators.holeybin.holeybin_generator as generator
import generators.holeybin.holeybin_form as form
import generators.holeybin.holeybin_settings as settings
import grid_constants

import uuid
import os
import logging

from holeybin_settings import HoleShape

logger = logging.getLogger('HBG')

def get_generator(settings):
    return generator.Generator(settings)

def process(form, constants):
    # Copy the settings from the form
    s = settings.Settings()
    s.numHolesX = form.numHolesX.data
    s.numHolesY = form.numHolesY.data
    s.sizeUnitsX = form.sizeUnitsX.data
    s.sizeUnitsY = form.sizeUnitsY.data
    s.holeShape = form.holeShape.data
    s.holeSize = float(form.holeSize.data)
    s.holeDepth      = float(form.holeDepth.data)
    s.keepoutDiameter   = float(form.keepoutDiameter.data)

    s.addStackingLip = form.addStackingLip.data
    s.addMagnetHoles = form.addMagnetHoles.data
    s.magnetHoleDiameter = float(form.magnetHoleDiameter.data)
    s.addRemovalHoles = form.addRemovalHoles.data
    s.addScrewHoles = form.addScrewHoles.data

    # Default grid (Gridfinity)
    if not constants:
        g = grid_constants.Grid()
    else:
        g = constants
    
    # Construct the names for the temporary and downloaded file
    filename = "/tmpfiles/" + str(uuid.uuid4()) + "." + form.exportFormat.data

    logger.info(s)

    # Generate the STL file
    gen = generator.Generator(s, g)
    gen.generate_stl(filename)

    logger.debug("Generating completed")

    # Delete the temp file after it was downloaded
    @after_this_request
    def delete_image(response):
        try:
            os.remove(filename)
        except Exception as ex:
            print(ex)
        return response


    # Send the generated STL file to the client
    downloadName = "HoleyBin_{0}x{1}x{2}.{3}".format(s.numHolesX, s.numHolesY, s.holeDepth, form.exportFormat.data)
    return send_file(filename, as_attachment=True, download_name=downloadName)

def get_form():
    return form.Form()

def handles(request, form):
    if form.id in request.form and form.validate_on_submit():
        return True

    return False

