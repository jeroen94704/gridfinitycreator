from dataclasses import dataclass

@dataclass
class Grid:
    """This class holds the necessary key dimensions to define the grid used by all 
       the generators to create components that fit together. The defaults are all
       set to Gridfinity standard values, but for flexibility these can be changed 
       to generate e.g. Raaco compatible bins
    """
        
    # CQ cannot chamfer an edge all the way to another edge, so reduce the chamfer by a tiny amount to avoid problems
    CHAMFER_EPSILON: float = 0.01 

    # Fixed dimensions (Magic numbers come from the GridFinity profile specification (https://gridfinity.xyz/specification/))
    GRID_UNIT_SIZE_X_MM: float = 42
    GRID_UNIT_SIZE_Y_MM: float = 42
    HEIGHT_UNITSIZE_MM: float = 7
    BRICK_SIZE_TOLERANCE_MM: float = 0.5
    BASE_BOTTOM_THICKNESS: float = 2.6
    BASE_BOTTOM_CHAMFER_SIZE: float = 0.8
    BASE_BOTTOM_FILLET_RADIUS: float = 1.6
    BASE_TOP_THICKNESS: float = 2.15
    BASE_TOP_FILLET_RADIUS: float = 3.75
    FLOOR_THICKNESS: float = 2.25 # This thickness makes the base exactly 1 height unit high
    LIGHT_FLOOR_THICKNESS: float = 0.9
    DEFAULT_MAGNET_HOLE_DIAMETER: float = 6.5
    DEFAULT_MAGNET_HOLE_DEPTH: float = 2
    SCREW_HOLE_DIAMETER: float = 3
    SCREW_HOLE_DEPTH: float = 6

    REMOVABLE_MAGNET_HOLE_OFFSET: float = 2.16 # This places the center of the remove-hole on the perimeter of the magnet hole
    REMOVABLE_MAGNET_HOLE_DIAMETER: float = 3.5
    WALL_THICKNESS: float = 1.9
    CORNER_FILLET_RADIUS: float = 3.75
    STACKING_LIP_HEIGHT: float = 4.4

    # Derived dimensions
    BRICK_UNIT_SIZE_X: float = GRID_UNIT_SIZE_X_MM - BRICK_SIZE_TOLERANCE_MM
    BRICK_UNIT_SIZE_Y: float = GRID_UNIT_SIZE_Y_MM - BRICK_SIZE_TOLERANCE_MM
    BASE_BOTTOM_SIZE_X: float = BRICK_UNIT_SIZE_X-4.3
    BASE_BOTTOM_SIZE_Y: float = BRICK_UNIT_SIZE_Y-4.3
    BASE_TOP_CHAMFER_SIZE: float = BASE_TOP_THICKNESS - CHAMFER_EPSILON
    HOLE_OFFSET_X: float = BRICK_UNIT_SIZE_X/2 - BASE_TOP_CHAMFER_SIZE - BASE_BOTTOM_CHAMFER_SIZE - 4.8
    HOLE_OFFSET_Y: float = BRICK_UNIT_SIZE_Y/2 - BASE_TOP_CHAMFER_SIZE - BASE_BOTTOM_CHAMFER_SIZE - 4.8

    # Some limits for sanity checking the inputs
    MAX_COMPARTMENTS_PER_GRID_UNIT: float = 3
    MAX_GRID_UNITS: float = 6
    MAX_HEIGHT_UNITS: float = 12
    MIN_HEIGHT_UNITS: float = 2 # A height of 1 unit would be just the base without anything on top

    def recalculate(self):
        # Recalculate the derived dimensions after changing one of the relevant fixed dimensions
        self.BRICK_UNIT_SIZE_X = self.GRID_UNIT_SIZE_X_MM - self.BRICK_SIZE_TOLERANCE_MM
        self.BRICK_UNIT_SIZE_Y = self.GRID_UNIT_SIZE_Y_MM - self.BRICK_SIZE_TOLERANCE_MM
        self.BASE_BOTTOM_SIZE_X = self.BRICK_UNIT_SIZE_X-4.3
        self.BASE_BOTTOM_SIZE_Y = self.BRICK_UNIT_SIZE_Y-4.3
        self.BASE_TOP_CHAMFER_SIZE = self.BASE_TOP_THICKNESS - self.CHAMFER_EPSILON
        self.HOLE_OFFSET_X = self.BRICK_UNIT_SIZE_X/2 - self.BASE_TOP_CHAMFER_SIZE - self.BASE_BOTTOM_CHAMFER_SIZE - 4.8
        self.HOLE_OFFSET_Y = self.BRICK_UNIT_SIZE_Y/2 - self.BASE_TOP_CHAMFER_SIZE - self.BASE_BOTTOM_CHAMFER_SIZE - 4.8
