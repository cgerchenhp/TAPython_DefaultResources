# -*- coding: utf-8 -*-
import unreal
import sys
import pydoc
import inspect
import os
from enum import IntFlag


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def has_instance(cls):
        return cls in cls._instances

    def get_instance(cls):
        if cls in cls._instances:
            return cls._instances[cls]
        return None

def cast(object_to_cast, object_class):
    try:
        return object_class.cast(object_to_cast)
    except:
        return None



# short cut for print dir
def d(obj, subString=''):
    subString = subString.lower()
    for x in dir(obj):
        if subString == '' or subString in x.lower():
            print(x)


def l(obj, subString='', bPrint = True):
    '''
    输出物体详细信息：函数、属性，editorProperty等，并以log形式输出
    :param obj: Object实例或者类
    :param subString: 过滤用字符串
    :return: 无
    '''
    def _simplifyDoc(content):
        bracketS, bracketE = content.find('('), content.find(')')
        arrow = content.find('->')
        funcDocPos = len(content)
        endSign = ['--', '\n', '\r']
        for s in endSign:
            p = content.find(s)
            if p != -1 and p < funcDocPos:
                funcDocPos = p
        funcDoc = content[:funcDocPos]
        param = content[bracketS + 1: bracketE].strip()
        return funcDoc, param

    def _getEditorProperties(content, obj):
        lines = content.split('\r')
        signFound = False
        allInfoFound = False
        result = []
        for line in lines:
            if not signFound and '**Editor Properties:**' in line:
                signFound = True
            if signFound:
                #todo re
                nameS, nameE = line.find('``') + 2, line.find('`` ')
                if nameS == -1 or nameE == -1:
                    continue
                typeS, typeE = line.find('(') + 1, line.find(')')
                if typeS == -1 or typeE == -1:
                    continue
                rwS, rwE = line.find('[') + 1, line.find(']')
                if rwS == -1 or rwE == -1:
                    continue
                name = line[nameS: nameE]
                type = line[typeS: typeE]
                rws = line[rwS: rwE]
                descript = line[rwE + 2:]
                allInfoFound = True
                result.append((name, type, rws, descript))
        if signFound:
            if not allInfoFound:
                unreal.log_warning("not all info found {}".format(obj))
        else:
            unreal.log_warning("can't find editor properties in {}".format(obj))
        return result

    if obj == None:
        unreal.log_warning("obj == None")
        return None

    if inspect.ismodule(obj):
        return None
    ignoreList = ['__delattr__', '__getattribute__', '__hash__', '__init__', '__setattr__']

    propertiesNames = []
    builtinCallableNames = []
    otherCallableNames = []

    for x in dir(obj):
        if subString == '' or subString in x.lower():
            attr = getattr(obj, x)
            if callable(attr):
                if inspect.isbuiltin(attr): # or inspect.isfunction(attr) or inspect.ismethod(attr):
                    builtinCallableNames.append(x)
                else:
                    # Not Built-in
                    otherCallableNames.append(x)
            else:
                # Properties
                propertiesNames.append(x)

    # 1 otherCallables
    otherCallables = []
    for name in otherCallableNames:
        descriptionStr = ""
        if name == "__doc__":
            resultStr = "ignored.."  #doc太长，不输出
        else:
            resultStr = "{}".format(getattr(obj, name))
        otherCallables.append([name, (), descriptionStr, resultStr])

    # 2 builtinCallables
    builtinCallables = []
    for name in builtinCallableNames:
        attr = getattr(obj, name)
        descriptionStr = ""
        resultStr = ""
        bHasParameter = False
        if hasattr(attr, '__doc__'):
            docForDisplay, paramStr = _simplifyDoc(attr.__doc__)
            if paramStr == '':
                # Method with No params
                descriptionStr = docForDisplay[docForDisplay.find(')') + 1:]
                if '-> None' not in docForDisplay:
                    resultStr = "{}".format(attr.__call__())
                else:
                    resultStr = 'skip call'
            else:
                # 有参函数
                descriptionStr = paramStr
                bHasParameter  = True
                resultStr = ""
        else:
            pass
        builtinCallables.append([name, (bHasParameter,), descriptionStr, resultStr])

    # 3 properties
    editorPropertiesInfos = []
    editorPropertiesNames = []
    if hasattr(obj, '__doc__') and isinstance(obj, unreal.Object):
        editorPropertiesInfos = _getEditorProperties(obj.__doc__, obj)
        for name, _, _, _ in editorPropertiesInfos:
            editorPropertiesNames.append(name)

    properties = []
    for name in propertiesNames:
        descriptionStr = ""
        if name == "__doc__":
            resultStr = "ignored.."  #doc太长，不输出
        else:
            try:
                resultStr = "{}".format(getattr(obj, name))
            except:
                resultStr = ""

        isAlsoEditorProperty = name in editorPropertiesNames    #是否同时是EditorProprty同时也是property
        properties.append([name, (isAlsoEditorProperty,), descriptionStr, resultStr])

    # 4 editorProperties
    editorProperties = []
    propertyAlsoEditorPropertyCount = 0
    for info in editorPropertiesInfos:
        name, type, rw, descriptionStr = info
        if subString == '' or subString in name.lower():    #过滤掉不需要的
            try:
                value = eval('obj.get_editor_property("{}")'.format(name))
            except:
                value = ""
            descriptionStr = "[{}]".format(rw)
            resultStr = "{}".format(value)
            isAlsoProperty = name in propertiesNames
            if isAlsoProperty:
                propertyAlsoEditorPropertyCount += 1
            editorProperties.append( [name, (isAlsoProperty,), descriptionStr, resultStr])

    strs = []
    strs.append("Detail: {}".format(obj))
    formatWidth = 70
    for info in otherCallables:
        name, flags, descriptionStr, resultStr = info
        # line = "\t{} {}{}{}".format(name, descriptionStr, " " *(formatWidth -1 - len(name) - len(descriptionStr)), resultStr)
        line = "\t{} {}".format(name, descriptionStr)
        line += "{}{}".format(" " * (formatWidth-len(line)+1-4), resultStr)
        strs.append(line)
    for info in builtinCallables:
        name, flags, descriptionStr, resultStr = info
        if flags[0]:    # 有参函数
            # line = "\t{}({})    {} {}".format(name, descriptionStr, " " * (formatWidth - 5 - len(name) - len(descriptionStr)), resultStr)
            line = "\t{}({})".format(name, descriptionStr)
            line += "{}{}".format(" " * (formatWidth-len(line)+1-4), resultStr)
        else:
            # line = "\t{}()     {} |{}| {}".format(name, descriptionStr, "-" * (formatWidth - 7 - len(name) - len(descriptionStr)), resultStr)
            line = "\t{}()     {}".format(name, descriptionStr)
            line += "|{}| {}".format("-" * (formatWidth-len(line)+1-4-3), resultStr)
        strs.append(line)
    for info in properties:
        name, flags, descriptionStr, resultStr = info
        sign = "**" if flags[0] else ""
        # line = "\t\t{} {}     {}{}{}".format(name, sign, descriptionStr, " " * (formatWidth - 6 - len(name) -len(sign) - len(descriptionStr)), resultStr)
        line = "\t\t{} {}     {}".format(name, sign, descriptionStr)
        line += "{}{}".format(" " * (formatWidth-len(line)+2-8), resultStr)
        strs.append(line)
    strs.append("Special Editor Properties:")
    for info in editorProperties:
        name, flags, descriptionStr, resultStr = info
        if flags[0]:
            pass # 已经输出过跳过
        else:
            sign = "*"
            # line = "\t\t{0} {1}  {3}{4} {2}".format(name, sign, descriptionStr, " " * (formatWidth - 3 - len(name) -len(sign) ), resultStr)    #descriptionStr 中是[rw]放到最后显示
            line = "\t\t{} {}".format(name, sign)
            line += "{}{}   {}".format(" " * (formatWidth-len(line)+2-8), resultStr, descriptionStr)  # descriptionStr 中是[rw]放到最后显示
            strs.append(line)

    if bPrint:
        for l in strs:
            print(l)
        print("'*':Editor Property, '**':Editor Property also object attribute.")
        print("{}: matched, builtinCallable: {}  otherCallables: {}  prop: {}  EditorProps: {}  both: {}".format(obj
            , len(builtinCallables), len(otherCallables), len(properties), len(editorProperties), propertyAlsoEditorPropertyCount))

    return otherCallables, builtinCallables, properties, editorProperties


# short cut for print type
def t(obj):
    print(type(obj))

# unreal type to Python dict
def ToJson(v):
    tp = type(v)
    if tp == unreal.Transform:
        result = {'translation': ToJson(v.translation), 'rotation': ToJson(v.rotation), 'scale3d': ToJson(v.scale3d)}
        return result
    elif tp == unreal.Vector:
        return {'x': v.x, 'y': v.y, 'z': v.z}
    elif tp == unreal.Quat:
        return {'x': v.x, 'y': v.y, 'z': v.z, 'w': v.w}
    else:
        print("Error type: " + str(tp) + " not implemented.")
        return None

def get_selected_comps():
    return unreal.PythonBPLib.get_selected_components()

def get_selected_comp():
    comps = unreal.PythonBPLib.get_selected_components()
    return comps[0] if len(comps) > 0 else None

def get_selected_asset():
    selected = unreal.PythonBPLib.get_selected_assets_paths()
    if selected:
        return unreal.load_asset(unreal.PythonBPLib.get_selected_assets_paths()[0])
    else:
        return None

def get_selected_assets():
    assets = []
    for path in unreal.PythonBPLib.get_selected_assets_paths():
        asset = unreal.load_asset(path)
        if (asset != None):
            assets.append(asset)
    return assets

def get_selected_actors():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_selected_level_actors()


def get_selected_actor():
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_selected_level_actors()
    return actors[0] if len(actors) > 0 else None

def set_preview_es31():
    unreal.PythonBPLib.set_preview_platform("GLSL_ES3_1_ANDROID", "ES3_1")

def set_preview_sm5():
    unreal.PythonBPLib.set_preview_platform("", "SM5")




# todo: create export tools for create help/dir to file

def export_dir(filepath, cls):
    f = open(filepath, 'w')
    sys.stdout = f
    for x in sorted(dir(cls)):
        print(x)
    sys.stdout = sys.__stdout__
    f.close()

def export_help(filepath, cls):
    f = open(filepath, 'w')
    sys.stdout = f
    pydoc.help(cls)
    sys.stdout = sys.__stdout__
    f.close()



# 修改site.py 文件中的Encoding
def set_default_encoding(encodingStr):

    pythonPath = os.path.dirname(sys.path[0])
    if not os.path.exists(pythonPath):
        unreal.PythonBPLib.message_dialog("can't find python folder: {}".format(pythonPath), "Warning")
        return
    sitePyPath = pythonPath + "/Lib/site.py"
    if not os.path.exists(sitePyPath):
        unreal.PythonBPLib.message_dialog("can't find site.py: {}".format(sitePyPath), "Warning")
        return
#简单查找字符串替换
    with open(sitePyPath, "r") as f:
        lines = f.readlines()
        startLine = -1
        endLine = -1
        for i in range(len(lines)):
            if startLine == -1 and lines[i][:len('def setencoding():')] == 'def setencoding():':
                startLine = i
                continue
            if endLine == -1 and startLine > -1 and  lines[i].startswith('def '):
                endLine = i
        print("startLine: {}  endLine: {}".format(startLine, endLine))

        changedLineCount = 0
        if -1 < startLine and startLine < endLine:
            linePosWithIf = []
            for i in range(startLine + 1, endLine):
                if lines[i].lstrip().startswith('if '):
                    linePosWithIf.append(i)
                    print(lines[i])
            if len(linePosWithIf) != 4:
                unreal.PythonBPLib.message_dialog("Find pos failed: {}".format(sitePyPath), "Warning")
                print(linePosWithIf)
                return
            lines[linePosWithIf[2]] = lines[linePosWithIf[2]].replace("if 0", "if 1") # 简单修改第三个if所在行的内容
            changedLineCount += 1
            for i in range(linePosWithIf[2] + 1, linePosWithIf[3]):
                line = lines[i]
                if "encoding=" in line.replace(" ", ""):
                    s = line.find('"')
                    e = line.find('"', s+1)
                    if s > 0 and e > s:
                        lines[i] = line[:s+1] + encodingStr + line[e:]
                        changedLineCount += 1
                        break

    if changedLineCount == 2:
        with open(sitePyPath, 'w') as f:
            f.writelines(lines)
        unreal.PythonBPLib.notification("Success: {}".format(sitePyPath), 0)
        currentEncoding = sys.getdefaultencoding()
        if currentEncoding == encodingStr:
            unreal.PythonBPLib.notification("已将default encoding设置为{}".format(currentEncoding), 0)
        else:
            unreal.PythonBPLib.message_dialog("已将default encoding设置为{}，需要重启编辑器以便生效".format(encodingStr), "Warning")
    else:
        unreal.PythonBPLib.message_dialog("Find content failed: {}".format(sitePyPath), "Warning")



def get_actors_at_location(location, error_tolerance):
    allActors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_selected_level_actors()
    result = [_actor for _actor in allActors if _actor.get_actor_location().is_near_equal(location, error_tolerance)]
    return result

def select_actors_at_location(location, error_tolerance, actorTypes=None):
    actors = get_actors_at_location(location, error_tolerance)
    if len(actors) > 1:
        print("Total {} actor(s) with the same locations.".format(len(actors)))
        if actorTypes is not None:
            actors = [actor for actor in actors if type(actor) in actorTypes]
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).set_selected_level_actors(actors)
        return actors
    else:
        print("None actor with the same locations.")
        return []

def select_actors_with_same_location(actor, error_tolerance):
    if actor is not None:
        actors = select_actors_at_location(actor.get_actor_location(), error_tolerance, [unreal.StaticMeshActor, unreal.SkeletalMeshActor])
        return actors
    else:
        print("actor is None.")
        return []


def get_chameleon_tool_instance(json_name):
    found_count = 0
    result = None
    for var in globals():
        if hasattr(var, "jsonPath")  and hasattr(var, "data"):
            if isinstance(var.data, unreal.ChameleonData):
                if var.jsonPath.endswith(json_name):
                    found_count += 1
                    result = var
    if found_count == 1:
        return result
    if found_count > 1:
        unreal.log_warning(f"Found Multi-ToolsInstance by name: {json_name}, count: {found_count}")

    return None




#
#   Flags describing an object instance
#
class EObjectFlags(IntFlag):
    # Do not add new flags unless they truly belong here. There are alternatives.
	# if you change any the bit of any of the RF_Load flags, then you will need legacy serialization
	RF_NoFlags					= 0x00000000,	#< No flags, used to avoid a cast

	# This first group of flags mostly has to do with what kind of object it is. Other than transient, these are the persistent object flags.
	# The garbage collector also tends to look at these.
	RF_Public					=0x00000001,	#< Object is visible outside its package.
	RF_Standalone				=0x00000002,	#< Keep object around for editing even if unreferenced.
	RF_MarkAsNative				=0x00000004,	#< Object (UField) will be marked as native on construction (DO NOT USE THIS FLAG in HasAnyFlags() etc)
	RF_Transactional			=0x00000008,	#< Object is transactional.
	RF_ClassDefaultObject		=0x00000010,	#< This object is its class's default object
	RF_ArchetypeObject			=0x00000020,	#< This object is a template for another object - treat like a class default object
	RF_Transient				=0x00000040,	#< Don't save object.

	# This group of flags is primarily concerned with garbage collection.
	RF_MarkAsRootSet			=0x00000080,	#< Object will be marked as root set on construction and not be garbage collected, even if unreferenced (DO NOT USE THIS FLAG in HasAnyFlags() etc)
	RF_TagGarbageTemp			=0x00000100,	#< This is a temp user flag for various utilities that need to use the garbage collector. The garbage collector itself does not interpret it.

	# The group of flags tracks the stages of the lifetime of a uobject
	RF_NeedInitialization		=0x00000200,	#< This object has not completed its initialization process. Cleared when ~FObjectInitializer completes
	RF_NeedLoad					=0x00000400,	#< During load, indicates object needs loading.
	RF_KeepForCooker			=0x00000800,	#< Keep this object during garbage collection because it's still being used by the cooker
	RF_NeedPostLoad				=0x00001000,	#< Object needs to be postloaded.
	RF_NeedPostLoadSubobjects	=0x00002000,	#< During load, indicates that the object still needs to instance subobjects and fixup serialized component references
	RF_NewerVersionExists		=0x00004000,	#< Object has been consigned to oblivion due to its owner package being reloaded, and a newer version currently exists
	RF_BeginDestroyed			=0x00008000,	#< BeginDestroy has been called on the object.
	RF_FinishDestroyed			=0x00010000,	#< FinishDestroy has been called on the object.

	# Misc. Flags
	RF_BeingRegenerated			=0x00020000,	#< Flagged on UObjects that are used to create UClasses (e.g. Blueprints) while they are regenerating their UClass on load (See FLinkerLoad::CreateExport()), as well as UClass objects in the midst of being created
	RF_DefaultSubObject			=0x00040000,	#< Flagged on subobjects that are defaults
	RF_WasLoaded				=0x00080000,	#< Flagged on UObjects that were loaded
	RF_TextExportTransient		=0x00100000,	#< Do not export object to text form (e.g. copy/paste). Generally used for sub-objects that can be regenerated from data in their parent object.
	RF_LoadCompleted			=0x00200000,	#< Object has been completely serialized by linkerload at least once. DO NOT USE THIS FLAG, It should be replaced with RF_WasLoaded.
	RF_InheritableComponentTemplate = 0x00400000, #< Archetype of the object can be in its super class
	RF_DuplicateTransient		=0x00800000,	#< Object should not be included in any type of duplication (copy/paste, binary duplication, etc.)
	RF_StrongRefOnFrame			=0x01000000,	#< References to this object from persistent function frame are handled as strong ones.
	RF_NonPIEDuplicateTransient	=0x02000000,	#< Object should not be included for duplication unless it's being duplicated for a PIE session
	RF_Dynamic                  =0x04000000,	#< Field Only. Dynamic field. UE_DEPRECATED(5.0, "RF_Dynamic should no longer be used. It is no longer being set by engine code.") - doesn't get constructed during static initialization, can be constructed multiple times  # @todo: BP2CPP_remove
	RF_WillBeLoaded				=0x08000000,	#< This object was constructed during load and will be loaded shortly
	RF_HasExternalPackage		=0x10000000,	#< This object has an external package assigned and should look it up when getting the outermost package

	# RF_Garbage and RF_PendingKill are mirrored in EInternalObjectFlags because checking the internal flags is much faster for the Garbage Collector
	# while checking the object flags is much faster outside of it where the Object pointer is already available and most likely cached.
	# RF_PendingKill is mirrored in EInternalObjectFlags because checking the internal flags is much faster for the Garbage Collector
	# while checking the object flags is much faster outside of it where the Object pointer is already available and most likely cached.

	RF_PendingKill              = 0x20000000,	#< Objects that are pending destruction (invalid for gameplay but valid objects).  UE_DEPRECATED(5.0, "RF_PendingKill should not be used directly. Make sure references to objects are released using one of the existing engine callbacks or use weak object pointers.")  This flag is mirrored in EInternalObjectFlags as PendingKill for performance
	RF_Garbage                  =0x40000000,	#< Garbage from logical point of view and should not be referenced.  UE_DEPRECATED(5.0, "RF_Garbage should not be used directly. Use MarkAsGarbage and ClearGarbage instead.")  This flag is mirrored in EInternalObjectFlags as Garbage for performance
	RF_AllocatedInSharedPage	=0x80000000,	#< Allocated from a ref-counted page shared with other UObjects


class EMaterialValueType(IntFlag):
	MCT_Float1		= 1,
	MCT_Float2		= 2,
	MCT_Float3		= 4,
	MCT_Float4		= 8,
	MCT_Texture2D	          = 1 << 4,
	MCT_TextureCube	          = 1 << 5,
	MCT_Texture2DArray		  = 1 << 6,
	MCT_TextureCubeArray      = 1 << 7,
	MCT_VolumeTexture         = 1 << 8,
	MCT_StaticBool            = 1 << 9,
	MCT_Unknown               = 1 << 10,
	MCT_MaterialAttributes	  = 1 << 11,
	MCT_TextureExternal       = 1 << 12,
	MCT_TextureVirtual        = 1 << 13,
	MCT_VTPageTableResult     = 1 << 14,

	MCT_ShadingModel		  = 1 << 15,
	MCT_Strata				  = 1 << 16,
	MCT_LWCScalar			  = 1 << 17,
	MCT_LWCVector2			  = 1 << 18,
	MCT_LWCVector3			  = 1 << 19,
	MCT_LWCVector4			  = 1 << 20,
	MCT_Execution             = 1 << 21,
	MCT_VoidStatement         = 1 << 22,