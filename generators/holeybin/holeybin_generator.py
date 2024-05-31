import cadquery as cq
from cadquery import exporters
from grid_constants import *
import math

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
        self.sizeUnitsX = math.ceil((self.settings.numHolesX * self.settings.keepoutDiameter + 2*self.grid.WALL_THICKNESS) / (self.grid.GRID_UNIT_SIZE_X_MM - self.grid.BRICK_SIZE_TOLERANCE_MM))
        self.sizeUnitsY = math.ceil((self.settings.numHolesY * self.settings.keepoutDiameter + 2*self.grid.WALL_THICKNESS) / (self.grid.GRID_UNIT_SIZE_Y_MM - self.grid.BRICK_SIZE_TOLERANCE_MM))
        self.sizeUnitsZ = 1 + math.ceil(self.settings.holeDepth / self.grid.HEIGHT_UNITSIZE_MM)

        self.brickSizeX = self.sizeUnitsX * self.grid.GRID_UNIT_SIZE_X_MM - self.grid.BRICK_SIZE_TOLERANCE_MM 
        self.brickSizeY = self.sizeUnitsY * self.grid.GRID_UNIT_SIZE_Y_MM - self.grid.BRICK_SIZE_TOLERANCE_MM
        self.brickSizeZ = self.sizeUnitsZ*self.grid.HEIGHT_UNITSIZE_MM
        self.internalSizeX = self.brickSizeX-2*self.grid.WALL_THICKNESS
        self.internalSizeY = self.brickSizeY-2*self.grid.WALL_THICKNESS
        self.compartmentSizeZ = (self.sizeUnitsZ-1)*self.grid.HEIGHT_UNITSIZE_MM

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
        
        for x in range(self.sizeUnitsX):
            for y in range(self.sizeUnitsY):
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

        wall = basePlane.box(self.brickSizeX, self.brickSizeY, sizeZ, centered=False, combine = False)
        
        result = wall.edges("|Z").fillet(self.grid.CORNER_FILLET_RADIUS)
                   
        return result

    def stacking_lip(self, basePlane):
        if self.settings.addStackingLip:
            thickness = self.grid.WALL_THICKNESS

            # Increase the height of the block by the thickness of the stacking lip
            wall = basePlane.box(self.brickSizeX, self.brickSizeY, self.grid.STACKING_LIP_HEIGHT, centered=False, combine = False)      
            result = wall.edges("|Z").fillet(self.grid.CORNER_FILLET_RADIUS)

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
                        cq.selectors.NearestToPointSelector((self.brickSizeX/2, self.brickSizeY/2, (self.compartmentSizeZ+self.grid.STACKING_LIP_HEIGHT)*2))
                    ).chamfer(thickness - self.grid.CHAMFER_EPSILON)

            return result
        
    def holey_grid(self, body, basePlane):
        result = body
        for x in range(self.settings.numHolesX):
            for y in range(self.settings.numHolesY):
                result = result + (basePlane.box(self.settings.holeDiameter, self.settings.holeDiameter, self.settings.holeDepth).translate((x*self.settings.keepoutDiameter, y*self.settings.keepoutDiameter, -self.settings.holeDepth+0.1)))
        
        return result

    def validate_settings(self):
        """Do some sanity checking on the settings to prevent impossible or unreasonable results"""

        # Cap the size in grid-units to avoid thrashing the server
        self.sizeUnitsX = min(self.sizeUnitsX, self.grid.MAX_GRID_UNITS)
        self.sizeUnitsY = min(self.sizeUnitsY, self.grid.MAX_GRID_UNITS)
        self.sizeUnitsZ = min(self.sizeUnitsZ, self.grid.MAX_HEIGHT_UNITS)

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
        
        # Continue from the top of the bin
        plane = result.faces(">Z").workplane()

        # Add the stacking lip
        result.add(self.stacking_lip(plane))

        # Create the hole-grid in the same plane as the previous operation
        self.holey_grid(result, plane)

        # Combine everything together
        result = result.combine(clean=True)

        return result

    def generate_stl(self, filename):
        model = self.generate_model()
        exporters.export(model, filename)


