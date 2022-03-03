# -*- coding: utf-8 -*-
import unreal
from Utilities.Utils import Singleton


class MinimalExample(metaclass=Singleton):
    def __init__(self, jsonPath:str):
        self.jsonPath = jsonPath
        self.data = unreal.PythonBPLib.get_chameleon_data(self.jsonPath)
        self.ui_output = "InfoOutput"
        self.clickCount = 0

    def on_button_click(self):
        self.clickCount += 1
        self.data.set_text(self.ui_output, "Clicked {} time(s)".format(self.clickCount))



