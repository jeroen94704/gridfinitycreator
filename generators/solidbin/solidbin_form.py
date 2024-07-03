from flask_wtf import FlaskForm
from wtforms import IntegerField, DecimalField, SelectField, BooleanField
from wtforms.widgets import NumberInput
from grid_constants import *
import os
from generators.common.settings_form import get_standard_settings_form

class Form(FlaskForm):
    id = "solidbin"
    sizeUnitsX     = IntegerField("Width", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    sizeUnitsY     = IntegerField("Length", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    sizeUnitsZ     = IntegerField("Height", widget=NumberInput(min = 1, max = Grid.MAX_HEIGHT_UNITS), default=6)
    addStackingLip = BooleanField("Stacking lip", default="True")
    addMagnetHoles = BooleanField("Magnet holes", default="True")
    magnetHoleDiameter = DecimalField("Magnet-hole diameter", default = 6.5, places = 2)
    addRemovalHoles = BooleanField("Magnet removal holes", default="False")
    addScrewHoles   = BooleanField("Screw holes", default="False")
    exportFormat    = SelectField('Export format', choices=[('stl', 'STL'), ('step', 'STEP')])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def get_rows(self):
        return [
          ["Size", [self.sizeUnitsX, self.sizeUnitsY, self.sizeUnitsZ]],
          ["Magnets", [self.addMagnetHoles, self.addRemovalHoles, self.addScrewHoles, self.magnetHoleDiameter]],
          ["Other", [self.addStackingLip, self.exportFormat]],
        ]
    
    def get_title(self):
        return "Solid bin"
    
    def get_settings_html(self):
        return get_standard_settings_form()

    def get_description(self):
        with open(os.path.dirname(__file__) + '/solidbin_description.html', 'r') as reader:
            return reader.read()    
        
