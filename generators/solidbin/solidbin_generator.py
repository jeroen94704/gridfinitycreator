import cadquery as cq
from cadquery import exporters
from grid_constants import *

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
        self.brickSizeX = self.settings.sizeUnitsX * self.grid.GRID_UNIT_SIZE_X_MM - self.grid.BRICK_SIZE_TOLERANCE_MM 
        self.brickSizeY = self.settings.sizeUnitsY * self.grid.GRID_UNIT_SIZE_Y_MM - self.grid.BRICK_SIZE_TOLERANCE_MM
        self.brickSizeZ = self.settings.sizeUnitsZ*self.grid.HEIGHT_UNITSIZE_MM
        self.internalSizeX = self.brickSizeX-2*self.grid.WALL_THICKNESS
        self.internalSizeY = self.brickSizeY-2*self.grid.WALL_THICKNESS
        self.compartmentSizeZ = (self.settings.sizeUnitsZ-1)*self.grid.HEIGHT_UNITSIZE_MM

    def outer_wall(self, basePlane):
        """Create the outer wall of the bin"""

        # Allow creation of a 1-unit height bin (just the base)
        if self.compartmentSizeZ == 0:
            return

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
        
        result = bin_base(plane, self.settings, self.grid)

        plane = result.faces(">Z").workplane()

        # Add the outer wall
        result.add(self.outer_wall(plane))
        
        # Combine everything together
        result = result.combine(clean=True)

        return result

    def generate_stl(self, filename):
        model = self.generate_model()
        exporters.export(model, filename)


