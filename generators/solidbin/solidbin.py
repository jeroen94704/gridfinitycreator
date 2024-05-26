import cadquery as cq
from cadquery import exporters
from dataclasses import dataclass
from grid_constants import *

# Generator inputs
@dataclass
class Settings:
    sizeUnitsX: int = 3 # Width (X) of the brick in grid units
    sizeUnitsY: int = 1  # Length (Y) of the brick in grid units
    sizeUnitsZ: int = 3  # Height (Z) of the brick in height-units

    addStackingLip: bool = True  # Add a stacking lip (True) or not (False)?
    addMagnetHoles: bool = True  # Add holes for magnets
    addScrewHoles:  bool = True  # Add holes for screws

class SolidbinGenerator:
    def __init__(self, settings) -> None:
        self.settings = settings

        # Precalculate both before and after validation to process settings that changes
        self.precalculate()
        self.validate_settings()
        self.precalculate()

    def precalculate(self):
        """Precalculate a number of useful derived values used in construction"""
        self.brickSizeX = self.settings.sizeUnitsX * GRID_UNIT_SIZE_X_MM - BRICK_SIZE_TOLERANCE_MM 
        self.brickSizeY = self.settings.sizeUnitsY * GRID_UNIT_SIZE_Y_MM - BRICK_SIZE_TOLERANCE_MM
        self.brickSizeZ = self.settings.sizeUnitsZ*HEIGHT_UNITSIZE_MM
        self.internalSizeX = self.brickSizeX-2*WALL_THICKNESS
        self.internalSizeY = self.brickSizeY-2*WALL_THICKNESS
        self.compartmentSizeZ = (self.settings.sizeUnitsZ-1)*HEIGHT_UNITSIZE_MM

    def unit_base(self, basePlane):
        """Construct a 1x1 GridFinity unit base on the provided workplane"""
        
        # The elements are constructed "centered" because that makes life easier. 
        baseBottom = basePlane.box(BASE_BOTTOM_SIZE_X, BASE_BOTTOM_SIZE_Y, BASE_BOTTOM_THICKNESS, combine=False)
        baseBottom = baseBottom.edges("|Z").fillet(BASE_BOTTOM_FILLET_RADIUS)
        baseBottom = baseBottom.faces("<Z").chamfer(BASE_BOTTOM_CHAMFER_SIZE)
        
        baseTop = baseBottom.faces(">Z").workplane()
        baseTop = baseTop.box(BRICK_UNIT_SIZE_X, BRICK_UNIT_SIZE_Y, BASE_TOP_THICKNESS, centered=(True, True, False), combine=False)
        baseTop = baseTop.edges("|Z").fillet(BASE_TOP_FILLET_RADIUS)
        baseTop = baseTop.faces("<Z").chamfer(BASE_TOP_CHAMFER_SIZE)
        
        result = baseTop | baseBottom
        
        if self.settings.addMagnetHoles:
            result = result.faces("<Z").workplane()
            result = result.pushPoints([(HOLE_OFFSET_X, HOLE_OFFSET_Y),
                                                (-HOLE_OFFSET_X, HOLE_OFFSET_Y),
                                                (HOLE_OFFSET_X, -HOLE_OFFSET_Y),
                                                (-HOLE_OFFSET_X, -HOLE_OFFSET_Y)])
            result = result.hole(DEFAULT_MAGNET_HOLE_DIAMETER, DEFAULT_MAGNET_HOLE_DEPTH)

        if self.settings.addScrewHoles:
            result = result.faces("<Z").workplane()
            result = result.pushPoints([(HOLE_OFFSET_X, HOLE_OFFSET_Y),
                                        (-HOLE_OFFSET_X, HOLE_OFFSET_Y),
                                        (HOLE_OFFSET_X, -HOLE_OFFSET_Y),
                                        (-HOLE_OFFSET_X, -HOLE_OFFSET_Y)])
            result = result.hole(SCREW_HOLE_DIAMETER, SCREW_HOLE_DEPTH)
            
        # Translate the result because it is now centered around the origin, which is inconvenient for subsequent steps
        result = result.translate((BRICK_UNIT_SIZE_X/2, BRICK_UNIT_SIZE_Y/2, BASE_BOTTOM_THICKNESS/2))
                
        return result

    def grid_base(self, basePlane):
        """Construct a base of WidthxLength grid units"""
        
        result = basePlane.workplane()
        
        for x in range(self.settings.sizeUnitsX):
            for y in range(self.settings.sizeUnitsY):
                result.add(self.unit_base(basePlane).translate((x*GRID_UNIT_SIZE_X_MM, y*GRID_UNIT_SIZE_Y_MM, 0)))
        
        return result

    def brick_floor(self, basePlane):
        """Create a floor covering all unit bases"""

        floor = basePlane.box(self.brickSizeX, self.brickSizeY, FLOOR_THICKNESS, centered = False, combine = False)
        
        floor = floor.edges("|Z").fillet(CORNER_FILLET_RADIUS)

        return floor

    def outer_wall(self, basePlane):
        """Create the outer wall of the bin"""

        sizeZ = self.compartmentSizeZ

        if self.settings.addStackingLip:
            sizeZ = sizeZ + STACKING_LIP_HEIGHT

        wall = basePlane.box(self.brickSizeX, self.brickSizeY, sizeZ, centered=False, combine = False)
        
        thickness = WALL_THICKNESS
        result = wall.edges("|Z").fillet(CORNER_FILLET_RADIUS)
        
        if self.settings.addStackingLip:
                cutout = (
                    wall.faces(">Z").workplane().center(thickness, thickness)
                    .box(self.internalSizeX, self.internalSizeY, STACKING_LIP_HEIGHT, centered=False, combine = False)
                    .translate((0,0,-STACKING_LIP_HEIGHT))
                        )

                # If the walls are thicker than the outside radius of the corners, skip the fillet
                if thickness < CORNER_FILLET_RADIUS:
                    cutout = cutout.edges("|Z").fillet(CORNER_FILLET_RADIUS-thickness)

                result = result - cutout

                result = result.edges(
                            cq.selectors.NearestToPointSelector((self.brickSizeX/2, self.brickSizeY/2, sizeZ*2))
                        ).chamfer(thickness-CHAMFER_EPSILON)
            
        return result

    def validate_settings(self):
        """Do some sanity checking on the settings to prevent impossible or unreasonable results"""

        # Cap the size in grid-units to avoid thrashing the server
        self.settings.sizeUnitsX = min(self.settings.sizeUnitsX, MAX_GRID_UNITS)
        self.settings.sizeUnitsY = min(self.settings.sizeUnitsY, MAX_GRID_UNITS)
        self.settings.sizeUnitsZ = min(self.settings.sizeUnitsZ, MAX_HEIGHT_UNITS)

    def generate_model(self):
        plane = cq.Workplane("XY")
        result = plane.workplane()

        # Add the base of Gridfinity profiles
        result.add(self.grid_base(plane))

        # Continue from the top of the base
        plane = result.faces(">Z").workplane()

        # Add the floor of the bin
        result.add(self.brick_floor(plane))

        # Continue from the top of the floor
        plane = result.faces(">Z").workplane()

        # Add the outer wall
        result.add(self.outer_wall(plane))
        
        # Combine everything together
        result = result.combine(clean=True)

        return result

    def generate_stl(self, filename):
        model = self.generate_model()
        exporters.export(model, filename)

    def render_model(self):
        model = self.generate_model()
        show_object(model)

