from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, BooleanField
from wtforms.widgets import NumberInput
from gridfinity import *

class Form(FlaskForm):
    def __init__(self):
        FlaskForm.__init__(self)
        self.id = "lightbin"
        self.sizeUnitsX     = IntegerField("Width of the bin in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
        self.sizeUnitsY     = IntegerField("Length of the bin in grid units", widget=NumberInput(min = 1, max = MAX_GRID_UNITS), default=2)
        self.sizeUnitsZ     = IntegerField("Height of the bin in height-units", widget=NumberInput(min = 1, max = MAX_HEIGHT_UNITS), default=6)
        self.addStackingLip = BooleanField("Add a stacking lip", default="True")
        self.submit         = SubmitField('Generate STL', id=self.id, name=self.id)

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
    
    def dispatch(self, request):
        if self.id in request.form and self.validate_on_submit():
        
            return generate()            

        return False 