# -*- coding: utf-8 -*-
import os
import logging

"""
    This script is used to split the unreal.py into multiple files. For better auto-completion in IDE.
"""

def split_stub(file_path, targetFolder):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        doc_ranges = []

        class_name = "_Global"
        last_line_number = 0
        for line_number, line in enumerate(lines):
            if line[0:6] == "class " and line[:-1]:
                last_class_name = class_name
                class_name = line[6: line.find('(') ]
                print("{} Class Name: {}   line: {}".format(line_number, last_class_name, line.strip()))
                doc_ranges.append([last_line_number, line_number, last_class_name])
                last_line_number = line_number
        # add the last content
        doc_ranges.append([last_line_number, len(lines)-1, class_name])

        if not os.path.exists(targetFolder):
            os.makedirs(targetFolder)

        init_py_file_path = os.path.join(targetFolder, "__init__.py")
        init_lines = []
        for start, end, class_name in doc_ranges:
            with open(f"{targetFolder}/{class_name}.py", 'w', encoding='utf-8') as f:
                f.writelines(lines[start:end])
                init_lines.append(f"from .{class_name} import *\n")

        with open(init_py_file_path, 'w', encoding="UTF-8") as f:
            f.writelines(init_lines)

if __name__ == "__main__":
    local_folder = os.path.dirname(__file__)
    stub_folder = os.path.join(local_folder, "../../../..", "Intermediate/PythonStub")
    latest_unreal_py = os.path.abspath(os.path.join(stub_folder, "unreal.py"))

    if os.path.exists(os.path.exists(latest_unreal_py)):
        target_folder = os.path.abspath(os.path.join(local_folder, "..", "unreal"))
        split_stub(file_path=latest_unreal_py, targetFolder=target_folder)
        print("unreal stub has export to: {}".format(target_folder))
    else:
        logging.warning(f"Can't find the stub file: {latest_unreal_py}. Please turn on Developer Mode in UE Editor Preferences > Plugins > Python.")

