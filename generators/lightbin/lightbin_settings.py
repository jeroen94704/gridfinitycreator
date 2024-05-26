from dataclasses import dataclass

# Generator inputs
@dataclass
class Settings:
    sizeUnitsX: int = 3 # Width (X) of the brick in grid units
    sizeUnitsY: int = 2  # Length (Y) of the brick in grid units
    sizeUnitsZ: int = 3  # Height (Z) of the brick in height-units

    compartmentsX: int = 2 # The number of compartments in the X (width) direction 
    compartmentsY: int = 1 # The number of compartments in the Y (length) direction 

    addStackingLip: bool = True  # Add a stacking lip (True) or not (False)?
    addLabelRidge:  bool = True  # Add a ridge to pick up the bin and attach a label
    multiLabel:     bool = False # Add a ridge to every row of compartments?

    labelRidgeWidth:  int = 13   
    wallThickness: int = 1.5