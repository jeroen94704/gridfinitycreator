import lightbingenerator as generator
import lightbinform as form
import lightbinsettings as settings

def get_generator(settings):
    return generator.Generator(settings)


def handle(request):
    form = form.Form()
    if form.id in request.form and form.validate_on_submit():
        # Copy the settings from the form
        settings = settings.Settings()
        settings.sizeUnitsX = form.sizeUnitsX.data
        settings.sizeUnitsY = form.sizeUnitsY.data
        settings.sizeUnitsZ = form.sizeUnitsZ.data
        settings.addStackingLip = form.addStackingLip.data

        return 

    return False