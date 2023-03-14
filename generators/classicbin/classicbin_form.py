from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, BooleanField
from wtforms.widgets import NumberInput
from gridfinity_constants import *

class Form(FlaskForm):
    id = "classicbin"
    sizeUnitsX     = IntegerField("Width of the bin in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
    sizeUnitsY     = IntegerField("Length of the brick in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
    sizeUnitsZ     = IntegerField("Height of the brick in height-units", widget=NumberInput(min = MIN_HEIGHT_UNITS, max = MAX_HEIGHT_UNITS), default=6)
    compartmentsX  = IntegerField("Number of compartments in the width direction", widget=NumberInput(min = 1, max = MAX_COMPARTMENTS_PER_GRID_UNIT*MAX_GRID_UNITS), default=3)
    compartmentsY  = IntegerField("Number of compartments in the length direction", widget=NumberInput(min = 1, max = MAX_COMPARTMENTS_PER_GRID_UNIT*MAX_GRID_UNITS), default=3)
    addStackingLip = BooleanField("Add a stacking lip", default="True")
    addMagnetHoles = BooleanField("Add holes for magnets", default="True")
    addScrewHoles  = BooleanField("Add holes for screws", default="True")
    addGrabCurve   = BooleanField("Add a curved scoop surface", default="True")
    addLabelRidge  = BooleanField("Add a label tab", default="True")
    multiLabel     = BooleanField("Add label tab for each compartment row", default="")
    submit         = SubmitField('Generate STL', id=id, name=id)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_rows(self):
        return [
          [self.sizeUnitsX, self.sizeUnitsY, self.sizeUnitsZ],
          [self.compartmentsX, self.compartmentsY],
          [self.addStackingLip, self.addMagnetHoles, self.addScrewHoles],
          [self.addGrabCurve, self.addLabelRidge, self.multiLabel],
          [self.submit]
        ]
    
    def get_title(self):
        return "Classic bin"
    
    def get_description(self):
        return "This generates a normal Gridfinity divider bin of your desired size with the extra option of compartments in both length and width directions"
    