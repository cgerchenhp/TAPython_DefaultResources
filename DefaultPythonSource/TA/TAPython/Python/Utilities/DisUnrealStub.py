# -*- coding: utf-8 -*-
import os
import logging
import shutil

def split_stub(file_path, targetFolder):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

        index = 0
        class_name = "_Global"
        last_class_name = ""
        doc_ranges = []
        start = 0

        for line in lines:
            if line[0:6] == "class " and line[:-1]:
                last_class_name = class_name
                class_name = line[6: line.find('(') ]
                print("{} Class Name: {}   line: {}".format(index, last_class_name, line.strip()))
                doc_ranges.append([start, index, last_class_name])
                start = index
            index += 1
        doc_ranges.append([start, index, class_name])

        if not os.path.exists(targetFolder):
            os.makedirs(targetFolder)

        for start, end, class_name in doc_ranges:
            with open(f"{targetFolder}/{class_name}.py", 'w', encoding='utf-8') as f:
                f.writelines(lines[start:end])

if __name__ == "__main__":
    local_folder = os.getcwd()
    latest_stub_folder = os.path.join(local_folder, "../../../..", "Intermediate/PythonStub")
    latest_unreal_py = os.path.join(latest_stub_folder, "unreal.py")
    print(f"stub, unreal.py exists: {os.path.exists(latest_unreal_py)}")

    current_unreal_py = "{}/../unreal.py".format(os.path.dirname(__file__))
    print(f"current unreal.py exists: {os.path.exists(latest_unreal_py)}")
    shutil.copy(latest_unreal_py, current_unreal_py)

    if not os.path.exists(current_unreal_py):
        logging.warning("Can't find file: {}".format(current_unreal_py))
    else:
        target_folder = os.path.abspath(os.path.join(local_folder, "..", "unreal"))

        split_stub(file_path=current_unreal_py, targetFolder=target_folder)
        print("unreal stub has export to: {}".format(target_folder))
