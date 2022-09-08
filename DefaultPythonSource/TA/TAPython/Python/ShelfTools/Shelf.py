import os
import json

import unreal
from Utilities.Utils import Singleton


class Shelf(metaclass=Singleton):
    '''
    This is a demo tool for showing how to create Chamelon Tools in Python
    '''
    MAXIMUM_ICON_COUNT = 12
    Visible = "Visible"
    Collapsed = "Collapsed"

    def __init__(self, jsonPath:str):
        self.jsonPath = jsonPath
        self.data = unreal.PythonBPLib.get_chameleon_data(self.jsonPath)

        self.shelf_data = self.load_data()
        self.is_text_readonly = True
        self.ui_drop_at_last_aka = "DropAtLast"
        self.ui_drop_is_full_aka = "DropIsFull"
        self.update_ui(bForce=True)


    def update_ui(self, bForce=False):
        visibles = [False] * Shelf.MAXIMUM_ICON_COUNT
        for i, shortcut in enumerate(self.shelf_data.shortcuts):
            if i >= Shelf.MAXIMUM_ICON_COUNT:
                continue
            self.data.set_visibility(self.get_ui_button_group_name(i), Shelf.Visible)
            self.data.set_tool_tip_text(self.get_ui_button_group_name(i), self.shelf_data.shortcuts[i].get_tool_tips())
            self.data.set_text(self.get_ui_text_name(i), self.shelf_data.shortcuts[i].text)

            # ITEM_TYPE_PY_CMD = 1  ITEM_TYPE_CHAMELEON = 2 ITEM_TYPE_ACTOR = 3 ITEM_TYPE_ASSETS = 4 ITEM_TYPE_ASSETS_FOLDER = 5
            icon_name = ["PythonTextGreyIcon_40x.png", "PythonChameleonGreyIcon_40x.png", "LitSphere_40x.png", "Primitive_40x.png", "folderIcon.png"][shortcut.drop_type-1]
            if os.path.exists(os.path.join(os.path.dirname(__file__), f"Images/{icon_name}")):
                self.data.set_image_from(self.get_ui_img_name(i), f"Images/{icon_name}")
            else:
                unreal.log_warning("file: {} not exists in this tool's folder: {}".format(f"Images/{icon_name}", os.path.join(os.path.dirname(__file__))))
            visibles[i] = True

        for i, v in enumerate(visibles):
            if not v:
                self.data.set_visibility(self.get_ui_button_group_name(i), Shelf.Collapsed)

        self.lock_text(self.is_text_readonly, bForce)
        bFull = len(self.shelf_data) == Shelf.MAXIMUM_ICON_COUNT
        self.data.set_visibility(self.ui_drop_at_last_aka, "Collapsed" if bFull else "Visible")
        self.data.set_visibility(self.ui_drop_is_full_aka, "Visible" if bFull else "Collapsed" )


    def lock_text(self, bLock, bForce=False):
        if self.is_text_readonly != bLock or bForce:
            for i in range(Shelf.MAXIMUM_ICON_COUNT):
                self.data.set_text_read_only(self.get_ui_text_name(i), bLock)
                self.data.set_color_and_opacity(self.get_ui_text_name(i), [1,1,1,1] if bLock else [1,0,0,1])
                self.data.set_visibility(self.get_ui_text_name(i), "HitTestInvisible" if bLock else "Visible" )

            self.is_text_readonly = bLock


    def get_ui_button_group_name(self, index):
        return f"ButtonGroup_{index}"

    def get_ui_text_name(self, index):
        return f"Txt_{index}"

    def get_ui_img_name(self, index):
        return f"Img_{index}"

    def on_close(self):
        self.save_data()

    def get_data_path(self):
        return os.path.join(os.path.dirname(__file__), "saved_shelf.json")

    def load_data(self):
        saved_file_path = self.get_data_path()
        if os.path.exists(saved_file_path):
            return ShelfData.load(saved_file_path)
        else:
            return ShelfData()

    def save_data(self):
        # fetch text from UI
        for i, shortcut in enumerate(self.shelf_data.shortcuts):
            shortcut.text = self.data.get_text(self.get_ui_text_name(i))
        saved_file_path = self.get_data_path()
        if self.shelf_data != None:
            ShelfData.save(self.shelf_data, saved_file_path)
        else:
            unreal.log_warning("data null")

    def clear_shelf(self):
        self.shelf_data.clear()
        self.update_ui()

    def set_item_to_shelf(self, index, shelf_item):
        if index >= len(self.shelf_data):
            self.shelf_data.add(shelf_item)
        else:
            self.shelf_data.set(index, shelf_item)
        self.update_ui()

    # add shortcuts
    def add_py_code_shortcut(self, index, py_code):
        shelf_item = ShelfItem(icon="", drop_type=ShelfItem.ITEM_TYPE_PY_CMD)
        shelf_item.py_cmd = py_code
        shelf_item.text=py_code[:3]

        self.set_item_to_shelf(index, shelf_item)

    def add_chameleon_shortcut(self, index, chameleon_json):
        short_name = os.path.basename(chameleon_json)
        if short_name.lower().startswith("chameleon") and len(short_name) > 9:
            short_name = short_name[9:]

        shelf_item = ShelfItem(icon="", drop_type=ShelfItem.ITEM_TYPE_CHAMELEON)
        shelf_item.chameleon_json = chameleon_json
        shelf_item.text = short_name[:3]
        self.set_item_to_shelf(index, shelf_item)

    def add_actors_shortcut(self, index, actor_names):
        shelf_item = ShelfItem(icon="", drop_type=ShelfItem.ITEM_TYPE_ACTOR)
        shelf_item.actors = actor_names
        shelf_item.text = shelf_item.actors[0][:3] if shelf_item.actors else ""
        shelf_item.text += str(len(shelf_item.actors))

        self.set_item_to_shelf(index, shelf_item)

    def add_assets_shortcut(self, index, assets):
        shelf_item = ShelfItem(icon="", drop_type=ShelfItem.ITEM_TYPE_ASSETS)
        shelf_item.assets = assets
        if assets:
            first_asset = unreal.load_asset(assets[0])
            if first_asset:
                shelf_item.text = f"{first_asset.get_name()[:3]}{str(len(shelf_item.assets)) if len(shelf_item.assets)>1 else ''}"
            else:
                shelf_item.text = "None"
        else:
            shelf_item.text = ""

        self.set_item_to_shelf(index, shelf_item)

    def add_folders_shortcut(self, index, folders):
        shelf_item = ShelfItem(icon="", drop_type=ShelfItem.ITEM_TYPE_ASSETS_FOLDER)
        shelf_item.folders = folders
        if folders:
            shelf_item.text = f"{(os.path.basename(folders[0]))[:3]}{str(len(folders)) if len(folders)>1 else ''}"
        else:
            shelf_item.text = ""

        self.set_item_to_shelf(index, shelf_item)

    def get_dropped_by_type(self, *args, **kwargs):
        py_cmd = kwargs.get("text", "")

        file_names = kwargs.get("files", None)
        if file_names:
            json_files = [n for n in file_names if n.lower().endswith(".json")]
            chameleon_json = json_files[0] if json_files else ""
        else:
            chameleon_json = ""

        actors = kwargs.get("actors", [])
        assets = kwargs.get("assets", [])
        folders = kwargs.get("assets_folders", [])

        return py_cmd, chameleon_json, actors, assets, folders

    def on_drop(self, id,  *args, **kwargs):
        print(f"OnDrop: id:{id} {kwargs}")
        py_cmd, chameleon_json, actors, assets, folders = self.get_dropped_by_type(*args, **kwargs)
        if chameleon_json:
            self.add_chameleon_shortcut(id, chameleon_json)
        elif py_cmd:
            self.add_py_code_shortcut(id, py_cmd)
        elif actors:
            self.add_actors_shortcut(id, actors)
        elif assets:
            self.add_assets_shortcut(id, assets)
        elif folders:
            self.add_folders_shortcut(id, folders)
        else:
            print("Drop python snippet, chameleon json, actors or assets.")


    def on_drop_last(self, *args, **kwargs):
        print(f"on drop last: {args}, {kwargs}")
        if len(self.shelf_data) <= Shelf.MAXIMUM_ICON_COUNT:
            self.on_drop(len(self.shelf_data) + 1, *args, **kwargs)


    def select_actors(self, actor_names):
        actors = [unreal.PythonBPLib.find_actor_by_name(name) for name in actor_names]
        unreal.PythonBPLib.select_none()
        for i, actor in enumerate(actors):
            if actor:
                unreal.PythonBPLib.select_actor(actor, selected=True, notify=True, force_refresh= i == len(actors)-1)

    def select_assets(self, assets):
        exists_assets = [asset for asset in assets if unreal.EditorAssetLibrary.does_asset_exist(asset)]
        unreal.PythonBPLib.set_selected_assets_by_paths(exists_assets)

    def select_assets_folders(self, assets_folders):
        print(f"select_assets_folders: {assets_folders}")
        unreal.PythonBPLib.set_selected_folder(assets_folders)

    def on_button_click(self, id):
        shortcut = self.shelf_data.shortcuts[id]
        if not shortcut:
            unreal.log_warning("shortcut == None")
            return
        if shortcut.drop_type == ShelfItem.ITEM_TYPE_PY_CMD:
            eval(shortcut.py_cmd)
        elif shortcut.drop_type == ShelfItem.ITEM_TYPE_CHAMELEON:
            unreal.ChameleonData.launch_chameleon_tool(shortcut.chameleon_json)
        elif shortcut.drop_type == ShelfItem.ITEM_TYPE_ACTOR:
            self.select_actors(shortcut.actors) # do anything what you want
        elif shortcut.drop_type == ShelfItem.ITEM_TYPE_ASSETS:
            self.select_assets(shortcut.assets)
        elif shortcut.drop_type == ShelfItem.ITEM_TYPE_ASSETS_FOLDER:
            self.select_assets_folders(shortcut.folders)


class ShelfItem:
    ITEM_TYPE_NONE = 0
    ITEM_TYPE_PY_CMD = 1
    ITEM_TYPE_CHAMELEON = 2
    ITEM_TYPE_ACTOR = 3
    ITEM_TYPE_ASSETS = 4
    ITEM_TYPE_ASSETS_FOLDER = 5
    def __init__(self, drop_type, icon=""):
        self.drop_type = drop_type
        self.icon = icon
        self.py_cmd = ""
        self.chameleon_json = ""
        self.actors = []
        self.assets = []
        self.folders = []
        self.text = ""
    def get_tool_tips(self):
        if self.drop_type == ShelfItem.ITEM_TYPE_PY_CMD:
            return f"PyCmd: {self.py_cmd}"
        elif self.drop_type == ShelfItem.ITEM_TYPE_CHAMELEON:
            return f"Chameleon Tools: {os.path.basename(self.chameleon_json)}"
        elif self.drop_type == ShelfItem.ITEM_TYPE_ACTOR:
            return f"{len(self.actors)} actors: {self.actors}"
        elif self.drop_type == ShelfItem.ITEM_TYPE_ASSETS:
            return f"{len(self.assets)} actors: {self.assets}"
        elif self.drop_type == ShelfItem.ITEM_TYPE_ASSETS_FOLDER:
            return f"{len(self.folders)} folders: {self.folders}"

class ShelfData:
    def __init__(self):
        self.shortcuts = []

    def __len__(self):
        return len(self.shortcuts)

    def add(self, item):
        assert isinstance(item, ShelfItem)
        self.shortcuts.append(item)

    def set(self, index, item):
        assert isinstance(item, ShelfItem)
        self.shortcuts[index] = item

    def clear(self):
        self.shortcuts.clear()

    @staticmethod
    def save(shelf_data, file_path):
        with open(file_path, 'w') as f:
            f.write(json.dumps(shelf_data, default=lambda o: o.__dict__, sort_keys=True, indent=4))
            print(f"Shelf data saved: {file_path}")

    @staticmethod
    def load(file_path):
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'r') as f:
            content = json.load(f)
            instance = ShelfData()
            instance.shortcuts = []
            for item in content["shortcuts"]:
                shelf_item = ShelfItem(item["drop_type"], item["icon"])
                shelf_item.py_cmd = item["py_cmd"]
                shelf_item.chameleon_json = item["chameleon_json"]
                shelf_item.text = item["text"]
                shelf_item.actors = item["actors"]
                shelf_item.assets = item["assets"]
                shelf_item.folders = item["folders"]

                instance.shortcuts.append(shelf_item)
            return instance

