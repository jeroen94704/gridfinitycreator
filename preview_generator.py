import io
import base64
import cadquery as cq
from cadquery import exporters
import logging
import json

logger = logging.getLogger('Preview')

class PreviewGenerator:
    """Generates lightweight 3D previews for real-time visualization"""
    
    @staticmethod
    def generate_stl_preview(model, simplify=True):
        """
        Generate a lightweight STL for web preview
        Returns base64 encoded STL data
        """
        try:
            import tempfile
            import os
            
            # Create a temporary file for STL export
            with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            # Export to temporary file
            exporters.export(model, temp_filename, exportType='STL', tolerance=0.1 if simplify else 0.01)
            
            # Read the file and convert to base64
            with open(temp_filename, 'rb') as f:
                stl_data = f.read()
            
            # Clean up temporary file
            os.unlink(temp_filename)
            
            # Return base64 encoded for easy transport
            return base64.b64encode(stl_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            return None
    
    @staticmethod
    def generate_mesh_data(model):
        """
        Generate mesh data (vertices and faces) for direct Three.js consumption
        Returns JSON with vertices and faces arrays
        """
        try:
            # Export to STL to get mesh data
            stl_buffer = io.BytesIO()
            exporters.export(model, stl_buffer, exportType='STL', tolerance=0.1)
            stl_buffer.seek(0)
            
            # For now, return base64 STL
            # In future, we could parse STL to extract vertices/faces
            return base64.b64encode(stl_buffer.read()).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error generating mesh data: {e}")
            return None