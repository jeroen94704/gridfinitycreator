from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, BooleanField, DecimalField, SelectField
from wtforms.widgets import NumberInput
from grid_constants import *
from holeybin_settings import HoleShape

import os

class Form(FlaskForm):
    id = "holeybin"
    numHolesX      = IntegerField("Width direction", description="Number of holes in the Width direction", widget=NumberInput(min = 1, max = Grid.MAX_COMPARTMENTS_PER_GRID_UNIT*Grid.MAX_GRID_UNITS), default=2)
    numHolesY      = IntegerField("Length direction", widget=NumberInput(min = 1, max = Grid.MAX_COMPARTMENTS_PER_GRID_UNIT*Grid.MAX_GRID_UNITS), default=2)
    holeDepth      = DecimalField("Depth", default = 5.0, places = 2)
    holeShape      = SelectField("Shape", choices=[(HoleShape.CIRCLE, "Circle"), (HoleShape.HEAXAGON, "Hexagon"), (HoleShape.SQUARE, "Square")])
    holeDiameter   = DecimalField("Diameter", default = 4.0, places = 2)
    keepoutShape   = SelectField("Shape", choices=[(HoleShape.CIRCLE, "Circle"), (HoleShape.HEAXAGON, "Hexagon"), (HoleShape.SQUARE, "Square")])
    keepoutDiameter = DecimalField("Diameter", default = 4.0, places = 2)

    addStackingLip  = BooleanField("Stacking lip", default="checked", false_values=(False, "false", ""))
    addMagnetHoles  = BooleanField("Magnet holes", default="true", false_values=(False, "false", ""))
    magnetHoleDiameter = DecimalField("Magnet-hole diameter", default = 6.5, places = 2)
    addRemovalHoles = BooleanField("Magnet removal holes", false_values=(False, "false", ""))
    addScrewHoles   = BooleanField("Screw holes", false_values=(False, "false", ""))

    exportFormat    = SelectField('Export format', choices=[('stl', 'STL'), ('step', 'STEP')])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def get_rows(self):
        return [
            ["Number of holes", [self.numHolesX, self.numHolesY]],
            ["Holes", [self.holeShape, self.holeDiameter, self.holeDepth]],
            ["Keepout", [self.keepoutShape, self.keepoutDiameter]],
            ["Other", [self.addStackingLip, self.exportFormat]],
            ["Magnets", [self.addMagnetHoles, self.addRemovalHoles, self.addScrewHoles, self.magnetHoleDiameter]],
        ]
    
    def get_title(self):
        return "Holey bin"
    
    def get_description(self):
        with open(os.path.dirname(__file__) + '/holeybin_description.html', 'r') as reader:
            return reader.read()    