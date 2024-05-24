from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, BooleanField
from flask_bootstrap import Bootstrap5, SwitchField
from wtforms.widgets import NumberInput
from grid_constants import *
import os

class Form(FlaskForm):
    id = "lightbin"
    sizeUnitsX     = IntegerField("Width", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    sizeUnitsY     = IntegerField("Length", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    sizeUnitsZ     = IntegerField("Height", widget=NumberInput(min = 1, max = Grid.MAX_HEIGHT_UNITS), default=6)
    addStackingLip = BooleanField("Stacking lip", default="True")
    exportFormat   = SelectField('Export format', choices=[('stl', 'STL'), ('step', 'STEP')])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def get_rows(self):
        return [
            ["Size", [self.sizeUnitsX, self.sizeUnitsY, self.sizeUnitsZ]],
            ["Options", [self.addStackingLip, self.exportFormat]],
        ]
    
    def get_title(self):
        return "Light bin"
    
    def get_description(self):
        with open(os.path.dirname(__file__) + '/lightbin_description.html', 'r') as reader:
            return reader.read()       
