import cadquery as cq
from cadquery import exporters
from gridfinity import *

class Generator:
    def __init__(self, settings) -> None:
        self.settings = settings

        # Precalculate both before and after validation to process settings that changes
        self.precalculate()
        self.validate_settings()
        self.precalculate()

    def precalculate(self):
        """Precalculate a number of useful derived values used in construction"""
        self.brickSizeX = self.settings.sizeUnitsX * GRID_UNIT_SIZE_MM - BRICK_SIZE_TOLERANCE_MM 
        self.brickSizeY = self.settings.sizeUnitsY * GRID_UNIT_SIZE_MM - BRICK_SIZE_TOLERANCE_MM
        self.brickSizeZ = self.settings.sizeUnitsZ*HEIGHT_UNITSIZE_MM
        self.internalSizeX = self.brickSizeX-2*WALL_THICKNESS
        self.internalSizeY = self.brickSizeY-2*WALL_THICKNESS
        self.compartmentSizeX = self.internalSizeX / self.settings.compartmentsX
        self.compartmentSizeY = self.internalSizeY / self.settings.compartmentsY
        self.compartmentSizeZ = (self.settings.sizeUnitsZ-1)*HEIGHT_UNITSIZE_MM

    def unit_base(self, basePlane):
        """Construct a 1x1 GridFinity unit base on the provided workplane"""

        plane = basePlane.workplane()

        profile = (cq.Workplane("XZ").moveTo(BRICK_UNIT_SIZE/2,0).sketch()
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
        
        theBox = plane.box(BRICK_UNIT_SIZE,BRICK_UNIT_SIZE,0.1).edges('|Z').fillet(CORNER_FILLET_RADIUS).translate((0,0,-2))
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
        result = result.translate((BRICK_UNIT_SIZE/2, BRICK_UNIT_SIZE/2, BASE_BOTTOM_THICKNESS/2))
                
        return result

    def grid_base(self, basePlane):
        """Construct a base of WidthxLength grid units"""
        
        result = basePlane.workplane()
        
        baseUnit = self.unit_base(basePlane)
        for x in range(self.settings.sizeUnitsX):
            for y in range(self.settings.sizeUnitsY):
                result.add(baseUnit.translate((x*GRID_UNIT_SIZE_MM, y*GRID_UNIT_SIZE_MM, 0)))
        
        return result

    def brick_floor(self, basePlane):
        """Create a floor covering all unit bases"""

        plane=basePlane.workplane()

        # Create the solid floor
        floor = basePlane.box(self.brickSizeX, self.brickSizeY, 0.9, centered = False, combine = False)
        floor = floor.edges("|Z").fillet(CORNER_FILLET_RADIUS)

        # Create the cutout and remove it for each base unit
        cutoutSize = BRICK_UNIT_SIZE-2*WALL_THICKNESS
        cutout = plane.box(cutoutSize, cutoutSize,3, combine=False)
        cutout = cutout.edges("|Z")
        cutout = cutout.fillet(CORNER_FILLET_RADIUS-WALL_THICKNESS)
        cutout = cutout.translate((BRICK_UNIT_SIZE/2, BRICK_UNIT_SIZE/2, 0))
                                  
        for x in range(self.settings.sizeUnitsX):
            for y in range(self.settings.sizeUnitsY):
                floor = floor - cutout.translate((x*GRID_UNIT_SIZE_MM, y*GRID_UNIT_SIZE_MM, 0))

        # Chanfer the sharp edges 
        dx = self.brickSizeX
        dy = self.brickSizeY
        s = cq.selectors.BoxSelector((0,0,2), (dx,dy,3))
        floor = floor.edges(s).chamfer(0.9-EPSILON)
        
        return floor

    def outer_wall(self, basePlane):
        """Create the outer wall of the bin"""

        plane=basePlane.workplane()
        
        sizeZ = self.compartmentSizeZ + FLOOR_THICKNESS

        if self.settings.addStackingLip:
            sizeZ = sizeZ + STACKING_LIP_HEIGHT

        wall = plane.box(self.brickSizeX, self.brickSizeY, sizeZ, centered=False, combine = False)
        
        thickness = WALL_THICKNESS
        wall = wall.edges("|Z").fillet(CORNER_FILLET_RADIUS)

        cutout = (
                    plane.center(thickness, thickness)
                    .box(self.internalSizeX, self.internalSizeY, sizeZ, centered=False, combine = False)
                )

        # If the walls are thicker than the outside radius of the corners, skip the fillet
        if thickness < CORNER_FILLET_RADIUS:
            cutout = cutout.edges("|Z").fillet(CORNER_FILLET_RADIUS-thickness)
        
        result = wall-cutout
        
        if self.settings.addStackingLip:
            result = result.edges(
                        cq.selectors.NearestToPointSelector((self.brickSizeX/2, self.brickSizeY/2, sizeZ))
                    ).chamfer(thickness-EPSILON)
            
        return result
    
    def validate_settings(self):
        """Do some sanity checking on the settings to prevent impossible or unreasonable results"""

        # Cap the size in grid-units to avoid thrashing the server
        self.settings.sizeUnitsX = min(self.settings.sizeUnitsX, MAX_GRID_UNITS)
        self.settings.sizeUnitsY = min(self.settings.sizeUnitsY, MAX_GRID_UNITS)
        self.settings.sizeUnitsZ = min(self.settings.sizeUnitsZ, MAX_HEIGHT_UNITS)

        # Limit the number of compartment in each direction
        self.settings.compartmentsX = min(self.settings.compartmentsX, self.settings.sizeUnitsX*MAX_COMPARTMENTS_PER_GRID_UNIT)
        self.settings.compartmentsY = min(self.settings.compartmentsY, self.settings.sizeUnitsY*MAX_COMPARTMENTS_PER_GRID_UNIT)

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

