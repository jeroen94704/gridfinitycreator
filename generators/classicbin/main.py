from flask import send_file, Flask, after_this_request

import classicbin_generator as generator
import classicbin_form as form
import classicbin_settings as settings

import uuid
import os

def process(form):
    # Copy the settings from the form
    s = settings.Settings()
        # Copy the settings from the form
    s.sizeUnitsX = form.sizeUnitsX.data
    s.sizeUnitsY = form.sizeUnitsY.data
    s.sizeUnitsZ = form.sizeUnitsZ.data
    s.compartmentsX = form.compartmentsX.data
    s.compartmentsY = form.compartmentsY.data
    s.addStackingLip = form.addStackingLip.data
    s.addMagnetHoles = form.addMagnetHoles.data
    s.addScrewHoles = form.addScrewHoles.data
    s.addGrabCurve = form.addGrabCurve.data
    s.addLabelRidge = form.addLabelRidge.data
    s.multiLabel = form.multiLabel.data

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
    downloadName = "Divider Bin {0}x{1}x{2} {3}x{4} Compartments.stl".format(s.sizeUnitsX, s.sizeUnitsY, s.sizeUnitsZ, s.compartmentsX, s.compartmentsY)
    return send_file(filename, as_attachment=True, download_name=downloadName)

def get_form():
    return form.Form()

def handles(request, form):
    if form.id in request.form and form.validate_on_submit():
        return True
    
    return False