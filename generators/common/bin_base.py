import cadquery as cq

from grid_constants import *

def unit_base(basePlane, settings, grid):
    """Construct a 1x1 GridFinity unit base on the provided workplane"""
    
    # The elements are constructed "centered" because that makes life easier. 
    baseBottom = basePlane.box(grid.BASE_BOTTOM_SIZE_X, grid.BASE_BOTTOM_SIZE_Y, grid.BASE_BOTTOM_THICKNESS, combine=False)
    baseBottom = baseBottom.edges("|Z").fillet(grid.BASE_BOTTOM_FILLET_RADIUS)
    baseBottom = baseBottom.faces("<Z").chamfer(grid.BASE_BOTTOM_CHAMFER_SIZE)
    
    baseTop = baseBottom.faces(">Z").workplane()
    baseTop = baseTop.box(grid.BRICK_UNIT_SIZE_X, grid.BRICK_UNIT_SIZE_Y, grid.BASE_TOP_THICKNESS, centered=(True, True, False), combine=False)
    baseTop = baseTop.edges("|Z").fillet(grid.CORNER_FILLET_RADIUS)
    baseTop = baseTop.faces("<Z").chamfer(grid.BASE_TOP_CHAMFER_SIZE)
    
    result = baseTop | baseBottom
    
    if settings.addMagnetHoles:
        result = result.faces("<Z").workplane()
        result = result.pushPoints([(grid.HOLE_OFFSET_X, grid.HOLE_OFFSET_Y),
                                            (-grid.HOLE_OFFSET_X, grid.HOLE_OFFSET_Y),
                                            (grid.HOLE_OFFSET_X, -grid.HOLE_OFFSET_Y),
                                            (-grid.HOLE_OFFSET_X, -grid.HOLE_OFFSET_Y)])
        result = result.hole(settings.magnetHoleDiameter, grid.DEFAULT_MAGNET_HOLE_DEPTH)

        if settings.addRemovalHoles:
            result = result.pushPoints([(grid.HOLE_OFFSET_X-grid.REMOVABLE_MAGNET_HOLE_OFFSET, grid.HOLE_OFFSET_Y-grid.REMOVABLE_MAGNET_HOLE_OFFSET),
                                            (-grid.HOLE_OFFSET_X+grid.REMOVABLE_MAGNET_HOLE_OFFSET, grid.HOLE_OFFSET_Y-grid.REMOVABLE_MAGNET_HOLE_OFFSET),
                                            (grid.HOLE_OFFSET_X-grid.REMOVABLE_MAGNET_HOLE_OFFSET, -grid.HOLE_OFFSET_Y+grid.REMOVABLE_MAGNET_HOLE_OFFSET),
                                            (-grid.HOLE_OFFSET_X+grid.REMOVABLE_MAGNET_HOLE_OFFSET, -grid.HOLE_OFFSET_Y+grid.REMOVABLE_MAGNET_HOLE_OFFSET)])
            result = result.hole(grid.REMOVABLE_MAGNET_HOLE_DIAMETER, grid.DEFAULT_MAGNET_HOLE_DEPTH)

    if settings.addScrewHoles:
        result = result.faces("<Z").workplane()
        result = result.pushPoints([(grid.HOLE_OFFSET_X, grid.HOLE_OFFSET_Y),
                                    (-grid.HOLE_OFFSET_X, grid.HOLE_OFFSET_Y),
                                    (grid.HOLE_OFFSET_X, -grid.HOLE_OFFSET_Y),
                                    (-grid.HOLE_OFFSET_X, -grid.HOLE_OFFSET_Y)])
        result = result.hole(grid.SCREW_HOLE_DIAMETER, grid.SCREW_HOLE_DEPTH)
        
    # Translate the result because it is now centered around the origin, which is inconvenient for subsequent steps
    result = result.translate((grid.BRICK_UNIT_SIZE_X/2, grid.BRICK_UNIT_SIZE_Y/2, grid.BASE_BOTTOM_THICKNESS/2))
            
    return result

def grid_base(basePlane, settings, grid):
    """Construct a base of WidthxLength grid units"""
    
    result = basePlane.workplane()
    
    base_unit = unit_base(basePlane, settings, grid)
    
    for x in range(settings.sizeUnitsX):
        for y in range(settings.sizeUnitsY):
            result.add(base_unit.translate((x*grid.GRID_UNIT_SIZE_X_MM, y*grid.GRID_UNIT_SIZE_Y_MM, 0)))
    
    return result

def brick_floor(basePlane, settings, grid):
    """Create a floor covering all unit bases"""

    brickSizeX = settings.sizeUnitsX * grid.GRID_UNIT_SIZE_X_MM - grid.BRICK_SIZE_TOLERANCE_MM 
    brickSizeY = settings.sizeUnitsY * grid.GRID_UNIT_SIZE_Y_MM - grid.BRICK_SIZE_TOLERANCE_MM

    floor = basePlane.box(brickSizeX, brickSizeY, grid.FLOOR_THICKNESS, centered = False, combine = False)
    
    floor = floor.edges("|Z").fillet(grid.CORNER_FILLET_RADIUS)

    return floor

def bin_base(basePlane, settings, grid):
    
    result = grid_base(basePlane, settings, grid)

    # Continue from the top of the base
    plane = result.faces(">Z").workplane()

    # Add the floor of the bin
    result.add(brick_floor(plane, settings, grid))

    result = result.combine(clean=True)

    return result