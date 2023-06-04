from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, BooleanField
from wtforms.widgets import NumberInput
from gridfinity_constants import *

class Form(FlaskForm):
    id = "solidbin"
    sizeUnitsX     = IntegerField("Width of the bin in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
    sizeUnitsY     = IntegerField("Length of the brick in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
    sizeUnitsZ     = IntegerField("Height of the brick in height-units", widget=NumberInput(min = 1, max = MAX_HEIGHT_UNITS), default=6)
    addStackingLip = BooleanField("Add a stacking lip", default="True")
    addMagnetHoles = BooleanField("Add holes for magnets", default="True")
    addScrewHoles  = BooleanField("Add holes for screws", default="True")
    submit         = SubmitField('Generate STL', id=id, name=id)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def get_rows(self):
        return [
            [self.sizeUnitsX, self.sizeUnitsY, self.sizeUnitsZ],
            [self.addStackingLip, self.addMagnetHoles, self.addScrewHoles],
            [self.submit]
        ]
    
    def get_title(self):
        return "Solid bin"
    
    def get_description(self):
        return "This generates a completely filled solid Gridfinity bin which can be used as a starting point for custom bins"
