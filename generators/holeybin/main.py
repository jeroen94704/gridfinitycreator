from flask import send_file, Flask, after_this_request

import generators.holeybin.holeybin_generator as generator
import generators.holeybin.holeybin_form as form
import generators.holeybin.holeybin_settings as settings
import grid_constants

import uuid
import os

def get_generator(settings):
    return generator.Generator(settings)

def process(form, constants):
    # Copy the settings from the form
    s = settings.Settings()
    s.sizeUnitsX = form.sizeUnitsX.data
    s.sizeUnitsY = form.sizeUnitsY.data
    s.sizeUnitsZ = form.sizeUnitsZ.data
    s.addStackingLip = form.addStackingLip.data
    s.addMagnetHoles = form.addMagnetHoles.data
    s.addScrewHoles = form.addScrewHoles.data

    # Default grid (Gridfinity)
    if not constants:
        g = grid_constants.Grid()
    else:
        g = constants
    
    # Construct the names for the temporary and downloaded file
    filename = "/tmpfiles/" + str(uuid.uuid4()) + ".stl"

    # Generate the STL file
    gen = generator.Generator(s, g)
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
    downloadName = "HoleyBin_{0}x{1}x{2}_{3}_{4}x{5}.stl".format(s.sizeUnitsX, s.sizeUnitsY, s.sizeUnitsZ, s.holeShape, s.numHolesX, s.numHolesY)
    return send_file(filename, as_attachment=True, download_name=downloadName)

def get_form():
    return form.Form()

def handles(request, form):
    if form.id in request.form and form.validate_on_submit():
        return True
    
    return False