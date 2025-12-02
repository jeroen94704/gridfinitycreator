import cadquery as cq
from cadquery import exporters
from grid_constants import *
import time
import logging

logger = logging.getLogger('LBG')

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
        self.compartmentSizeZ = (self.settings.sizeUnitsZ-1)*self.grid.HEIGHT_UNITSIZE_MM # This is the height in units minus the thickness of the base

    def unit_base(self, basePlane):
        """Construct a 1x1 GridFinity unit base on the provided workplane"""

        x_offs = self.grid.BRICK_UNIT_SIZE_X/2-3.5
        frame_pts = [(0+x_offs,0),       (0+x_offs, 3.15), 
                    (1.6+x_offs, 4.75), (3.5+x_offs, 4.75),
                    (1.35+x_offs, 2.6), (1.35+x_offs, 0.8),
                    (0.55+x_offs, 0) 
                    ]

        path = basePlane.rect(self.grid.BRICK_UNIT_SIZE_X, self.grid.BRICK_UNIT_SIZE_X).val()
        path = path.fillet2D(self.grid.BASE_TOP_FILLET_RADIUS, path.Vertices())

        baseUnit = (
            cq.Workplane("XZ")
            .polyline(frame_pts)
            .close()
            .sweep(path)
            )

        floor = basePlane.box(self.grid.BRICK_UNIT_SIZE_X-6.7,self.grid.BRICK_UNIT_SIZE_X-6.7,self.settings.wallThickness).translate((0,0,self.settings.wallThickness/2))
        baseUnit = baseUnit.add(floor)
        baseUnit = baseUnit.combine()

        # Translate the result because it is now centered around the origin, which is inconvenient for subsequent steps
        baseUnit = baseUnit.translate((self.grid.BRICK_UNIT_SIZE_X/2, self.grid.BRICK_UNIT_SIZE_Y/2))

        return baseUnit

    def grid_base(self, basePlane):
        """Construct a base of WidthxLength grid units"""
        
        result = basePlane

        baseUnit = self.unit_base(basePlane)

        for x in range(self.settings.sizeUnitsX):
            for y in range(self.settings.sizeUnitsY):
                result.add(baseUnit.translate((x*self.grid.GRID_UNIT_SIZE_X_MM, y*self.grid.GRID_UNIT_SIZE_Y_MM, 0)))

        return result

    def brick_floor(self, basePlane):
        """Create a floor covering all unit bases"""

        # Create the solid floor
        floor = basePlane.box(self.grid.GRID_UNIT_SIZE_X_MM, self.grid.GRID_UNIT_SIZE_X_MM, self.grid.LIGHT_FLOOR_THICKNESS, centered = True, combine = False)

        # Create the cutout and remove it for each base unit
        cutoutSizeX = self.grid.BRICK_UNIT_SIZE_X-2*self.grid.WALL_THICKNESS
        cutoutSizeY = self.grid.BRICK_UNIT_SIZE_Y-2*self.grid.WALL_THICKNESS
        cutout = basePlane.box(cutoutSizeX, cutoutSizeY,3, centered = True, combine=False)
        cutout = cutout.edges("|Z")
        cutout = cutout.fillet(self.grid.CORNER_FILLET_RADIUS-self.grid.WALL_THICKNESS)
        
        floor = floor - cutout

        # Chamfer the sharp edges 
        dx = self.grid.BRICK_UNIT_SIZE_X/2
        dy = self.grid.BRICK_UNIT_SIZE_Y/2
        s = cq.selectors.BoxSelector((0,0,5), (dx,dy,6))
        floor = floor.edges(s).chamfer(self.grid.LIGHT_FLOOR_THICKNESS-self.grid.CHAMFER_EPSILON)
        floor = floor.translate((self.grid.BRICK_UNIT_SIZE_X/2, self.grid.BRICK_UNIT_SIZE_Y/2, self.grid.LIGHT_FLOOR_THICKNESS/2))

        result = basePlane
        for x in range(self.settings.sizeUnitsX):
            for y in range(self.settings.sizeUnitsY):
                result.add(floor.translate((x*self.grid.GRID_UNIT_SIZE_X_MM, y*self.grid.GRID_UNIT_SIZE_Y_MM, 0)))
        
        result = result.combine()
        
        # Create 
        plane = cq.Workplane("XY")
        cutout = plane.box(self.brickSizeX, self.brickSizeY, 1.9, centered=True, combine = False)
        cutout = cutout.edges("|Z").fillet(self.grid.CORNER_FILLET_RADIUS)
        shrink_box = plane.box(self.brickSizeX+5, self.brickSizeY+5, 1.9, centered = True, combine = False)
        shrink_box = shrink_box - cutout
        shrink_box = shrink_box.translate((self.brickSizeX/2, self.brickSizeY/2, 5.25))

        result = result - shrink_box
    
        return result

    def outer_wall(self, basePlane):
        """Create the outer wall of the bin"""
        
        plane = basePlane.workplane()
        sizeZ = self.compartmentSizeZ + self.grid.FLOOR_THICKNESS

        if self.settings.addStackingLip:
            sizeZ = sizeZ + self.grid.STACKING_LIP_HEIGHT

        wall = plane.box(self.brickSizeX, self.brickSizeY, sizeZ, combine = False)
        
        thickness = self.grid.WALL_THICKNESS
        wall = wall.edges("|Z").fillet(self.grid.CORNER_FILLET_RADIUS)

        cutout = (
                    plane.box(self.brickSizeX-2*thickness, self.brickSizeY-2*thickness, sizeZ, combine = False)
                )

        # If the walls are thicker than the outside radius of the corners, skip the fillet
        if thickness < self.grid.CORNER_FILLET_RADIUS:
            cutout = cutout.edges("|Z").fillet(self.grid.CORNER_FILLET_RADIUS-thickness)
        
        result = wall-cutout

        if self.settings.addStackingLip:
            result = result.edges(
                        cq.selectors.NearestToPointSelector((0, 0, sizeZ*2))
                    ).chamfer(thickness-self.grid.CHAMFER_EPSILON)
        
        result = result.translate((self.brickSizeX/2,self.brickSizeY/2,sizeZ/2-self.grid.LIGHT_FLOOR_THICKNESS))
            
        return result
    
    def label_tab(self, basePlane):
        """Construct the pickup/label tab"""

        result = basePlane

        startX = self.grid.WALL_THICKNESS
        
        # Limit the height of the label ridge to avoid it being taller than the compartment
        labelRidgeHeight = min(self.compartmentSizeZ+2.25, self.settings.labelRidgeWidth-self.grid.CHAMFER_EPSILON)

        # Create the label tab profile and extrude it
        result.add(
            basePlane.sketch()
            .segment((startX,self.brickSizeZ-labelRidgeHeight),(startX,self.brickSizeZ))
            .segment((startX+self.settings.labelRidgeWidth,self.brickSizeZ))
            .close()
            .reset()
            .assemble()
            .finalize()
            .extrude(self.internalSizeX)
            .edges(">Y").fillet(0.5)
            )

        return result
        
    def validate_settings(self):
        """Do some sanity checking on the settings to prevent impossible or unreasonable results"""

        # Cap the size in grid-units to avoid thrashing the server
        self.settings.sizeUnitsX = min(self.settings.sizeUnitsX, self.grid.MAX_GRID_UNITS)
        self.settings.sizeUnitsY = min(self.settings.sizeUnitsY, self.grid.MAX_GRID_UNITS)
        self.settings.sizeUnitsZ = min(self.settings.sizeUnitsZ, self.grid.MAX_HEIGHT_UNITS)

        # Limit the number of compartment in each direction
        self.settings.compartmentsX = min(self.settings.compartmentsX, self.settings.sizeUnitsX*self.grid.MAX_COMPARTMENTS_PER_GRID_UNIT)
        self.settings.compartmentsY = min(self.settings.compartmentsY, self.settings.sizeUnitsY*self.grid.MAX_COMPARTMENTS_PER_GRID_UNIT)

        # Ensure the labeltab is smaller than half the compartmentsize, or it will close off a row
        self.settings.labelRidgeWidth = min(self.compartmentSizeY/2, self.settings.labelRidgeWidth)

    def generate_model(self):
        # Add the base of Gridfinity profiles
        result = self.grid_base(cq.Workplane("XY"))

        # Continue from the top of the base
        plane = result.faces(">Z").workplane()

        # Add the floor of the bin
        result.add(self.brick_floor(plane))

        # Add the outer walls
        plane = result.faces(">Z").workplane()
        result.add(self.outer_wall(plane))

        # Add the grabbing/label tab
        if self.settings.addLabelRidge:
            plane = cq.Workplane("YZ").workplane(offset=self.grid.WALL_THICKNESS)
            result.add(self.label_tab(plane))      

        # Combine everything together
        result = result.combine()

        return result

    def generate_stl(self, filename):
        model = self.generate_model()
        exporters.export(model, filename)

