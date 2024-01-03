# -*- coding: utf-8 -*-
import unreal
from Utilities.Utils import Singleton


class MinimalExample(metaclass=Singleton):
    def __init__(self, json_path:str):
        self.json_path = json_path
        self.data:unreal.ChameleonData = unreal.PythonBPLib.get_chameleon_data(self.json_path)
        self.ui_output = "InfoOutput"
        self.click_count = 0

    def on_button_click(self):
        self.click_count += 1
        self.data.set_text(self.ui_output, "Clicked {} time(s)".format(self.click_count))

