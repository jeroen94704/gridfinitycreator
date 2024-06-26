from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, BooleanField
from wtforms.widgets import NumberInput
from grid_constants import *
import os
import help_provider as help

class Form(FlaskForm):
    id = "lightbin"
    sizeUnitsX     = IntegerField("Width", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    sizeUnitsY     = IntegerField("Length", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    sizeUnitsZ     = IntegerField("Height", widget=NumberInput(min = 1, max = Grid.MAX_HEIGHT_UNITS), default=6)
    addStackingLip = BooleanField("Stacking lip", default="True")
    addLabelRidge  = BooleanField("Add label tab", default="True", false_values=(False, "false", ""))
    exportFormat   = SelectField('Export format', choices=[('stl', 'STL'), ('step', 'STEP')])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sizeUnitsX.description = help.get_size_help()
        self.sizeUnitsY.description = help.get_size_help()
        self.sizeUnitsZ.description = help.get_size_help()
        self.addStackingLip.description = help.get_stackinglip_help()
        self.exportFormat.description = help.get_exportformat_help()
        self.addLabelRidge.description = help.get_labeltab_help()

    def get_rows(self):
        return [
            ["Size", [self.sizeUnitsX, self.sizeUnitsY, self.sizeUnitsZ]],
            ["Options", [self.addStackingLip, self.addLabelRidge, self.exportFormat]],
        ]
    
    def get_title(self):
        return "Light bin"
    
    def get_description(self):
        with open(os.path.dirname(__file__) + '/lightbin_description.html', 'r') as reader:
            return reader.read()       
