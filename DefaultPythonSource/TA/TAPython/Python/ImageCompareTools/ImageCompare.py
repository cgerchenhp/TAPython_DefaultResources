import unreal
from Utilities.Utils import Singleton

import math

try:
    import numpy as np
    b_use_numpy = True
except:
    b_use_numpy = False

class ImageCompare(metaclass=Singleton):
    def __init__(self, json_path:str):
        self.json_path = json_path
        self.data:unreal.ChameleonData = unreal.PythonBPLib.get_chameleon_data(self.json_path)
        self.left_texture_size = (128, 128)
        self.right_texture_size = (128, 128)
        self.dpi_scale = 1

        self.ui_img_left = "ImageLeft"
        self.ui_img_right = "ImageRight"
        self.ui_img_right_bg = "ImageRightBG"
        self.ui_comparison_widget = "ComparisonWidget"
        self.ui_dpi_scaler = "Scaler"
        self.ui_status_bar = "StatusBar"
        self.ui_ignore_alpha = "AlphaCheckBox"
        self.ui_scaler_combobox = "ScaleComboBox"
        self.combobox_items = self.data.get_combo_box_items(self.ui_scaler_combobox)

        self.update_status_bar()

    def set_image_from_viewport(self, bLeft):
        data, width_height = unreal.PythonBPLib.get_viewport_pixels_as_data()
        w, h = width_height.x, width_height.y

        channel_num = int(len(data) / w / h)

        if b_use_numpy:
            im = np.fromiter(data, dtype=np.uint8).reshape(w, h, channel_num)

            self.data.set_image_data_from_memory(self.ui_img_left if bLeft else self.ui_img_right, im.ctypes.data, len(data)
                                 , w, h, channel_num=channel_num, bgr=False
                                 , tiling=unreal.SlateBrushTileType.HORIZONTAL if bLeft else unreal.SlateBrushTileType.NO_TILE)
        else:
            texture = unreal.PythonBPLib.get_viewport_pixels_as_texture()
            self.data.set_image_data_from_texture2d(self.ui_img_left if bLeft else self.ui_img_right, texture
                        , tiling=unreal.SlateBrushTileType.HORIZONTAL if bLeft else unreal.SlateBrushTileType.NO_TILE)

        if bLeft:
            self.left_texture_size = (w, h)
        else:
            self.right_texture_size = (w, h)

        self.update_dpi_by_texture_size()
        self.fit_window_size()

    def fit_window_size1(self):
        size = unreal.ChameleonData.get_chameleon_desired_size(self.json_path)

    def set_images_from_viewport(self):
        unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
        self.set_image_from_viewport(bLeft=True)
        unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_WIREFRAME)
        self.set_image_from_viewport(bLeft=False)
        unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
        self.fit_window_size()
        self.update_status_bar()

    def update_dpi_by_texture_size(self):
        max_size = max(self.left_texture_size[1], self.right_texture_size[1])
        if max_size >= 64:
            self.dpi_scale = 1 / math.ceil(max_size / 512)
        else:
            self.dpi_scale = 4 if max_size <= 16 else 2

        print(f"Set dpi -> {self.dpi_scale }")
        self.data.set_dpi_scale(self.ui_dpi_scaler, self.dpi_scale)

        for index, value_str in enumerate(self.combobox_items):
            if float(value_str) == self.dpi_scale:
                self.data.set_combo_box_selected_item(self.ui_scaler_combobox, index)
                break

    def on_ui_change_scale(self, value_str):
        self.dpi_scale = float(value_str)
        self.data.set_dpi_scale(self.ui_dpi_scaler, self.dpi_scale)
        self.fit_window_size()

    def update_status_bar(self):
        self.data.set_text(self.ui_status_bar, f"Left: {self.left_texture_size}, Right: {self.right_texture_size} ")
        if self.left_texture_size != self.right_texture_size:
            self.data.set_color_and_opacity(self.ui_status_bar, unreal.LinearColor(2, 0, 0, 1))
        else:
            self.data.set_color_and_opacity(self.ui_status_bar, unreal.LinearColor.WHITE)
    def fit_window_size(self):
        max_x = max(self.left_texture_size[0], self.right_texture_size[0])
        max_y = max(self.left_texture_size[1], self.right_texture_size[1])
        MIN_WIDTH = 400
        MAX_HEIGHT = 900

        self.data.set_chameleon_window_size(self.json_path
                                            , unreal.Vector2D(max(MIN_WIDTH, max_x * self.dpi_scale + 18)
                                                            , min(MAX_HEIGHT, max_y * self.dpi_scale + 125))
                                            )


    def on_drop(self, bLeft,  **kwargs):
        for asset_path in kwargs["assets"]:
            asset = unreal.load_asset(asset_path)
            if isinstance(asset, unreal.Texture2D):
                width = asset.blueprint_get_size_x()
                height = asset.blueprint_get_size_y()

                ignore_alpha = self.data.get_is_checked(self.ui_ignore_alpha)
                if self.data.set_image_data_from_texture2d(self.ui_img_left if bLeft else self.ui_img_right, asset, ignore_alpha=ignore_alpha):
                    if bLeft:
                        self.left_texture_size = (width, height)
                    else:
                        self.right_texture_size = (width, height)
                    self.update_dpi_by_texture_size()
                    self.fit_window_size()
                    self.update_status_bar()
                    break


