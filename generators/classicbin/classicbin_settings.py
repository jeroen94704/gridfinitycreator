from dataclasses import dataclass

# Generator inputs
@dataclass
class Settings:
    sizeUnitsX: int = 3 # Width (X) of the brick in grid units
    sizeUnitsY: int = 1  # Length (Y) of the brick in grid units
    sizeUnitsZ: int = 3  # Height (Z) of the brick in height-units

    compartmentsX: int = 2 # The number of compartments in the X (width) direction 
    compartmentsY: int = 1 # The number of compartments in the Y (length) direction 

    addStackingLip: bool = True   # Add a stacking lip (True) or not (False)?
    addMagnetHoles: bool = True   # Add holes for magnets
    magnetHoleDiameter: float = 6.5 # Diameter of magnet holes
    addRemovalHoles: bool = False # Add an extra magnet-removal hole to each magnet hole
    addScrewHoles:  bool = True   # Add holes for screws
    addGrabCurve:   bool = True   # Add a curved floor to easily get parts out of the bin
    addLabelRidge:  bool = True   # Add a ridge to pick up the bin and attach a label
    multiLabel:     bool = False  # Add a ridge to every row of compartments?

    exportFormat: str = "stl"
    labelRidgeWidth:  int = 13   
    dividerThickness: int = 1.5