from dataclasses import dataclass

# Generator inputs
@dataclass
class Settings:
    sizeUnitsX: int = 2 # Width (X) of the brick in grid units
    sizeUnitsY: int = 2  # Length (Y) of the brick in grid units