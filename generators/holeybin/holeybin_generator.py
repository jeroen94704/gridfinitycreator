import cadquery as cq
from cadquery import exporters
from grid_constants import *
import math
from holeybin_settings import HoleShape

from generators.common.bin_base import bin_base

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
        self.settings.sizeUnitsX = math.ceil((self.settings.numHolesX * self.settings.keepoutDiameter + 2*self.grid.WALL_THICKNESS) / (self.grid.GRID_UNIT_SIZE_X_MM - self.grid.BRICK_SIZE_TOLERANCE_MM))
        self.settings.sizeUnitsY = math.ceil((self.settings.numHolesY * self.settings.keepoutDiameter + 2*self.grid.WALL_THICKNESS) / (self.grid.GRID_UNIT_SIZE_Y_MM - self.grid.BRICK_SIZE_TOLERANCE_MM))
        self.settings.sizeUnitsZ = 1 + math.ceil(self.settings.holeDepth / self.grid.HEIGHT_UNITSIZE_MM)

        self.brickSizeX = self.settings.sizeUnitsX * self.grid.GRID_UNIT_SIZE_X_MM - self.grid.BRICK_SIZE_TOLERANCE_MM 
        self.brickSizeY = self.settings.sizeUnitsY * self.grid.GRID_UNIT_SIZE_Y_MM - self.grid.BRICK_SIZE_TOLERANCE_MM
        self.brickSizeZ = self.settings.sizeUnitsZ*self.grid.HEIGHT_UNITSIZE_MM
        self.internalSizeX = self.brickSizeX-2*self.grid.WALL_THICKNESS
        self.internalSizeY = self.brickSizeY-2*self.grid.WALL_THICKNESS
        self.compartmentSizeZ = (self.settings.sizeUnitsZ-1)*self.grid.HEIGHT_UNITSIZE_MM

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
        
    def holey_grid(self, basePlane):

        # Calculate step-size based on actual internal size to spread the holes evenly across the bin
        x_step = self.internalSizeX / self.settings.numHolesX
        y_step = self.internalSizeY / self.settings.numHolesY
        
        # Move the entire hole-grid so it is centered on the bin
        offset_x = (self.brickSizeX - self.internalSizeX) / 2 + x_step / 2
        offset_y = (self.brickSizeY - self.internalSizeY) / 2 + y_step / 2

        # Create the grid of points where the holes go
        hole_points = []
        for x in range(self.settings.numHolesX):
            for y in range(self.settings.numHolesY):
                hole_points.append((x*x_step + offset_x, y*y_step + offset_y))
                
        # Extrude the holes based on the shape setting
        if self.settings.holeShape == "HEXAGON":
            result = basePlane.pushPoints(hole_points).polygon(6, self.settings.holeSize).extrude(-self.settings.holeDepth, combine="cut")
        elif self.settings.holeShape == "SQUARE":
            result = basePlane.pushPoints(hole_points).rect(self.settings.holeSize, self.settings.holeSize).extrude(-self.settings.holeDepth, combine="cut")
        else: # By default, use HoleShape.CIRCLE
            result = basePlane.pushPoints(hole_points).hole(self.settings.holeSize, self.settings.holeDepth)
        
        return result

    def validate_settings(self):
        """Do some sanity checking on the settings to prevent impossible or unreasonable results"""

        # Cap the size in grid-units to avoid thrashing the server
        self.settings.sizeUnitsX = min(self.settings.sizeUnitsX, self.grid.MAX_GRID_UNITS)
        self.settings.sizeUnitsY = min(self.settings.sizeUnitsY, self.grid.MAX_GRID_UNITS)
        self.settings.sizeUnitsZ = min(self.settings.sizeUnitsZ, self.grid.MAX_HEIGHT_UNITS)

    def generate_model(self):
        plane = cq.Workplane("XY")

        # First create the base
        result = bin_base(plane, self.settings, self.grid)

        # Continue at the top of the base
        plane = result.faces(">Z").workplane()

        # Add the outer wall
        result.add(self.outer_wall(plane))
        
        # Continue from the top of the bin
        plane = result.faces(">Z").workplane()

        # Create the hole-grid in the same plane as the previous operation
        result = self.holey_grid(plane)

        # Add the stacking lip
        result.add(self.stacking_lip(plane))

        # Combine everything together
        result = result.combine(clean=True)

        return result

    def generate_stl(self, filename):
        model = self.generate_model()
        exporters.export(model, filename)


