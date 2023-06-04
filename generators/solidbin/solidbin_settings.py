from dataclasses import dataclass

# Generator inputs
@dataclass
class Settings:
    sizeUnitsX: int = 3 # Width (X) of the brick in grid units
    sizeUnitsY: int = 1  # Length (Y) of the brick in grid units
    sizeUnitsZ: int = 3  # Height (Z) of the brick in height-units

    addStackingLip: bool = True  # Add a stacking lip (True) or not (False)?
    addMagnetHoles: bool = True  # Add holes for magnets
    addScrewHoles:  bool = True  # Add holes for screws