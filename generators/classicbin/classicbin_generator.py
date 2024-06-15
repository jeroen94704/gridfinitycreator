import cadquery as cq
from cadquery import exporters
from dataclasses import dataclass
from grid_constants import *
import logging

from generators.common.bin_base import bin_base

logger = logging.getLogger('CBG')

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
        self.compartmentSizeX = self.internalSizeX / self.settings.compartmentsX
        self.compartmentSizeY = self.internalSizeY / self.settings.compartmentsY
        self.compartmentSizeZ = (self.settings.sizeUnitsZ-1)*self.grid.HEIGHT_UNITSIZE_MM

    def outer_wall(self, basePlane):
        """Create the outer wall of the bin"""

        sizeZ = self.compartmentSizeZ

        if self.settings.addStackingLip:
            sizeZ = sizeZ + self.grid.STACKING_LIP_HEIGHT

        wall = basePlane.box(self.brickSizeX, self.brickSizeY, sizeZ, centered=False, combine = False)
        
        thickness = self.grid.WALL_THICKNESS
        wall = wall.edges("|Z").fillet(self.grid.CORNER_FILLET_RADIUS)

        cutout = (
                    basePlane.center(thickness, thickness)
                    .box(self.internalSizeX, self.internalSizeY, sizeZ, centered=False, combine = False)
                )

        # If the walls are thicker than the outside radius of the corners, skip the fillet
        if thickness < self.grid.CORNER_FILLET_RADIUS:
            cutout = cutout.edges("|Z").fillet(self.grid.CORNER_FILLET_RADIUS-thickness)
        
        result = wall-cutout
        
        if self.settings.addStackingLip:
            result = result.edges(
                        cq.selectors.NearestToPointSelector((self.brickSizeX/2, self.brickSizeY/2, sizeZ*2))
                    ).chamfer(thickness-self.grid.CHAMFER_EPSILON)
            
        return result

    def divider_walls(self, basePlane):
        """Create a regularly spaced grid of internal divider walls"""
        
        resultPlane = basePlane.center(self.grid.WALL_THICKNESS, self.grid.WALL_THICKNESS)
        result = resultPlane.workplane()
        
        if(self.settings.compartmentsX > 1):
            for x in range(self.settings.compartmentsX-1):
                result.add(resultPlane.box(self.settings.dividerThickness,self.internalSizeY, self.compartmentSizeZ,
                        centered=(True, False,False), combine=False).translate(((x+1)*self.compartmentSizeX, 0, 0)))

        if(self.settings.compartmentsY > 1):
            for y in range(self.settings.compartmentsY-1):
                result.add(resultPlane.box(self.internalSizeX,self.settings.dividerThickness,self.compartmentSizeZ, 
                        centered=(False, True, False), combine=False).translate((0, (y+1)*self.compartmentSizeY, 0)))

        # Combining fails when there is no overlap between the objects, which is the case when there are 0 dividers in one direction
        if(self.settings.compartmentsX > 1 and self.settings.compartmentsY > 1):
            result = result.combine()

        return result

    def label_tab(self, basePlane):
        """Construct the pickip/label tab"""

        result = basePlane.workplane()

        numRidges = self.settings.compartmentsY if self.settings.multiLabel else 1

        for x in range(numRidges):
            startX = self.grid.WALL_THICKNESS + x*self.compartmentSizeY
            result.add(
                basePlane.sketch()
                .segment((startX,self.brickSizeZ-self.settings.labelRidgeWidth),(startX,self.brickSizeZ))
                .segment((startX+self.settings.labelRidgeWidth,self.brickSizeZ))
                .close()
                .reset()
                .assemble()
                .finalize()
                .extrude(self.internalSizeX)
                )

        result = result.edges(">Y").fillet(0.5)

        return result

    def grab_curve(self, basePlane):

        result = basePlane.workplane()

        # To ensure the curve fits, take the smallest of: The height of the divider walls, the length of a compartment, half the brick unit-size (Y-direction)
        radius = min((self.settings.sizeUnitsZ-1) * self.grid.HEIGHT_UNITSIZE_MM, self.compartmentSizeY, self.grid.BRICK_UNIT_SIZE_Y/2)
        
        for y in range(self.settings.compartmentsY):
            startX = self.grid.WALL_THICKNESS + (y+1)*self.compartmentSizeY
            result.add(
                basePlane.sketch()
                .segment((startX,self.grid.HEIGHT_UNITSIZE_MM+radius),(startX,self.grid.HEIGHT_UNITSIZE_MM))
                .segment((startX-radius,self.grid.HEIGHT_UNITSIZE_MM))
                .arc((startX-radius,self.grid.HEIGHT_UNITSIZE_MM+radius),radius,270,90)
                .assemble()
                .finalize()
                .extrude(self.internalSizeX)
                )

        return result

    def validate_settings(self):
        """Do some sanity checking on the settings to prevent impossible or unreasonable results"""

        # Cap the size in grid-units to avoid thrashing the server
        self.settings.sizeUnitsX = min(self.settings.sizeUnitsX, self.grid.MAX_GRID_UNITS)
        self.settings.sizeUnitsY = min(self.settings.sizeUnitsY, self.grid.MAX_GRID_UNITS)
        self.settings.sizeUnitsZ = min(self.settings.sizeUnitsZ, self.grid.MAX_HEIGHT_UNITS)
        self.settings.sizeUnitsZ = max(self.settings.sizeUnitsZ, self.grid.MIN_HEIGHT_UNITS)

        # Limit the number of compartment in each direction
        self.settings.compartmentsX = min(self.settings.compartmentsX, self.settings.sizeUnitsX*self.grid.MAX_COMPARTMENTS_PER_GRID_UNIT)
        self.settings.compartmentsY = min(self.settings.compartmentsY, self.settings.sizeUnitsY*self.grid.MAX_COMPARTMENTS_PER_GRID_UNIT)

        # Ensure the labeltab is smaller than half the compartmentsize, or it will close off a row
        self.settings.labelRidgeWidth = min(self.compartmentSizeY/2, self.settings.labelRidgeWidth)

        # Ensure the label tab is not deeper than the interior height of the bin or it will stick out 
        self.settings.labelRidgeWidth = min(self.compartmentSizeZ, self.settings.labelRidgeWidth)

    def generate_model(self):
        plane = cq.Workplane("XY")

        # First create the base
        result = bin_base(plane, self.settings, self.grid)

        # Continue at the top of the base
        plane = result.faces(">Z").workplane()

        # Add the outer walls
        result.add(self.outer_wall(plane))
        
        # Add the divider walls
        result.add(self.divider_walls(plane))

        # Continue from the left-most outside face of the brick
        plane = cq.Workplane("YZ").workplane(offset=self.grid.WALL_THICKNESS)

        # Add the grabbing/label tab
        if self.settings.addLabelRidge:
            result.add(self.label_tab(plane))

        # Add the curve
        if self.settings.addGrabCurve:
            result.add(self.grab_curve(plane))

        # Combine everything together
        result = result.combine(clean=True)

        return result

    def generate_stl(self, filename):
        model = self.generate_model()
        logger.debug("Saved classicbin to {0}".format(filename))
        exporters.export(model, filename)


