from flask_wtf import FlaskForm
from wtforms import IntegerField, DecimalField, SelectField, BooleanField
from wtforms.widgets import NumberInput
from grid_constants import *

import os
import help_provider as help
from generators.common.settings_form import get_standard_settings_form

class Form(FlaskForm):
    id = "classicbin"
    sizeUnitsX      = IntegerField("Width", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    sizeUnitsY      = IntegerField("Length", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    sizeUnitsZ      = IntegerField("Height", widget=NumberInput(min = Grid.MIN_HEIGHT_UNITS, max = Grid.MAX_HEIGHT_UNITS), default=6)
    compartmentsX   = IntegerField("Width direction", widget=NumberInput(min = 1, max = Grid.MAX_COMPARTMENTS_PER_GRID_UNIT*Grid.MAX_GRID_UNITS), default=3)
    compartmentsY   = IntegerField("Length direction", widget=NumberInput(min = 1, max = Grid.MAX_COMPARTMENTS_PER_GRID_UNIT*Grid.MAX_GRID_UNITS), default=3)
    addStackingLip  = BooleanField("Stacking lip", default="checked", false_values=(False, "false", ""))
    addMagnetHoles  = BooleanField("Magnet holes", default="true", false_values=(False, "false", ""))
    magnetHoleDiameter = DecimalField("Magnet-hole diameter", default = 6.5, places = 2)
    addRemovalHoles = BooleanField("Magnet removal holes", false_values=(False, "false", ""))
    addScrewHoles   = BooleanField("Screw holes", false_values=(False, "false", ""))
    addGrabCurve    = BooleanField("Scoop ramp", default="true", false_values=(False, "false", ""))
    addLabelRidge   = BooleanField("Add label tab(s)", default="true", false_values=(False, "false", ""))
    multiLabel      = BooleanField("Label tab per row", false_values=(False, "false", ""))
    exportFormat    = SelectField('Export format', choices=[('stl', 'STL'), ('step', 'STEP')])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sizeUnitsX.description = help.get_size_help()
        self.sizeUnitsY.description = help.get_size_help()
        self.sizeUnitsZ.description = help.get_size_help()
        self.compartmentsX.description = help.get_compartment_help()
        self.compartmentsY.description = help.get_compartment_help()
        self.addStackingLip.description = help.get_stackinglip_help()
        self.addMagnetHoles.description = help.get_magnet_help()
        self.magnetHoleDiameter.description = help.get_magnet_help()
        self.addRemovalHoles.description = help.get_magnet_help()
        self.addScrewHoles.description = help.get_magnet_help()
        self.addGrabCurve.description = help.get_scoopramp_help()
        self.addLabelRidge.description = help.get_labeltab_help()
        self.multiLabel.description = help.get_labeltab_help()
        self.exportFormat.description = help.get_exportformat_help()

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
    
    def get_settings_html(self):
        return get_standard_settings_form()
    
    def get_description(self):
        with open(os.path.dirname(__file__) + '/classicbin_description.html', 'r') as reader:
            return reader.read()    