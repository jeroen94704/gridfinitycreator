from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, BooleanField
from wtforms.widgets import NumberInput
from grid_constants import *
import os
import help_provider as help

class Form(FlaskForm):
    id = "baseplate"
    sizeUnitsX     = IntegerField("Width", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    sizeUnitsY     = IntegerField("Length", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    exportFormat   = SelectField('Export format', choices=[('stl', 'STL'), ('step', 'STEP')])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sizeUnitsX.description = help.get_size_help()
        self.sizeUnitsY.description = help.get_size_help()
        self.exportFormat.description = help.get_exportformat_help()

    def get_rows(self):
        return [
            ["Size", [self.sizeUnitsX, self.sizeUnitsY]],
            ["Options", [self.exportFormat]],
        ]
    
    def get_title(self):
        return "Baseplate"
    
    def get_description(self):
        with open(os.path.dirname(__file__) + '/baseplate_description.html', 'r') as reader:
            return reader.read()       
