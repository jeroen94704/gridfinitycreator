from flask import Flask, send_file, after_this_request

import lightbin_generator as generator
import lightbin_form as form
import lightbin_settings as settings

import uuid
import os

def get_generator(settings):
    return generator.Generator(settings)

def process(form):
    # Copy the settings from the form
    s = settings.Settings()
    s.sizeUnitsX = form.sizeUnitsX.data
    s.sizeUnitsY = form.sizeUnitsY.data
    s.sizeUnitsZ = form.sizeUnitsZ.data
    s.addStackingLip = form.addStackingLip.data

    # Construct the names for the temporary and downloaded file
    filename = "/tmpfiles/" + str(uuid.uuid4()) + ".stl"

    # Generate the STL file
    gen = generator.Generator(s)
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
    downloadName = "Light divider bin {0}x{1}x{2}.stl".format(s.sizeUnitsX, s.sizeUnitsY, s.sizeUnitsZ)
    return send_file(filename, as_attachment=True, download_name=downloadName)

def get_form():
    return form.Form()

def handles(request, form):
    if form.id in request.form and form.validate_on_submit():
        return True
    
    return False