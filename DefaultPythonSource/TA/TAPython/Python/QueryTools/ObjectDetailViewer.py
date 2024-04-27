# -*- coding: utf-8 -*-
import unreal
import os
from Utilities.Utils import Singleton
from Utilities.Utils import cast
import Utilities
import QueryTools
import re

import types
import collections
from .import Utils

global _r


COLUMN_COUNT = 2
class DetailData(object):
    def __init__(self):
        self.filter_str = ""
        self.filteredIndexToIndex = []
        self.hisCrumbObjsAndNames = []  #list[(obj, propertyName)]

        self.attributes = None
        self.filtered_attributes = None

        self.plains = []
        self.riches = []
        self.selected = set()




    def check_line_id(self, line_id, column_count):
        from_line = line_id * column_count
        to_line = (line_id + 1) * column_count
        assert len(self.plains) == len(self.riches), "len(self.plains) != len(self.riches)"
        if 0 <= from_line < len(self.plains) and 0 <= to_line <= len(self.plains):
            return True
        else:
            unreal.log_error(f"Check Line Id Failed: {line_id}, plains: {len(self.plains)}, rich: {len(self.riches)}")
        return False

    def get_plain(self, line_id, column_count):
        assert self.check_line_id(line_id, column_count), "check line id failed."
        return self.plains[line_id * 2 : line_id * 2 + 2]

    def get_rich(self, line_id, column_count):
        assert self.check_line_id(line_id, column_count), "check line id failed."
        return self.riches[line_id * 2: line_id * 2 + 2]




class ObjectDetailViewer(metaclass=Singleton):

    def __init__(self, jsonPath):
        self.jsonPath = jsonPath
        self.data = unreal.PythonBPLib.get_chameleon_data(self.jsonPath)
        self.ui_checkbox_single_mode = "CheckBoxSingleMode"
        self.ui_checkbox_compare_mode = "CheckBoxCompareMode"
        self.ui_left_group = "LeftDetailGroup"
        self.ui_right_group = "RightDetailGroup"
        self.ui_button_refresh = "RefreshCompareButton"

        self.ui_detailListLeft = "ListViewLeft"
        self.ui_detailListRight = "ListViewRight"
        self.ui_hisObjsBreadcrumbLeft = 'ObjectHisBreadcrumbLeft'
        self.ui_hisObjsBreadcrumbRight = 'ObjectHisBreadcrumbRight'
        # self.ui_headRowLeft = "HeaderRowLeft"
        # self.ui_headRowRight = "HeaderRowRight"
        self.ui_labelLeft = "LabelLeft"
        self.ui_labelRight = "LabelRight"

        self.ui_info_output = "InfoOutput"
        self.ui_rightButtonsGroup = "RightButtonsGroup"  # used for compare mode
        self.ui_rightListGroup = "RightListGroup"
        self.ui_refreshButtonGroup = "RefreshButtonGroup"

        self.reset()

    def on_close(self):
        self.reset()

    def on_map_changed(self, map_change_type_str):
        # remove the reference, avoid memory leaking when load another map.
        if map_change_type_str == "TearDownWorld":
            self.reset(bResetParameter=False)
        else:
            pass # skip: LoadMap, SaveMap, NewMap

    def reset(self, bResetParameter=True):
        if bResetParameter:
            self.showBuiltin = True
            self.showOther = True
            self.showProperties = True
            self.showEditorProperties = True
            self.showParamFunction = True

            self.compareMode = False
        self.left = None
        self.right = None
        self.leftSearchText = ""
        self.rightSearchText = ""

        self.left_rich = None
        self.left_plain = None
        self.var = None
        self.diff_count = 0
        self.clear_ui_info()


    def clear_ui_info(self):
        for text_ui in [self.ui_info_output, self.ui_labelLeft, self.ui_labelRight]:
            self.data.set_text(text_ui, "")

        self.data.set_list_view_multi_column_items(self.ui_detailListLeft, [], 2)
        self.data.set_list_view_multi_column_items(self.ui_detailListRight, [], 2)

        for ui_breadcrumb in [self.ui_hisObjsBreadcrumbRight, self.ui_hisObjsBreadcrumbLeft]:
            crumbCount = self.data.get_breadcrumbs_count_string(ui_breadcrumb)
            for i in range(crumbCount):
                self.data.pop_breadcrumb_string(ui_breadcrumb)


    def update_log_text(self, bRight):
        bShowRight = self.compareMode
        result = ""
        for side_str in ["left", "right"] if bShowRight else ["left"]:
            bRight = side_str != "left"
            ui_breadcrumb = self.ui_hisObjsBreadcrumbRight if bRight else self.ui_hisObjsBreadcrumbLeft
            breadcrumbs =  self.right.hisCrumbObjsAndNames if bRight else self.left.hisCrumbObjsAndNames
            crumbCount = self.data.get_breadcrumbs_count_string(ui_breadcrumb)
            if bRight:
                result += "\t\t\t"
            result += "{} crumb: {}  hisObj: {}".format(side_str, crumbCount, len(breadcrumbs))
        if self.compareMode:
            result = f"{result}\t\t\tdiff count: {self.diff_count}"
        self.data.set_text(self.ui_info_output, result)

    def get_color_by(self, attr : Utils.attr_detail):
        if attr.bCallable_builtin:
            return "DarkTurquoise".lower()
        if attr.bCallable_other:
            return "RoyalBlue".lower()
        if attr.bEditorProperty:
            return "LimeGreen".lower()
        if attr.bOtherProperty:
            return "yellow"

    def get_color(self, typeStr):
        if typeStr == "property":
            return 'white'
        if typeStr == "return_type":
            return 'gray'
        if typeStr == "param":
            return 'gray'

    def get_name_with_rich_text(self, attr:Utils.attr_detail):
        name_color = self.get_color_by(attr)
        param_color = self.get_color("param")
        return_type_color = self.get_color("return_type")
        if attr.bProperty:
            return "\t<RichText.{}>{}</>".format(name_color, attr.name)
        else:
            if attr.param_str:
                return "\t<RichText.{}>{}(</><RichText.{}>{}</><RichText.{}>)</>".format(name_color, attr.name
                                                                                         , param_color, attr.param_str
                                                                                         , name_color)
            else:
                if attr.bCallable_other:
                    return "\t<RichText.{}>{}</>".format(name_color, attr.name)
                else:
                    return "\t<RichText.{}>{}()</><RichText.{}>    {}</>".format(name_color, attr.name
                                                                             , return_type_color, attr.return_type_str)

    def get_name_with_plain_text(self, attr:Utils.attr_detail):
        if attr.bProperty:
            return "\t{}".format(attr.name)
        else:
            if attr.param_str:
                return "\t{}({})".format( attr.name, attr.param_str)
            else:
                if attr.bCallable_other:
                    return "\t{}".format( attr.name)
                else:
                    return "\t{}()    {}".format(attr.name,attr.return_type_str)

    def filter(self, data:DetailData):
        result = []
        indices = []
        for i, attr in enumerate(data.attributes):
            if not self.showEditorProperties and attr.bEditorProperty:
                continue
            if not self.showProperties and attr.bOtherProperty:
                continue
            if not self.showParamFunction and attr.bHasParamFunction:
                continue
            if not self.showBuiltin and attr.bCallable_builtin:
                continue
            if not self.showOther and attr.bCallable_other:
                continue
            if data.filter_str:
                if data.filter_str.lower() not in attr.display_result.lower() and data.filter_str not in attr.display_name.lower() :
                    continue
            result.append(attr)
            indices.append(i)
        return result, indices

    def show_data(self, data:DetailData, ui_listView):
        flatten_list_items = []
        flatten_list_items_plain = []
        for i, attr in enumerate(data.filtered_attributes):
            # print(f"{i}: {attr.name}  {attr.display_name}, {attr.display_result}  ")
            attr.check()
            assert attr.display_name, f"display name null {attr.display_name}"
            assert isinstance(attr.display_result, str), f"display result null {attr.display_result}"

            result_str = attr.display_result
            if len(result_str) > 200:
                result_str = result_str[:200] + "......"
            flatten_list_items.extend([self.get_name_with_rich_text(attr), result_str])
            flatten_list_items_plain.extend([self.get_name_with_plain_text(attr), result_str])

        data.riches = flatten_list_items
        data.plains = flatten_list_items_plain
        data.selected.clear()

        self.data.set_list_view_multi_column_items(ui_listView, flatten_list_items, 2)



    def query_and_push(self, obj, propertyName, bPush, bRight): #bPush: whether add Breadcrumb nor not, call by property
        if bRight:
            ui_Label = self.ui_labelRight
            ui_listView = self.ui_detailListRight
            ui_breadcrumb = self.ui_hisObjsBreadcrumbRight
        else:
            ui_Label = self.ui_labelLeft
            ui_listView = self.ui_detailListLeft
            ui_breadcrumb = self.ui_hisObjsBreadcrumbLeft

        data = self.right if bRight else self.left

        data.attributes = Utils.ll(obj)

        data.filtered_attributes, data.filteredIndexToIndex = self.filter(data)
        self.show_data(data, ui_listView)

        # set breadcrumb
        if propertyName and len(propertyName) > 0:
            label = propertyName
        else:
            if isinstance(obj, unreal.Object):
                label = obj.get_name()
            else:
                try:
                    label = obj.__str__()
                except TypeError:
                    label = f"{obj}"

        if bPush: # push
            # print(f"%%% push: {propertyName}, label {label}")
            data.hisCrumbObjsAndNames.append((obj, propertyName))
            self.data.push_breadcrumb_string(ui_breadcrumb, label, label)

        self.data.set_text(ui_Label, "{}  type: {}".format(label, type(obj)) )

        crumbCount = self.data.get_breadcrumbs_count_string(ui_breadcrumb)
        if bRight:
            assert len(self.right.hisCrumbObjsAndNames) == crumbCount, "hisCrumbObjsAndNames count not match  {}  {}".format(len(self.right.hisCrumbObjsAndNames), crumbCount)
        else:
            assert len(self.left.hisCrumbObjsAndNames) == crumbCount, "hisCrumbObjsAndNames count not match  {}  {}".format(len(self.left.hisCrumbObjsAndNames), crumbCount)

        self.update_log_text(bRight)

    def clear_and_query(self, obj, bRight):
        # first time query
        self.data.clear_breadcrumbs_string(self.ui_hisObjsBreadcrumbRight if bRight else self.ui_hisObjsBreadcrumbLeft)
        if not self.right:
            self.right = DetailData()
        if not self.left:
            self.left = DetailData()

        data = self.right if bRight else self.left
        data.hisCrumbObjsAndNames = []  #clear his-Object at first time query
        if bRight:
            assert len(self.right.hisCrumbObjsAndNames) == 0, "len(self.right.hisCrumbObjsAndNames) != 0"
        else:
            assert len(self.left.hisCrumbObjsAndNames) == 0, "len(self.left.hisCrumbObjsAndNames) != 0"

        self.query_and_push(obj, "", bPush=True, bRight= bRight)
        self.apply_compare_if_needed()
        self.update_log_text(bRight)


    def update_ui_by_mode(self):
        self.data.set_is_checked(self.ui_checkbox_compare_mode, self.compareMode)
        self.data.set_is_checked(self.ui_checkbox_single_mode, not self.compareMode)

        bCollapsed = not self.compareMode
        self.data.set_collapsed(self.ui_rightButtonsGroup, bCollapsed)
        self.data.set_collapsed(self.ui_right_group, bCollapsed)
        self.data.set_collapsed(self.ui_button_refresh, bCollapsed)


    def on_checkbox_SingleMode_Click(self, state):
        self.compareMode = False
        self.update_ui_by_mode()

    def on_checkbox_CompareMode_Click(self, state):
        self.compareMode = True
        self.update_ui_by_mode()

    def on_button_Refresh_click(self):
        self.apply_compare_if_needed()


    def on_button_SelectAsset_click(self, bRightSide):
        selectedAssets = Utilities.Utils.get_selected_assets()
        if len(selectedAssets) == 0:
            return
        self.clear_and_query(selectedAssets[0], bRightSide)

    def on_button_QuerySelected_click(self, bRightSide):
        # query component when any component was selected, otherwise actor
        obj = Utilities.Utils.get_selected_comp()
        if not obj:
            obj = Utilities.Utils.get_selected_actor()
        if obj:
            self.clear_and_query(obj, bRightSide)

    def on_drop(self, bRightSide, *args, **kwargs):
        if "assets" in kwargs and kwargs["assets"]:
            asset = unreal.load_asset(kwargs["assets"][0])
            if asset:
                self.clear_and_query(asset, bRightSide)
                return
        if "actors" in kwargs and kwargs["actors"]:
            actor = unreal.PythonBPLib.find_actor_by_name(kwargs["actors"][0], unreal.EditorLevelLibrary.get_editor_world())
            if actor:
                print(actor)
                self.clear_and_query(actor, bRightSide)
                return
        item_count = 0
        for k, v in kwargs.items():
            item_count += len(v)
        if item_count == 0:
            selected_comp = Utilities.Utils.get_selected_comp()
            if selected_comp:
                self.clear_and_query(selected_comp, bRightSide)

    def log_r_warning(self):
        unreal.log_warning("Assign the global var: '_r' with the MenuItem: 'select X --> _r' on Python Icon menu")


    def on_button_Query_R_click(self, r_obj,  bRightSide=False):
        print("on_button_Query_R_click call")
        if not r_obj:
            return
        self.clear_and_query(r_obj, bRightSide)




    def on_list_double_click_do(self, index, bRight):
        # print ("on_listview_DetailList_mouse_button_double_click {}  bRight: {}".format(index, bRight))
        data = self.right if bRight else self.left

        typeBlacklist = [int, float, str, bool] #, types.NotImplementedType]

        real_index = data.filteredIndexToIndex[index] if data.filteredIndexToIndex else index
        assert 0 <= real_index < len(data.attributes)

        currentObj, _ = data.hisCrumbObjsAndNames[len(data.hisCrumbObjsAndNames) - 1]
        attr_name = data.attributes[real_index].name
        objResult, propertyName = self.try_get_object(data, currentObj, attr_name)

        if not objResult or objResult is currentObj: # equal
            return
        if isinstance(objResult, str) and "skip call" in objResult.lower():
            return
        if type(objResult) in typeBlacklist:
            return

        if isinstance(objResult, collections.abc.Iterable):
            if type(objResult[0]) in typeBlacklist:
                return
            nextObj = objResult[0]
            nextPropertyName = str(propertyName) + "[0]"
        else:
            nextObj = objResult
            nextPropertyName = str(propertyName)
        self.query_and_push(nextObj, nextPropertyName, bPush=True, bRight=bRight)
        self.apply_compare_if_needed()
        self.update_log_text(bRight)

    def on_listview_DetailListRight_mouse_button_double_click(self, index):
        self.on_list_double_click_do(index, bRight=True)

    def on_listview_DetailListLeft_mouse_button_double_click(self, index):
        self.on_list_double_click_do(index, bRight=False)

    def on_breadcrumbtrail_click_do(self, item, bRight):
        ui_hisObjsBreadcrumb = self.ui_hisObjsBreadcrumbRight if bRight else self.ui_hisObjsBreadcrumbLeft
        data = self.right if bRight else self.left
        count = self.data.get_breadcrumbs_count_string(ui_hisObjsBreadcrumb)
        print ("on_breadcrumbtrail_ObjectHis_crumb_click: {}    count: {}    len(data.hisCrumbObjsAndNames): {}".format(item, count, len(data.hisCrumbObjsAndNames)))
        while len(data.hisCrumbObjsAndNames) > count:
            data.hisCrumbObjsAndNames.pop()
        nextObj, name = data.hisCrumbObjsAndNames[len(data.hisCrumbObjsAndNames) - 1]
        if not bRight:
            assert self.left.hisCrumbObjsAndNames == data.hisCrumbObjsAndNames, "self.left.hisCrumbObjsAndNames = data.hisCrumbObjsAndNames"

        self.query_and_push(nextObj, name, bPush=False, bRight=False)
        self.apply_compare_if_needed()
        self.update_log_text(bRight=False)

    def on_breadcrumbtrail_ObjectHisLeft_crumb_click(self, item):
        self.on_breadcrumbtrail_click_do(item, bRight=False)

    def on_breadcrumbtrail_ObjectHisRight_crumb_click(self, item):
        self.on_breadcrumbtrail_click_do(item, bRight=True)

    def remove_address_str(self, strIn):
        return re.sub(r'\(0x[0-9,A-F]{16}\)', '', strIn)

    def apply_compare_if_needed(self):
        if not self.compareMode:
            return

        lefts  = self.left.filtered_attributes if self.left.filtered_attributes else self.left.attributes
        rights = self.right.filtered_attributes if self.right.filtered_attributes else self.right.attributes
        if not lefts:
            lefts = []
        if not rights:
            rights = []

        leftIDs = []
        rightIDs = []
        for i, left_attr in enumerate(lefts):
            for j, right_attr in enumerate(rights):
                if right_attr.name == left_attr.name:
                    if right_attr.result != left_attr.result:
                        if isinstance(right_attr.result, unreal.Transform):
                            if right_attr.result.is_near_equal(left_attr.result, location_tolerance=1e-20, rotation_tolerance=1e-20, scale3d_tolerance=1e-20):
                                continue
                        leftIDs.append(i)
                        rightIDs.append(j)
                        break

        self.data.set_list_view_multi_column_selections(self.ui_detailListLeft, leftIDs)
        self.data.set_list_view_multi_column_selections(self.ui_detailListRight, rightIDs)
        self.diff_count = len(leftIDs)


    def apply_search_filter(self, text, bRight):
        _data = self.right if bRight else self.left
        _data.filter_str = text if len(text) else ""
        _data.filtered_attributes, _data.filteredIndexToIndex = self.filter(_data)
        ui_listView = self.ui_detailListRight if bRight else self.ui_detailListLeft
        self.show_data(_data, ui_listView)
        self.apply_compare_if_needed()


    def on_searchbox_FilterLeft_text_changed(self, text):
        self.apply_search_filter(text if text is not None else "", bRight=False)
    def on_searchbox_FilterLeft_text_committed(self, text):
        self.apply_search_filter(text if text is not None else "", bRight=False)

    def on_searchbox_FilterRight_text_changed(self, text):
        self.apply_search_filter(text if text is not None else "", bRight=True)
    def on_searchbox_FilterRight_text_committed(self, text):
        self.apply_search_filter(text if text is not None else "", bRight=True)


    def apply_filter(self):
        _datas = [self.left, self.right]
        _isRight = [False, True]
        for data, bRight  in zip(_datas, _isRight):
            if len(data.hisCrumbObjsAndNames) > 0:
                nextObj, name  = data.hisCrumbObjsAndNames[len(data.hisCrumbObjsAndNames)-1]
                self.query_and_push(nextObj, name, bPush=False, bRight=bRight)
                self.apply_compare_if_needed()
        self.update_log_text(bRight=False) #


    def try_get_object(self, data, obj, name:str):
        index = -1
        attribute = None
        for i, attr in enumerate(data.attributes):
            if attr.name == name:
                index = i
                attribute = attr
        assert index >= 0
        return attribute.result, name


    def ui_on_checkbox_ShowBuiltin_state_changed(self, bEnabled):
        self.showBuiltin = bEnabled
        self.apply_filter()
    def ui_on_checkbox_ShowOther_state_changed(self, bEnabled):
        self.showOther = bEnabled
        self.apply_filter()
    def ui_on_checkbox_ShowProperties_state_changed(self, bEnabled):
        self.showProperties = bEnabled
        self.apply_filter()
    def ui_on_checkbox_ShowEditorProperties_state_changed(self, bEnabled):
        self.showEditorProperties = bEnabled
        self.apply_filter()
    def ui_on_checkbox_ShowParamFunction_state_changed(self, bEnabled):
        self.showParamFunction = bEnabled
        self.apply_filter()

    def ui_on_listview_DetailList_selection_changed(self, bRight):
        data = [self.left, self.right][bRight]
        list_view = [self.ui_detailListLeft, self.ui_detailListRight][bRight]

        selected_indices = set(self.data.get_list_view_multi_column_selection(list_view))
        added = selected_indices - data.selected
        de_selected = data.selected - selected_indices

        for i, lineId in enumerate(added):
            self.data.set_list_view_multi_column_line(list_view, lineId, data.get_plain(lineId, column_count=COLUMN_COUNT)
                                                      , rebuild_list=True if i == len(added)-1 and len(de_selected) == 0 else False)

        for i, lineId in enumerate(de_selected):
            self.data.set_list_view_multi_column_line(list_view, lineId, data.get_rich(lineId, column_count=COLUMN_COUNT)
                                                      , rebuild_list=True if i == len(de_selected)-1 else False)

        data.selected = selected_indices

