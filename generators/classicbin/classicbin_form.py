from flask_wtf import FlaskForm
from wtforms import IntegerField, DecimalField, SelectField
from flask_bootstrap import Bootstrap5, SwitchField
from wtforms.widgets import NumberInput
from grid_constants import *

import os

class Form(FlaskForm):
    id = "classicbin"
    sizeUnitsX      = IntegerField("Width", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    sizeUnitsY      = IntegerField("Length", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    sizeUnitsZ      = IntegerField("Height", widget=NumberInput(min = Grid.MIN_HEIGHT_UNITS, max = Grid.MAX_HEIGHT_UNITS), default=6)
    compartmentsX   = IntegerField("Width direction", widget=NumberInput(min = 1, max = Grid.MAX_COMPARTMENTS_PER_GRID_UNIT*Grid.MAX_GRID_UNITS), default=3)
    compartmentsY   = IntegerField("Length direction", widget=NumberInput(min = 1, max = Grid.MAX_COMPARTMENTS_PER_GRID_UNIT*Grid.MAX_GRID_UNITS), default=3)
    addStackingLip  = SwitchField("Stacking lip", default="True") #, description="The stacking lip is the raised edge at the top of the bin into which another bin fits. On by default, but sometimes you may want to omit it."
    addMagnetHoles  = SwitchField("Magnet holes", default="True")
    magnetHoleDiameter = DecimalField("Magnet-hole diameter", default = 6.5, places = 2)
    addRemovalHoles = SwitchField("Magnet removal holes", default="False")
    addScrewHoles   = SwitchField("Screw holes", default="False")
    addGrabCurve    = SwitchField("Scoop ramp", default="True")
    addLabelRidge   = SwitchField("Add label tab(s)", default="True")
    multiLabel      = SwitchField("Label tab per row", default="False")
    exportFormat    = SelectField('Export format', choices=[('stl', 'STL'), ('step', 'STEP')])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_rows(self):
        return [
          ["Size", [self.sizeUnitsX, self.sizeUnitsY, self.sizeUnitsZ]],
          ["Compartments", [self.compartmentsX, self.compartmentsY]],
          ["Magnets", [self.addMagnetHoles, self.addRemovalHoles, self.addScrewHoles, self.magnetHoleDiameter]],
          ["Other", [self.addStackingLip, self.addGrabCurve, self.exportFormat]],
          ["Labels", [self.addLabelRidge, self.multiLabel]],
        ]
    
    def get_title(self):
        return "Divider bin"
    
    def get_description(self):
        with open(os.path.dirname(__file__) + '/classicbin_description.html', 'r') as reader:
            return reader.read()    