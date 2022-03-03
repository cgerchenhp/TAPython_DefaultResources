# -*- coding: utf-8 -*-
import unreal
import Utilities.Utils



def print_refs(packagePath):
    print("-" * 70)
    results, parentsIndex = unreal.PythonBPLib.get_all_refs(packagePath, True)
    print ("resultsCount: {}".format(len(results)))
    assert len(results) == len(parentsIndex), "results count not equal parentIndex count"
    print("{} Referencers Count: {}".format(packagePath, len(results)))

    def _print_self_and_children(results, parentsIndex, index, gen):
        if parentsIndex[index] < -1:
            return
        print ("{}{}".format("\t" * (gen +1), results[index]))
        parentsIndex[index] = -2
        for j in range(index + 1, len(parentsIndex), 1):
            if parentsIndex[j] == index:
                _print_self_and_children(results, parentsIndex, j, gen + 1)

    for i in range(len(results)):
        if parentsIndex[i] >= -1:
            _print_self_and_children(results, parentsIndex, i, 0)


def print_deps(packagePath):
    print("-" * 70)
    results, parentsIndex = unreal.PythonBPLib.get_all_deps(packagePath, True)
    print ("resultsCount: {}".format(len(results)))
    assert len(results) == len(parentsIndex), "results count not equal parentIndex count"
    print("{} Dependencies Count: {}".format(packagePath, len(results)))

    def _print_self_and_children(results, parentsIndex, index, gen):
        if parentsIndex[index] < -1:
            return
        print ("{}{}".format("\t" * (gen +1), results[index]))
        parentsIndex[index] = -2
        for j in range(index + 1, len(parentsIndex), 1):
            if parentsIndex[j] == index:
                _print_self_and_children(results, parentsIndex, j, gen + 1)

    for i in range(len(results)):
        if parentsIndex[i] >= -1:
            _print_self_and_children(results, parentsIndex, i, 0)


def print_related(packagePath):
    print_deps(packagePath)
    print_refs(packagePath)


def print_selected_assets_refs():
    assets = Utilities.Utils.get_selected_assets()
    for asset in assets:
        print_refs(asset.get_outermost().get_path_name())

def print_selected_assets_deps():
    assets = Utilities.Utils.get_selected_assets()
    for asset in assets:
        print_deps(asset.get_outermost().get_path_name())

def print_selected_assets_related():
    assets = Utilities.Utils.get_selected_assets()
    for asset in assets:
        print_related(asset.get_outermost().get_path_name())


def print_who_used_custom_depth():
    world = unreal.EditorLevelLibrary.get_editor_world()
    allActors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    print(len(allActors))
    errorCount = 0
    for actor in allActors:
        comps = actor.get_components_by_class(unreal.PrimitiveComponent)
        for comp in comps:
            if comp.render_custom_depth:
                errorCount += 1
            # v = comp.get_editor_property("custom_depth_stencil_value")
            # m = comp.get_editor_property("custom_depth_stencil_write_mask")
            print("actor: {} comp: {} enabled Custom depth ".format(actor.get_name(), comp.get_name()))
            #     errorCount += 1

    print("Custom Depth comps: {}".format(errorCount))