import cadquery as cq
from cadquery import exporters
from dataclasses import dataclass
from gridfinity import *

# Generator inputs
@dataclass
class Settings:
    sizeUnitsX: int = 3 # Width (X) of the brick in grid units
    sizeUnitsY: int = 1  # Length (Y) of the brick in grid units



