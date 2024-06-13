import cadquery as cq
from cadquery import exporters
from grid_constants import *

class Generator:
    def __init__(self, settings, grid) -> None:
        self.settings = settings
        self.grid = grid

        self.validate_settings()

    def base_grid(self):
        """Create the baseplate"""
        x_offs = -self.grid.GRID_UNIT_SIZE_X_MM/2
        frame_pts = [(0+x_offs,0), (0+x_offs,4.65), (2.25+x_offs, 2.5), (2.25+x_offs, 0.7), (2.85+x_offs,0)]

        path = cq.Workplane("XY").rect(self.grid.GRID_UNIT_SIZE_X_MM, self.grid.GRID_UNIT_SIZE_Y_MM).val()
        path = path.fillet2D(4, path.Vertices())

        corners = (
            cq.Workplane("XY")
            .box(self.grid.GRID_UNIT_SIZE_X_MM,self.grid.GRID_UNIT_SIZE_Y_MM,4.65)
            .translate((0,0,4.65/2))
            .faces(">Z")
            .sketch()
            .rect(42, 42)
            .vertices()
            .fillet(4)
            .finalize()
            .cutThruAll()
        )

        unit = corners + (
            cq.Workplane("XZ")
            .polyline(frame_pts)
            .close()
            .sweep(path)
            )

        result = cq.Workplane("XY")

        for x in range(self.settings.sizeUnitsX):
            for y in range(self.settings.sizeUnitsX):
                result.add(unit.translate((x*self.grid.GRID_UNIT_SIZE_X_MM, y*self.grid.GRID_UNIT_SIZE_Y_MM, 0)))

        result = result.combine(clean=True)
        result = result.edges("|Z").fillet(3.999)

        return result
    
    def validate_settings(self):
        """Do some sanity checking on the settings to prevent impossible or unreasonable results"""

        # Cap the size in grid-units to avoid thrashing the server
        self.settings.sizeUnitsX = min(self.settings.sizeUnitsX, self.grid.MAX_GRID_UNITS)
        self.settings.sizeUnitsY = min(self.settings.sizeUnitsY, self.grid.MAX_GRID_UNITS)

    def generate_model(self):
        plane = cq.Workplane("XY")
        result = plane.workplane()

        # Add the base of Gridfinity profiles
        result.add(self.base_grid())

        # Combine everything together
        result = result.combine(clean=True)

        return result

    def generate_stl(self, filename):
        model = self.generate_model()
        exporters.export(model, filename)

