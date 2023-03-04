# GridFinity defined constants
# Magic numbers come from the GridFinity profile specification (https://gridfinity.xyz/specification/)
GRID_UNIT_SIZE_MM = 42
HEIGHT_UNITSIZE_MM = 7
BRICK_SIZE_TOLERANCE_MM = 0.5
BRICK_UNIT_SIZE = GRID_UNIT_SIZE_MM - BRICK_SIZE_TOLERANCE_MM
BASE_BOTTOM_SIZE = BRICK_UNIT_SIZE-4.3
BASE_BOTTOM_THICKNESS = 2.6
BASE_TOP_THICKNESS = 2.15
FLOOR_THICKNESS = 2.25 # This ensures the base is exactly 1 height unit high
MAGNET_HOLE_DIAMETER = 6.5
MAGNET_HOLE_DEPTH = 2
SCREW_HOLE_DIAMETER = 3
SCREW_HOLE_DEPTH = 6
HOLE_OFFSET = 13
WALL_THICKNESS = 1.9
CORNER_FILLET_RADIUS = 3.75
STACKING_LIP_HEIGHT = 4.4
EPSILON = 0.01 # CQ cannot chamfer an edge all the way to another edge, so reduce the chamfer by a tiny amount to avoid problems

# Some limits for sanity checking the inputs
MAX_COMPARTMENTS_PER_GRID_UNIT = 3
MAX_GRID_UNITS = 6
MAX_HEIGHT_UNITS = 12
