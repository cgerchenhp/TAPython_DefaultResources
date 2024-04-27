# -*- coding: utf-8 -*-
import logging

import unreal
import inspect
import types
import Utilities
from collections import Counter


class attr_detail(object):
    def __init__(self, obj,  name:str):
        self.name = name

        attr = None
        self.bCallable = None
        self.bCallable_builtin = None

        try:
            if hasattr(obj, name):
                attr = getattr(obj, name)
                self.bCallable = callable(attr)
                self.bCallable_builtin = inspect.isbuiltin(attr)
        except Exception as e:
            unreal.log(str(e))



        self.bProperty = not self.bCallable
        self.result = None
        self.param_str = None
        self.bEditorProperty = None
        self.return_type_str = None
        self.doc_str = None
        self.property_rw = None

        if self.bCallable:
            self.return_type_str = ""

        if self.bCallable_builtin:
            if hasattr(attr, '__doc__'):
                docForDisplay, paramStr = _simplifyDoc(attr.__doc__)
                # print(f"~~~~~ attr: {self.name}  docForDisplay: {docForDisplay}  paramStr: {paramStr}")
                # print(attr.__doc__)

                try:
                    sig = inspect.getfullargspec(getattr(obj, self.name))
                    # print("+++ ", sig)

                    args = sig.args
                    argCount = len(args)
                    if "self" in args:
                        argCount -= 1
                except TypeError:
                    argCount = -1

                if "-> " in docForDisplay:
                    self.return_type_str = docForDisplay[docForDisplay.find(')') + 1:]
                else:
                    self.doc_str = docForDisplay[docForDisplay.find(')') + 1:]

                if argCount == 0 or (argCount == -1 and (paramStr == '' or paramStr == 'self')):
                    # Method with No params

                    if '-> None' not in docForDisplay or self.name in ["__reduce__", "_post_init"]:
                        try:
                            if name == "get_actor_time_dilation" and isinstance(obj, unreal.Object):
                                # call get_actor_time_dilation will crash engine if actor is get from CDO and has no world.
                                if obj.get_world():
                                    # self.result = "{}".format(attr.__call__())
                                    self.result = attr.__call__()
                                else:
                                    self.result = "skip call, world == None."
                            else:
                                # self.result = "{}".format(attr.__call__())
                                self.result = attr.__call__()
                        except:
                            self.result = "skip call.."
                    else:
                        print(f"docForDisplay: {docForDisplay}, self.name: {self.name}")
                        self.result = "skip call."
                else:
                    self.param_str = paramStr
                    self.result = ""
            else:
                logging.error("Can't find p")
        elif self.bCallable_other:
            if hasattr(attr, '__doc__'):
                if isinstance(attr.__doc__, str):
                    docForDisplay, paramStr = _simplifyDoc(attr.__doc__)

            if name in ["__str__", "__hash__", "__repr__", "__len__"]:
                try:
                    self.result = "{}".format(attr.__call__())
                except:
                    self.result = "skip call."
            else:
                # self.result = "{}".format(getattr(obj, name))
                self.result = getattr(obj, name)

    def post(self, obj):
        if self.bOtherProperty and not self.result:
            try:
                self.result = getattr(obj, self.name)
            except:
                self.result = "skip call..."



    def apply_editor_property(self, obj, type_, rws, descript):
        self.bEditorProperty = True
        self.property_rw = "[{}]".format(rws)

        try:
            self.result = eval('obj.get_editor_property("{}")'.format(self.name))
        except:
            self.result = "Invalid"



    def __str__(self):
        s = f"Attr: {self.name}  paramStr: {self.param_str}  desc: {self.return_type_str} result: {self.result}"
        if self.bProperty:
            s += ", Property"
        if self.bEditorProperty:
            s += ", Eidtor Property"
        if self.bOtherProperty:
            s += ", Other Property "
        if self.bCallable:
            s += ", Callable"
        if self.bCallable_builtin:
            s += ", Callable_builtin"
        if self.bCallable_other:
            s += ", bCallable_other"
        if self.bHasParamFunction:
            s+= ", bHasParamFunction"
        return s


    def check(self):
        counter = Counter([self.bOtherProperty, self.bEditorProperty, self.bCallable_other, self.bCallable_builtin])
        # print("counter: {}".format(counter))
        if counter[True] == 2:
            unreal.log_error(f"{self.name}: {self.bEditorProperty}, {self.bOtherProperty} {self.bCallable_builtin} {self.bCallable_other}")


    @property
    def bOtherProperty(self):
        if self.bProperty and not self.bEditorProperty:
            return True
        return False

    @property
    def bCallable_other(self):
        if self.bCallable and not self.bCallable_builtin:
            return True
        return False

    @property
    def display_name(self, bRichText=True):
        if self.bProperty:
            return f"\t{self.name}"
        else:
            # callable
            if self.param_str:
                return f"\t{self.name}({self.param_str})    {self.return_type_str}"
            else:
                if self.bCallable_other:
                    return f"\t{self.name}"  # __hash__, __class__, __eq__ 等
                else:
                    return f"\t{self.name}()    {self.return_type_str}"

    @property
    def display_result(self) -> str:
        if self.bEditorProperty:
            return "{}    {}".format(self.result, self.property_rw)
        else:
            return "{}".format(self.result)

    @property
    def bHasParamFunction(self):
        return self.param_str and len(self.param_str) != 0





def ll(obj):

    if not obj:
        return None
    if inspect.ismodule(obj):
        return None

    result = []
    for x in dir(obj):
        attr = attr_detail(obj, x)
        result.append(attr)


    if hasattr(obj, '__doc__') and isinstance(obj, unreal.Object):
        editorPropertiesInfos = _getEditorProperties(obj.__doc__, obj)
        for name, type_, rws, descript in editorPropertiesInfos:
            # print(f"~~ {name} {type} {rws}, {descript}")

            index = -1
            for i, v in enumerate(result):
                if v.name == name:
                    index = i
                    break
            if index != -1:
                this_attr = result[index]
            else:
                this_attr = attr_detail(obj, name)
                result.append(this_attr)
                # unreal.log_warning(f"Can't find editor property: {name}")

            this_attr.apply_editor_property(obj, type_, rws, descript)

    for i, attr in enumerate(result):
        attr.post(obj)

    return result


def _simplifyDoc(content):
    def next_balanced(content, s="(", e = ")" ):
        s_pos = -1
        e_pos = -1
        balance = 0
        for index, c in enumerate(content):
            match = c == s or c == e
            if not match:
                continue
            balance += 1 if c == s else -1
            if c == s and balance == 1 and s_pos == -1:
                s_pos = index
            if c == e and balance == 0 and s_pos != -1 and e_pos == -1:
                e_pos = index
                return s_pos, e_pos
        return -1, -1

    # bracketS, bracketE = content.find('('), content.find(')')
    if not content:
        return "", ""
    bracketS, bracketE = next_balanced(content, s='(', e = ')')
    arrow = content.find('->')
    funcDocPos = len(content)
    endSign = ['--', '\n', '\r']
    for s in endSign:
        p = content.find(s)
        if p != -1 and p < funcDocPos:
            funcDocPos = p
    funcDoc = content[:funcDocPos]
    if bracketS != -1 and bracketE != -1:
        param = content[bracketS + 1: bracketE].strip()
    else:
        param = ""
    return funcDoc, param


def _getEditorProperties(content, obj):
    # print("Content: {}".format(content))

    lines = content.split('\r')
    signFound = False
    allInfoFound = False
    result = []
    for line in lines:
        if not signFound and '**Editor Properties:**' in line:
            signFound = True
        if signFound:
            #todo re
            # nameS, nameE = line.find('``') + 2, line.find('`` ')
            nameS, nameE = line.find('- ``') + 4, line.find('`` ')
            if nameS == -1 or nameE == -1:
                continue
            typeS, typeE = line.find('(') + 1, line.find(')')
            if typeS == -1 or typeE == -1:
                continue
            rwS, rwE = line.find('[') + 1, line.find(']')
            if rwS == -1 or rwE == -1:
                continue
            name = line[nameS: nameE]
            type_str = line[typeS: typeE]
            rws = line[rwS: rwE]
            descript = line[rwE + 2:]
            allInfoFound = True
            result.append((name, type_str, rws, descript))
            # print(name, type, rws)
    if signFound:
        if not allInfoFound:
            unreal.log_warning("not all info found {}".format(obj))
    else:
        unreal.log_warning("can't find editor properties in {}".format(obj))
    return result


def log_classes(obj):
    print(obj)
    print("\ttype: {}".format(type(obj)))
    print("\tget_class: {}".format(obj.get_class()))
    if type(obj.get_class()) is unreal.BlueprintGeneratedClass:
        generatedClass = obj.get_class()
    else:
        generatedClass = unreal.PythonBPLib.get_blueprint_generated_class(obj)
        print("\tgeneratedClass: {}".format(generatedClass))
    print("\tbp_class_hierarchy_package: {}".format(unreal.PythonBPLib.get_bp_class_hierarchy_package(generatedClass)))

def is_selected_asset_type(types):
    selectedAssets = Utilities.Utils.get_selected_assets()
    for asset in selectedAssets:
        if type(asset) in types:
            return True;
    return False



