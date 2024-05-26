import cadquery as cq
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
        self.compartmentSizeX = self.internalSizeX / self.settings.compartmentsX
        self.compartmentSizeY = self.internalSizeY / self.settings.compartmentsY
        self.compartmentSizeZ = (self.settings.sizeUnitsZ-1)*self.grid.HEIGHT_UNITSIZE_MM

    def unit_base(self, basePlane):
        """Construct a 1x1 GridFinity unit base on the provided workplane"""

        plane = basePlane.workplane()

        profile = (cq.Workplane("XZ").moveTo(self.grid.BRICK_UNIT_SIZE_X/2,0).sketch()
                        .segment((0,0), (-2.15, -2.15))
                        .segment((-2.15, -3.95))
                        .segment((-2.95, -4.75))
                        .segment((-3.5, -4.75))
                        .segment((-3.5, -1.6))
                        .segment((-1.9, 0))
                        .close()
                        .assemble()
                        .finalize()
                        .wire()
                        )
        
        theBox = plane.box(self.grid.BRICK_UNIT_SIZE_X,self.grid.BRICK_UNIT_SIZE_Y,0.1).edges('|Z').fillet(self.grid.CORNER_FILLET_RADIUS).translate((0,0,-2))
        path = theBox.edges('>Z')
        path = path.wire(path.toPending())
        result = profile.sweep(path)
        
        d = 34.6
        s = cq.selectors.BoxSelector((-d/2,-d/2,-5.5), (d/2,d/2,-4.5))
        bottomOutline = cq.Wire.assembleEdges(result.edges(s).objects)
        bottom = basePlane.add(bottomOutline)
        bottom = bottom.wires().toPending().extrude(self.settings.wallThickness)
        
        result = result.add(bottom).combine()
        s = cq.selectors.BoxSelector((-d/2,-d/2,-3.2), (d/2,d/2,-3.3))
        result = result.edges(s).chamfer(0.25)
                
        # Translate the result because it is now centered around the origin, which is inconvenient for subsequent steps
        result = result.translate((self.grid.BRICK_UNIT_SIZE_X/2, self.grid.BRICK_UNIT_SIZE_Y/2, self.grid.BASE_BOTTOM_THICKNESS/2))
                
        return result

    def grid_base(self, basePlane):
        """Construct a base of WidthxLength grid units"""
        
        result = basePlane.workplane()
        
        baseUnit = self.unit_base(basePlane)
        for x in range(self.settings.sizeUnitsX):
            for y in range(self.settings.sizeUnitsY):
                result.add(baseUnit.translate((x*self.grid.GRID_UNIT_SIZE_X_MM, y*self.grid.GRID_UNIT_SIZE_Y_MM, 0)))
        
        return result

    def brick_floor(self, basePlane):
        """Create a floor covering all unit bases"""

        plane=basePlane.workplane()

        # Create the solid floor
        floor = basePlane.box(self.brickSizeX, self.brickSizeY, 0.9, centered = False, combine = False)
        floor = floor.edges("|Z").fillet(self.grid.CORNER_FILLET_RADIUS)

        # Create the cutout and remove it for each base unit
        cutoutSizeX = self.grid.BRICK_UNIT_SIZE_X-2*self.grid.WALL_THICKNESS
        cutoutSizeY = self.grid.BRICK_UNIT_SIZE_Y-2*self.grid.WALL_THICKNESS
        cutout = plane.box(cutoutSizeX, cutoutSizeY,3, combine=False)
        cutout = cutout.edges("|Z")
        cutout = cutout.fillet(self.grid.CORNER_FILLET_RADIUS-self.grid.WALL_THICKNESS)
        cutout = cutout.translate((self.grid.BRICK_UNIT_SIZE_X/2, self.grid.BRICK_UNIT_SIZE_Y/2, 0))
                                  
        for x in range(self.settings.sizeUnitsX):
            for y in range(self.settings.sizeUnitsY):
                floor = floor - cutout.translate((x*self.grid.GRID_UNIT_SIZE_X_MM, y*self.grid.GRID_UNIT_SIZE_Y_MM, 0))

        # Chanfer the sharp edges 
        dx = self.brickSizeX
        dy = self.brickSizeY
        s = cq.selectors.BoxSelector((0,0,2), (dx,dy,3))
        floor = floor.edges(s).chamfer(0.9-self.grid.CHAMFER_EPSILON)
        
        return floor

    def outer_wall(self, basePlane):
        """Create the outer wall of the bin"""

        plane=basePlane.workplane()
        
        sizeZ = self.compartmentSizeZ + self.grid.FLOOR_THICKNESS

        if self.settings.addStackingLip:
            sizeZ = sizeZ + self.grid.STACKING_LIP_HEIGHT

        wall = plane.box(self.brickSizeX, self.brickSizeY, sizeZ, centered=False, combine = False)
        
        thickness = self.grid.WALL_THICKNESS
        wall = wall.edges("|Z").fillet(self.grid.CORNER_FILLET_RADIUS)

        cutout = (
                    plane.center(thickness, thickness)
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
        plane = cq.Workplane("XY")
        result = plane.workplane()

        # Add the base of Gridfinity profiles
        result.add(self.grid_base(plane))

        # # Continue from the top of the base
        plane = result.faces(">Z").workplane()

        # Add the outer walls
        result.add(self.outer_wall(plane))

        # Add the floor of the bin
        result.add(self.brick_floor(plane)).combine()

        # Combine everything together
        result = result.combine()

        return result

    def generate_stl(self, filename):
        model = self.generate_model()
        exporters.export(model, filename)

