from dataclasses import dataclass
from enum import Enum

# Hole shapes
class HoleShape(Enum):
    CIRCLE = 1
    SQUARE = 2
    HEAXAGON = 3

# Generator inputs
@dataclass
class Settings:
    numHolesX: int = 3 # Number of holes in the Width (X) direction
    numHolesY: int = 3 # Number of holes in the Length (Y) direction
    holeShape: HoleShape = HoleShape.CIRCLE # The shape of the hole to use
    holeDiameter: float = 4.0 # Diameter of the hole
    holeDepth: float = 5.0 # Depth of the holes
    keepoutDiameter: float = 6.0 # Diameter of the keepout area

    addStackingLip: bool = True  # Add a stacking lip (True) or not (False)?
    addMagnetHoles: bool = True  # Add holes for magnets
    magnetHoleDiameter: float = 6.5 # Diameter of magnet holes
    addRemovalHoles: bool = False # Add an extra magnet-removal hole to each magnet hole
    addScrewHoles:  bool = True  # Add holes for screws

    exportFormat: str = "stl"
