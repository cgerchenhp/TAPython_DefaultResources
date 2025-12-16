"""
Minimal Editor Mode Example

A bare-bones editor mode example showing the absolute minimum required functionality:
- Enable/disable editor mode
- Capture mouse drag events
- Display cursor position
"""

import unreal
from Utilities.Utils import Singleton


class MinimalEditorMode(metaclass=Singleton):
    """
    The simplest possible editor mode implementation.
    
    This example demonstrates:
    - Basic editor mode toggle
    - Mouse drag event handling
    - Status text updates
    """
    
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.data: unreal.ChameleonData = unreal.PythonBPLib.get_chameleon_data(self.json_path)

    def on_drag(self, input_ray: unreal.InputDeviceRay, mouse_button: str, delta_time: float) -> None:
        """Handle mouse drag in viewport - update status text with cursor position."""
        screen_pos = input_ray.screen_position
        status_text = f"Dragging with {mouse_button} at ({screen_pos.x:.0f}, {screen_pos.y:.0f})"
        self.data.set_text("StatusText", status_text)
        unreal.log(status_text)
    
    def on_check_state_changed(self, is_enabled: bool) -> None:
        """Toggle editor mode on/off."""
        self.data.set_chameleon_editor_mode_enabled(is_enabled)
        
        button_text = "✓ Mode Active" if is_enabled else "Enable Mode"
        self.data.set_text("ButtonText", button_text)
        
        status = "Mode enabled — drag over a scene object to interact; \n(dragging empty space has no effect.)" if is_enabled else "Mode disabled"
        self.data.set_text("StatusText", status)
