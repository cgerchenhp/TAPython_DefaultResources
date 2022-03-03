# -*- coding: utf-8 -*-
import time

import unreal
from Utilities.Utils import Singleton
import random
import os

class ChameleonSketch(metaclass=Singleton):
    def __init__(self, jsonPath):
        self.jsonPath = jsonPath
        self.data = unreal.PythonBPLib.get_chameleon_data(self.jsonPath)
        self.ui_names = ["SMultiLineEditableTextBox", "SMultiLineEditableTextBox_2"]
        self.debug_index = 1
        self.ui_python_not_ready = "IsPythonReadyImg"
        self.ui_python_is_ready = "IsPythonReadyImgB"
        self.ui_is_python_ready_text = "IsPythonReadyText"

        print ("ChameleonSketch.Init")

    def mark_python_ready(self):
        print("set_python_ready call")
        self.data.set_visibility(self.ui_python_not_ready, "Collapsed")
        self.data.set_visibility(self.ui_python_is_ready, "Visible")
        self.data.set_text(self.ui_is_python_ready_text, "Python Path Ready.")

    def get_texts(self):
        for name in self.ui_names:
            n = self.data.get_text(name)
            print(f"name: {n}")

    def set_texts(self):
        for name in self.ui_names:
            self.data.set_text(name, ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"][random.randint(0, 5)])

    def set_text_one(self):
        self.data.set_text(self.ui_names[self.debug_index], ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"][random.randint(0, 5)] )

    def get_text_one(self):
        print(f"name: {self.data.get_text(self.ui_names[self.debug_index])}")

    def tree(self):
        print(time.time())
        names = []
        parent_indices = []
        name_to_index = dict()
        for root, folders, files in os.walk(r"D:\UnrealProjects\5_0\RDZ\Content"):
            root_name = os.path.basename(root)
            if root not in name_to_index:
                name_to_index[root] = len(names)
                parent_indices.append(-1 if not names else name_to_index[os.path.dirname(root)])
                names.append(root_name)
            parent_id = name_to_index[root]
            for items in [folders, files]:
                for item in items:
                    names.append(item)
                    parent_indices.append(parent_id)
        print(len(names))
        self.data.set_tree_view_items("TreeViewA", names,  parent_indices)
        print(time.time())