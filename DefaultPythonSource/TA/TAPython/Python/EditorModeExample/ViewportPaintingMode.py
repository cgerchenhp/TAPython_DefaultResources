"""
Viewport Painting Editor Mode Example

Demonstrates how to create a custom editor mode with viewport interaction capabilities.

=== JSON Configuration ===
    --- Core Configuration ---
    - EditorModeName: Display name of the editor mode
    - EditorModePropertySetClass: Property set class for customizable properties in Details panel
    - EditorModeAutoEnable: Whether to automatically enable the editor mode. (Default: True )

    --- Event Callbacks ---
    - EditorModeOnDrag: Invoked when mouse is dragged in viewport
    - EditorModeOnMouseDown: Invoked when mouse button is pressed
    - EditorModeOnMouseUp: Invoked when mouse button is released
    - EditorModeOnMouseWheel: Invoked when mouse wheel is scrolled
    - EditorModeCanCapture: Determines whether to capture mouse input

    === UI Components ===
    - Root: Tool panel UI (sidebar)
    - ViewportUI: Viewport overlay UI

=== PropertySet Usage ===
1. Define property class: Inherit from unreal.ChameleonEditorModeToolProperties
2. Set default values: Use get_default_object().set_editor_property()
3. Read properties: self.data.get_editor_mode_property_set().get_editor_property("property_name")
4. Write properties: property_set.set_editor_property("property_name", value)

=== Features ===
- 2D brush icon that follows mouse cursor in viewport
- Line tracing with 3D brush visualization (circle + normal) at hit point
- Configurable mouse button capture rules
- Viewport overlay visibility and interactivity control
"""

import unreal
from Utilities.Utils import Singleton
from typing import Literal, Optional


@unreal.uclass()
class ViewportPaintingModeProperties(unreal.ChameleonEditorModeToolProperties):
    static_mesh = unreal.uproperty(unreal.StaticMesh)
    color = unreal.uproperty(unreal.LinearColor)

# set default property values
set_cdo = ViewportPaintingModeProperties.get_default_object()
set_cdo.set_editor_property("color", unreal.LinearColor.GREEN)
set_cdo.set_editor_property("static_mesh", unreal.load_asset('/Engine/BasicShapes/Cube.Cube'))


class ViewportPaintingModeExample(metaclass=Singleton):
    
    def __init__(self, json_path: str):
        self.data: unreal.ChameleonData = unreal.PythonBPLib.get_chameleon_data(json_path)
        self._world: Optional[unreal.World] = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        self.b_draw_2d_brush = True
        self.brush3d_opacity = 0.5
        self.brush3d_radius = 200.0
        self.brush3d_color = unreal.LinearColor.GREEN
        self.meshes = [unreal.load_asset(f'/Engine/BasicShapes/{n}.{n}') 
                       for n in ['Cone', 'Cube', 'Cylinder', 'Plane', 'Sphere']]

    # =========================================================================
    # Editor Mode Event Handlers (Called by Framework)
    # =========================================================================
    def on_drag(
        self,
        input_ray: unreal.InputDeviceRay,
        mouse_button: Literal['LeftMouseButton', 'MiddleMouseButton', 'RightMouseButton'],
        delta_time: float
    ) -> None:
        screen_pos = input_ray.screen_position - unreal.Vector2D.ONE * 32
        self.data.set_canvas_element_position("CircleBrush", pos=screen_pos)
        
        color_map = {
            "LeftMouseButton": unreal.LinearColor(0, 0, 1, 1),
            "MiddleMouseButton": unreal.LinearColor(1, 1, 0, 1),
            "RightMouseButton": unreal.LinearColor(1, 0, 0, 1),
        }
        self.data.set_color_and_opacity("CircleBrush", color_map.get(mouse_button, unreal.LinearColor.WHITE))
        
        world_pos = None
        if mouse_button == "LeftMouseButton":
            world_pos = self._line_trace(input_ray)
        
        status = f"Button: {mouse_button}, Screen: {screen_pos.x:.0f}, {screen_pos.y:.0f}"
        if world_pos:
            status += f", World: {world_pos.x:.0f}, {world_pos.y:.0f}, {world_pos.z:.0f}"
        self.data.set_text("StatusText", status)
    
    def on_mouse_down(self, input_ray: unreal.InputDeviceRay, mouse_button: str) -> None:
        self._world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        self.brush3d_color = self.data.get_editor_mode_property_set().get_editor_property("color")
        
        if self.b_draw_2d_brush:
            self.data.set_visibility("CircleBrush", "Visible")
            screen_pos = input_ray.screen_position - unreal.Vector2D.ONE * 32
            self.data.set_canvas_element_position("CircleBrush", pos=screen_pos)
            self.data.set_color_and_opacity("CircleBrush", unreal.LinearColor(0, 1, 0, 1))

    def on_mouse_up(self, input_ray: unreal.InputDeviceRay, mouse_button: str) -> None:
        self.data.set_color_and_opacity("CircleBrush", unreal.LinearColor.WHITE)
        self.data.set_text("StatusText", f"Mouse Released, last Button: {mouse_button}")

    def on_wheel(self, delta: float) -> None:
        property_set = self.data.get_editor_mode_property_set()
        current_mesh = property_set.get_editor_property("static_mesh")
        current_index = self.meshes.index(current_mesh)
        if current_index != -1:
            new_index = (current_index + (1 if delta > 0 else -1)) % len(self.meshes)
            property_set.set_editor_property("static_mesh", self.meshes[new_index])

    def can_capture_mouse(self, input_ray: unreal.InputDeviceRay, mouse_button: str) -> Optional[bool]:
        """
        Return value controls framework behavior:
        - True: Force capture mouse input (framework uses this function's decision)
        - False: Force reject capture (framework uses this function's decision)
        - None: Let framework decide automatically (framework ignores this function, uses default behavior)
        """
        if mouse_button == "LeftMouseButton":
            return True
        if mouse_button == "MiddleMouseButton":
            return unreal.PythonBPLib.get_modifier_keys_state().get("IsControlDown", False)
        return None

    # =========================================================================
    # UI Control Callbacks (Called by UI Widgets)
    # =========================================================================
    def on_painting_state_changed(self, is_enabled: bool) -> None:
        self.data.set_chameleon_editor_mode_enabled(is_enabled)
        if not is_enabled:
            self.data.set_visibility("CircleBrush", "Hidden")
        self.data.set_text("CheckBoxText", "Disable Painting" if is_enabled else "Enable Painting")
    
    def on_viewport_brush_button_clicked(self) -> None:
        self.b_draw_2d_brush = not self.b_draw_2d_brush
        self.data.set_visibility("CircleBrush", "visible" if self.b_draw_2d_brush else "Hidden")
        self.data.set_text("ButtonInViewport", "Hide 2D Brush" if self.b_draw_2d_brush else "Show 2D Brush")

    def set_viewport_ui_visible(self, is_visible: bool) -> None:
        self.data.set_chameleon_mode_viewport_widget_visibility(is_visible)
    
    def set_viewport_ui_clickable(self, is_clickable: bool) -> None:
        self.data.set_chameleon_mode_viewport_widget_clickable(is_clickable)
    
    def on_mouse_option_changed(
        self,
        is_enabled: bool,
        button_name: Literal['MiddleMouseButton', 'RightMouseButton']
    ) -> None:
        if button_name == "MiddleMouseButton":
            self.data.set_editor_mode_capture_middle_button(is_enabled)
        elif button_name == "RightMouseButton":
            self.data.set_editor_mode_capture_right_button(is_enabled)

    def on_change_brush3d_radius(self, value: float) -> None:
        self.brush3d_radius = value
        self._draw_brush(unreal.Vector(), unreal.Vector.UP, self.brush3d_color, duration=0.066)

    def on_change_brush3d_opacity(self, value: float) -> None:
        self.brush3d_opacity = value
        self._draw_brush(unreal.Vector(), unreal.Vector.UP, self.brush3d_color, duration=0.066)

    # =========================================================================
    # Internal Utility Functions
    # =========================================================================
    def _convert_hit_result_to_dict(self, hit_result: unreal.HitResult) -> dict:
        """Convert HitResult tuple to dictionary for easier field access."""
        hit_result_tuple = hit_result.to_tuple()
        keys = [
            "blocking_hit", "initial_overlap", "time", "distance", "location", "impact_point",
            "normal", "impact_normal", "phys_mat", "hit_actor", "hit_component",
            "hit_bone_name", "bone_name", "hit_item", "element_index", "face_index",
            "trace_start", "trace_end"
        ]
        return {key: hit_result_tuple[i] for i, key in enumerate(keys)}

    def _line_trace(self, input_ray: unreal.InputDeviceRay) -> Optional[unreal.Vector]:
        world_ray = input_ray.world_ray
        hit_result = unreal.SystemLibrary.line_trace_single_by_profile(
            self._world, world_ray.origin, world_ray.direction * 10_000_000,
            profile_name="BlockAll", trace_complex=True,
            actors_to_ignore=[], draw_debug_type=unreal.DrawDebugTrace.NONE,
            ignore_self=True, draw_time=1.0
        )
        if not hit_result:
            return None

        hit_data = self._convert_hit_result_to_dict(hit_result)
        if not hit_data["blocking_hit"]:
            return None

        hit_point = hit_data["impact_point"]
        normal = hit_data["normal"]

        # Add a one-unit upward offset to avoid z-fighting.
        # In Unreal Engine 5.7 and later, you can use the
        # `depth_priority=unreal.DrawDebugSceneDepthPriorityGroup.FOREGROUND`
        # parameter instead of applying this offset.
        self._draw_brush(hit_point + unreal.Vector.UP, normal, self.brush3d_color)
        return hit_point

    def _draw_brush(
        self,
        hit_point: unreal.Vector,
        normal: unreal.Vector,
        brush_color: unreal.LinearColor,
        duration: float = 1.0
    ) -> None:
        unreal.SystemLibrary.draw_debug_circle(
            self._world, center=hit_point, radius=self.brush3d_radius, num_segments=24,
            line_color=brush_color, duration=duration,
            y_axis=unreal.Vector.LEFT, z_axis=unreal.Vector.cross(unreal.Vector.LEFT, normal),
            draw_axis=False
        )
        unreal.SystemLibrary.draw_debug_line(
            self._world, line_start=hit_point,
            line_end=hit_point + normal * self.brush3d_opacity * self.brush3d_radius * 2,
            line_color=unreal.LinearColor(1, 0, 0, 1),
            duration=duration
        )
