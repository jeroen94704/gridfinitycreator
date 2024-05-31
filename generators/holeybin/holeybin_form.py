from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, BooleanField, DecimalField, SelectField
from wtforms.widgets import NumberInput
from grid_constants import *
from holeybin_settings import HoleShape

class Form(FlaskForm):
    id = "holeybin"
    numHolesX      = IntegerField("Number of holes in the Width direction", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    numHolesY      = IntegerField("Number of holes in the Length direction", widget=NumberInput(min = 1, max = Grid.MAX_GRID_UNITS), default=2)
    sizeUnitsZ     = IntegerField("Height of the brick in height-units", widget=NumberInput(min = 1, max = Grid.MAX_HEIGHT_UNITS), default=6)
    holeShape      = SelectField("Shape of the holes in the grid", choices=[(HoleShape.CIRCLE, "Circle"), (HoleShape.HEAXAGON, "Hexagon"), (HoleShape.SQUARE, "Square")])
    holeDiameter   = DecimalField("Diameter of the holes in the grid", default = 4.0, places = 2)
    holeDepth      = DecimalField("Depth of the holes in the grid", default = 5.0, places = 2)
    holeKeepoutDiameter = DecimalField("Diameter of the keepout area around the holes", default = 4.0, places = 2)
    magnetHoleDiameter = DecimalField("Diameter of the magnet-holes", default = 6.5, places = 2)
    addRemovalHoles = BooleanField("Add extra offset holes to ease removal of magnets", default="False")
    addStackingLip = BooleanField("Add a stacking lip", default="True")
    addMagnetHoles = BooleanField("Add holes for magnets", default="True")
    addScrewHoles  = BooleanField("Add holes for screws", default="True")
    submit         = SubmitField('Generate STL', id=id, name=id)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def get_rows(self):
        return [
            [self.numHolesX, self.numHolesY, self.sizeUnitsZ],
            [self.holeShape, self.holeDiameter, self.holeDepth],
            [self.addStackingLip, self.addMagnetHoles, self.addScrewHoles],
            [self.submit]
        ]
    
    def get_title(self):
        return "Holey bin"
    
    def get_description(self):
        return "Generate a solid bin with a grid of holes. Specify a shape (circle, hexagon etc), how many holes you need in both directions and a keepout area and this will generate a bin of the minimum required size. Useful for things like screw-bit or battery holder bins"
