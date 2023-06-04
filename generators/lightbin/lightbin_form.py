from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, BooleanField
from wtforms.widgets import NumberInput
from gridfinity_constants import *

class Form(FlaskForm):
    id = "lightbin"
    sizeUnitsX     = IntegerField("Width of the bin in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
    sizeUnitsY     = IntegerField("Length of the bin in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
    sizeUnitsZ     = IntegerField("Height of the bin in height-units", widget=NumberInput(min = 1, max = MAX_HEIGHT_UNITS), default=6)
    addStackingLip = BooleanField("Add a stacking lip", default="True")
    submit         = SubmitField('Generate STL', id=id, name=id)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def get_rows(self):
        return [
            [self.sizeUnitsX, self.sizeUnitsY, self.sizeUnitsZ],
            [self.addStackingLip],
            [self.submit]
        ]
    
    def get_title(self):
        return "Light bin"
    
    def get_description(self):
        return "This generates a light version of the normal Gridfinity bin that saves plastic and offers more room. This means magnets and/or screws are not possible"
