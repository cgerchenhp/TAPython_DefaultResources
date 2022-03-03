# -*- coding: utf-8 -*-
import os
import unreal
from Utilities.Utils import Singleton
import random

class ChameleonGallery(metaclass=Singleton):
    def __init__(self, jsonPath):
        self.jsonPath = jsonPath
        self.data = unreal.PythonBPLib.get_chameleon_data(self.jsonPath)
        self.ui_crumbname = "SBreadcrumbTrailA"
        self.ui_image = "SImageA"
        self.ui_image_local = "SImage_ImageFromRelativePath"
        self.ui_imageB = "SImage_ImageFromPath"
        self.ui_progressBar = "ProgressBarA"
        self.ui_drop_target_text_box = "DropResultBox"
        self.ui_python_not_ready = "IsPythonReadyImg"
        self.ui_python_is_ready = "IsPythonReadyImgB"
        self.ui_is_python_ready_text = "IsPythonReadyText"
        self.imageFlagA = 0
        self.imageFlagB = 0
        # set data in init
        self.set_random_image_data()
        self.data.set_combo_box_items('CombBoxA', ['1', '3', '5'])
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
            unreal.PythonBPLib.notification("auto-generated Gallerys not exists", info_level=1)
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
                         'ChameleonGallery/auto_gen/check_box_style_Gallery.json']

        bLaunch = unreal.PythonBPLib.confirm_dialog(f'Open Other {len(gallery_paths)} Galleries? You can close them with the "Close all Gallery" Button' , "Open Other Galleries", with_cancel_button=False)

        if bLaunch:
            with unreal.ScopedSlowTask(len(gallery_paths), "Spawn Actors") as slow_task:
                slow_task.make_dialog(True)
                for i, p in enumerate(gallery_paths):
                    slow_task.enter_progress_frame(1, f"Launch Gallery: {p}")

                    unreal.ChameleonData.launch_chalemeon_tool(p)

    def request_close_other_galleries(self):
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'auto_gen/border_brushes_Gallery.json')):
            unreal.PythonBPLib.notification("auto-generated Gallerys not exists", info_level=1)
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
                         'ChameleonGallery/auto_gen/check_box_style_Gallery.json']

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