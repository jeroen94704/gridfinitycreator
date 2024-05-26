import cadquery as cqREMOVABLE_
from cadquery import exporters
from grid_constants import *

class Generator:
    def __init__(self, settings, grid) -> None:
        self.settings = settings
        self.grid = grid
        # Precalculate both before and after validation to process settings that changes
        self.precalculate()
        self.validate_settings()
        self.precalculate()

    def precalculate(self):
        """Precalculate a number of useful derived values used in construction"""
        self.brickSizeX = self.settings.sizeUnitsX * self.grid.GRID_UNIT_SIZE_X_MM - self.grid.BRICK_SIZE_TOLERANCE_MM 
        self.brickSizeY = self.settings.sizeUnitsY * self.grid.GRID_UNIT_SIZE_Y_MM - self.grid.BRICK_SIZE_TOLERANCE_MM
        self.brickSizeZ = self.settings.sizeUnitsZ*self.grid.HEIGHT_UNITSIZE_MM
        self.internalSizeX = self.brickSizeX-2*self.grid.WALL_THICKNESS
        self.internalSizeY = self.brickSizeY-2*self.grid.WALL_THICKNESS
        self.compartmentSizeZ = (self.settings.sizeUnitsZ-1)*self.grid.HEIGHT_UNITSIZE_MM

    def unit_base(self, basePlane):
        """Construct a 1x1 GridFinity unit base on the provided workplane"""
        
        # The elements are constructed "centered" because that makes life easier. 
        baseBottom = basePlane.box(self.grid.BASE_BOTTOM_SIZE_X, self.grid.BASE_BOTTOM_SIZE_Y, self.grid.BASE_BOTTOM_THICKNESS, combine=False)
        baseBottom = baseBottom.edges("|Z").fillet(self.grid.BASE_BOTTOM_FILLET_RADIUS)
        baseBottom = baseBottom.faces("<Z").chamfer(self.grid.BASE_BOTTOM_CHAMFER_SIZE)
        
        baseTop = baseBottom.faces(">Z").workplane()
        baseTop = baseTop.box(self.grid.BRICK_UNIT_SIZE_X, self.grid.BRICK_UNIT_SIZE_Y, self.grid.BASE_TOP_THICKNESS, centered=(True, True, False), combine=False)
        baseTop = baseTop.edges("|Z").fillet(self.grid.BASE_TOP_FILLET_RADIUS)
        baseTop = baseTop.faces("<Z").chamfer(self.grid.BASE_TOP_CHAMFER_SIZE)
        
        result = baseTop | baseBottom
        
        if self.settings.addMagnetHoles:
            result = result.faces("<Z").workplane()
            result = result.pushPoints([(self.grid.HOLE_OFFSET_X, self.grid.HOLE_OFFSET_Y),
                                                (-self.grid.HOLE_OFFSET_X, self.grid.HOLE_OFFSET_Y),
                                                (self.grid.HOLE_OFFSET_X, -self.grid.HOLE_OFFSET_Y),
                                                (-self.grid.HOLE_OFFSET_X, -self.grid.HOLE_OFFSET_Y)])
            result = result.hole(self.grid.DEFAULT_MAGNET_HOLE_DIAMETER, self.grid.DEFAULT_MAGNET_HOLE_DEPTH)

        if self.settings.addScrewHoles:
            result = result.faces("<Z").workplane()
            result = result.pushPoints([(self.grid.HOLE_OFFSET_X, self.grid.HOLE_OFFSET_Y),
                                        (-self.grid.HOLE_OFFSET_X, self.grid.HOLE_OFFSET_Y),
                                        (self.grid.HOLE_OFFSET_X, -self.grid.HOLE_OFFSET_Y),
                                        (-self.grid.HOLE_OFFSET_X, -self.grid.HOLE_OFFSET_Y)])
            result = result.hole(self.grid.SCREW_HOLE_DIAMETER, self.grid.SCREW_HOLE_DEPTH)
            
        # Translate the result because it is now centered around the origin, which is inconvenient for subsequent steps
        result = result.translate((self.grid.BRICK_UNIT_SIZE_X/2, self.grid.BRICK_UNIT_SIZE_Y/2, self.grid.BASE_BOTTOM_THICKNESS/2))
                
        return result

    def grid_base(self, basePlane):
        """Construct a base of WidthxLength grid units"""
        
        result = basePlane.workplane()
        
        for x in range(self.settings.sizeUnitsX):
            for y in range(self.settings.sizeUnitsY):
                result.add(self.unit_base(basePlane).translate((x*self.grid.GRID_UNIT_SIZE_X_MM, y*self.grid.GRID_UNIT_SIZE_Y_MM, 0)))
        
        return result

    def brick_floor(self, basePlane):
        """Create a floor covering all unit bases"""

        floor = basePlane.box(self.brickSizeX, self.brickSizeY, self.grid.FLOOR_THICKNESS, centered = False, combine = False)
        
        floor = floor.edges("|Z").fillet(self.grid.CORNER_FILLET_RADIUS)

        return floor

    def outer_wall(self, basePlane):
        """Create the outer wall of the bin"""

        sizeZ = self.compartmentSizeZ

        if self.settings.addStackingLip:
            sizeZ = sizeZ + self.grid.STACKING_LIP_HEIGHT

        wall = basePlane.box(self.brickSizeX, self.brickSizeY, sizeZ, centered=False, combine = False)
        
        thickness = self.grid.WALL_THICKNESS
        result = wall.edges("|Z").fillet(self.grid.CORNER_FILLET_RADIUS)
        
        if self.settings.addStackingLip:
                cutout = (
                    wall.faces(">Z").workplane().center(thickness, thickness)
                    .box(self.internalSizeX, self.internalSizeY, self.grid.STACKING_LIP_HEIGHT, centered=False, combine = False)
                    .translate((0,0,-self.grid.STACKING_LIP_HEIGHT))
                        )

                # If the walls are thicker than the outside radius of the corners, skip the fillet
                if thickness < self.grid.CORNER_FILLET_RADIUS:
                    cutout = cutout.edges("|Z").fillet(self.grid.CORNER_FILLET_RADIUS-thickness)

                result = result - cutout

                result = result.edges(
                            cq.selectors.NearestToPointSelector((self.brickSizeX/2, self.brickSizeY/2, sizeZ*2))
                        ).chamfer(thickness - self.grid.CHAMFER_EPSILON)
            
        return result

    def validate_settings(self):
        """Do some sanity checking on the settings to prevent impossible or unreasonable results"""

        # Cap the size in grid-units to avoid thrashing the server
        self.settings.sizeUnitsX = min(self.settings.sizeUnitsX, self.grid.MAX_GRID_UNITS)
        self.settings.sizeUnitsY = min(self.settings.sizeUnitsY, self.grid.MAX_GRID_UNITS)
        self.settings.sizeUnitsZ = min(self.settings.sizeUnitsZ, self.grid.MAX_HEIGHT_UNITS)

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


