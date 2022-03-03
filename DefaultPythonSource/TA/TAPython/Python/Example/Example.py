# -*- coding: utf-8 -*-
import unreal

def do_some_things(*args, **kwargs):
    unreal.log("do_some_things start:")
    for arg in args:
        unreal.log(arg)
    unreal.log("do_some_things end.")