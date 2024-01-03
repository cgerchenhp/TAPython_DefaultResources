# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import unreal
from Utilities.Utils import Singleton
import random
import re

if sys.platform == "darwin":
    import webbrowser


class ChameleonGallery(metaclass=Singleton):
    def __init__(self, jsonPath):
        self.jsonPath = jsonPath
        self.data = unreal.PythonBPLib.get_chameleon_data(self.jsonPath)
        self.ui_scrollbox = "ScrollBox"
        self.ui_crumbname = "SBreadcrumbTrailA"
        self.ui_image = "SImageA"
        self.ui_image_local = "SImage_ImageFromRelativePath"
        self.ui_imageB = "SImage_ImageFromPath"
        self.ui_progressBar = "ProgressBarA"
        self.ui_drop_target_text_box = "DropResultBox"
        self.ui_python_not_ready = "IsPythonReadyImg"
        self.ui_python_is_ready = "IsPythonReadyImgB"
        self.ui_is_python_ready_text = "IsPythonReadyText"
        self.ui_details_view = "DetailsView"
        self.ui_color_block = "ColorBlock"
        self.ui_button_expand_color_picker = "ButtonExpandColorPicker"
        self.ui_color_picker = "ColorPicker"
        self.ui_dpi_scaler = "DPIScaler"
        self.imageFlagA = 0
        self.imageFlagB = 0
        # set data in init
        self.set_random_image_data()
        self.data.set_combo_box_items('CombBoxA', ['1', '3', '5'])
        self.data.set_object(self.ui_details_view,  self.data)
        self.is_color_picker_shown = self.data.get_visibility(self.ui_color_picker) == "Visible"
        self.linearColor_re = re.compile(r"\(R=([-\d.]+),G=([-\d.]+),B=([-\d.]+),A=([-\d.]+)\)")

        self.tapython_version = dict(unreal.PythonBPLib.get_ta_python_version())

        print("ChameleonGallery.Init")

    def mark_python_ready(self):
        print("mark_python_ready call")
        self.data.set_visibility(self.ui_python_not_ready, "Collapsed")
        self.data.set_visibility(self.ui_python_is_ready, "Visible")
        self.data.set_text(self.ui_is_python_ready_text, "Python Path Ready.")


    def push_breadcrumb(self):
        count = self.data.get_breadcrumbs_count_string(self.ui_crumbname)
        strs = "is breadcrumb tail from alice in wonder world"
        label = strs.split()[count % len(strs.split())]
        self.data.push_breadcrumb_string(self.ui_crumbname, label, label)

    def set_random_image_data(self):
        width = 64
        height = 64
        colors = [unreal.LinearColor(1, 1, 1, 1)  if random.randint(0, 1) else unreal.LinearColor(0, 0, 0, 1) for _ in range(width * height)]
        self.data.set_image_pixels(self.ui_image, colors, width, height)

    def set_random_progress_bar_value(self):
        self.data.set_progress_bar_percent(self.ui_progressBar,random.random())


    def change_local_image(self):
        self.data.set_image_from(self.ui_image_local, ["Images/ChameleonLogo_c.png", "Images/ChameleonLogo_b.png"][self.imageFlagA])
        self.imageFlagA = (self.imageFlagA + 1) % 2


    def change_image(self):
        self.data.set_image_from_path(self.ui_imageB, ["PythonChameleonIcon_128x.png", "Icon128.png"][self.imageFlagB])
        self.imageFlagB = (self.imageFlagB + 1) % 2

    def change_comboBox_items(self):
        offset = random.randint(1, 10)
        items = [str(v+offset) for v in range(random.randint(1, 10))]

        self.data.set_combo_box_items("CombBoxA", items)




    def launch_other_galleries(self):
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'auto_gen/border_brushes_Gallery.json')):
            unreal.PythonBPLib.notification("auto-generated Galleries not exists", info_level=1)
            return

        gallery_paths = ['ChameleonGallery/auto_gen/border_brushes_Gallery.json',
                         'ChameleonGallery/auto_gen/image_brushes_Gallery.json',
                         'ChameleonGallery/auto_gen/box_brushes_Gallery.json',
                         'ChameleonGallery/auto_gen/button_style_Gallery.json',
                         'ChameleonGallery/auto_gen/fonts_Gallery.json',
                         'ChameleonGallery/auto_gen/text_block_styles_Gallery.json',
                         'ChameleonGallery/auto_gen/editable_text_box_style_Gallery.json',
                         'ChameleonGallery/auto_gen/link_Styles_Gallery.json',
                         'ChameleonGallery/auto_gen/slate_color_brushes_Gallery.json',
                         'ChameleonGallery/auto_gen/check_box_style_Gallery.json',
                         'ChameleonGallery/auto_gen/richtext_editor_style.json'
                         ]

        bLaunch = unreal.PythonBPLib.confirm_dialog(f'Open Other {len(gallery_paths)} Galleries? You can close them with the "Close all Gallery" Button' , "Open Other Galleries", with_cancel_button=False)

        if bLaunch:
            with unreal.ScopedSlowTask(len(gallery_paths), "Spawn Actors") as slow_task:
                slow_task.make_dialog(True)
                for i, p in enumerate(gallery_paths):
                    slow_task.enter_progress_frame(1, f"Launch Gallery: {p}")

                    unreal.ChameleonData.launch_chameleon_tool(p)

    def request_close_other_galleries(self):
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'auto_gen/border_brushes_Gallery.json')):
            unreal.PythonBPLib.notification("auto-generated Galleries not exists", info_level=1)
            return
        gallery_paths = ['ChameleonGallery/auto_gen/border_brushes_Gallery.json',
                         'ChameleonGallery/auto_gen/image_brushes_Gallery.json',
                         'ChameleonGallery/auto_gen/box_brushes_Gallery.json',
                         'ChameleonGallery/auto_gen/button_style_Gallery.json',
                         'ChameleonGallery/auto_gen/fonts_Gallery.json',
                         'ChameleonGallery/auto_gen/text_block_styles_Gallery.json',
                         'ChameleonGallery/auto_gen/editable_text_box_style_Gallery.json',
                         'ChameleonGallery/auto_gen/link_Styles_Gallery.json',
                         'ChameleonGallery/auto_gen/slate_color_brushes_Gallery.json',
                         'ChameleonGallery/auto_gen/check_box_style_Gallery.json',
                         'ChameleonGallery/auto_gen/richtext_editor_style.json'
                         ]

        for i, p in enumerate(gallery_paths):
            unreal.ChameleonData.request_close(p)
        # unreal.ChameleonData.request_close('/ChameleonGallery/auto_gen/border_brushes_Gallery.json')

    exists_tools_var = [globals()[x] for x in globals() if "Utilities.Utils.Singleton" in str(type(type(globals()[x])))]

    def on_drop(self, assets, assets_folders, actors):
        str_for_show = ""
        for items, name in zip([assets, assets_folders, actors], ["Assets:", "Assets Folders:", "Actors:"]):
            if items:
                str_for_show += f"{name}\n"
                for item in items:
                    str_for_show += f"\t{item}\n"
        self.data.set_text(self.ui_drop_target_text_box, str_for_show)

        print(f"str_for_show: {str_for_show}")

    def on_drop_func(self, *args, **kwargs):
        print(f"args: {args}")
        print(f"kwargs: {kwargs}")
        str_for_show = ""
        for name, items in kwargs.items():
            if items:
                str_for_show += f"{name}:\n"
                for item in items:
                    str_for_show += f"\t{item}\n"
        self.data.set_text(self.ui_drop_target_text_box, str_for_show)

    def get_full_size_of_this_chameleon(self):
        current_size = unreal.ChameleonData.get_chameleon_window_size(self.jsonPath)
        scrollbox_offsets = self.data.get_scroll_box_offsets(self.ui_scrollbox)
        height_full = scrollbox_offsets["ScrollOffsetOfEnd"] / (1.0-scrollbox_offsets["viewFraction"])
        height_full += 48
        print(f"delta: {height_full} - {round(height_full)}")
        return current_size.x, round(height_full)


    def on_button_ChangeTabSize_click(self, offset_pixel):
        current_size = unreal.ChameleonData.get_chameleon_window_size(self.jsonPath)
        print(f"currentSize: {current_size}")
        offsets = self.data.get_scroll_box_offsets(self.ui_scrollbox)
        print(offsets)
        if current_size:
            current_size.x += offset_pixel
            unreal.ChameleonData.set_chameleon_window_size("ChameleonGallery/ChameleonGallery.json", current_size)

    def on_button_FlashWindow_click(self):
        unreal.ChameleonData.flash_chameleon_window("ChameleonGallery/ChameleonGallery.json")

    def on_button_Snapshot_click(self):
        full_size = self.get_full_size_of_this_chameleon()
        print(f"try save snapshot @ {full_size}")
        saved_file_path = unreal.ChameleonData.snapshot_chameleon_window(self.jsonPath, unreal.Vector2D(*full_size))
        if saved_file_path:
            unreal.PythonBPLib.notification(f"UI Snapshot Saved:", hyperlink_text = saved_file_path
                                        , on_hyperlink_click_command = f'chameleon_gallery.explorer("{saved_file_path}")')
        else:
            unreal.PythonBPLib.notification(f"Save UI snapshot failed.", info_level = 1)

    def explorer(self, file_path):
        if sys.platform == "darwin":
            webbrowser.open(os.path.dirname(file_path))
        else:
            file_path = file_path.replace("/", "\\")
            subprocess.call('explorer "{}" '.format(os.path.dirname(file_path)))

    def set_selected_actor_to_details_view(self):
        selected = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_selected_level_actors()
        if selected:
            self.data.set_object(self.ui_details_view, selected[0])
        else:
            print("Selected None")

    def on_expand_color_picker_click(self):
        self.data.set_visibility(self.ui_color_picker, "Collapsed" if self.is_color_picker_shown else "Visible")
        self.data.set_text(self.ui_button_expand_color_picker, "Expand ColorPicker" if self.is_color_picker_shown else "Collapse ColorPicker")
        self.is_color_picker_shown = not self.is_color_picker_shown

        current_size = unreal.ChameleonData.get_chameleon_window_size(self.jsonPath)
        if current_size.x < 650:
            current_size.x = 650
        unreal.ChameleonData.set_chameleon_window_size("ChameleonGallery/ChameleonGallery.json", current_size)

    def on_color_picker_commit(self, color_str):
        v = [float(a) for a in self.linearColor_re.match(color_str).groups()]
        self.data.set_color(self.ui_color_block, unreal.LinearColor(*v))

    def change_dpi_scaler_value(self, value):
        if self.tapython_version["Minor"] < 2 or(
            self.tapython_version["Minor"] == 2 and self.tapython_version["Patch"] < 1
        ):
            print("Need TAPython version >= 1.2.1")
            return
        self.data.set_dpi_scale(self.ui_dpi_scaler, value + 0.5)

