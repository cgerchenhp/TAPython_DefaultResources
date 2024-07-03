import json
from enum import Enum, auto
import inspect
from typing import Callable, Union

from concurrent.futures import ThreadPoolExecutor, Future
from threading import Lock

import logging

import unreal

logger = logging.getLogger(__name__)


class FuncType(Enum):
    STATIC_METHOD = auto()
    CLASS_METHOD = auto()
    LAMBDA = auto()
    UNBOUND_METHOD = auto()
    INSTANCE_METHOD = auto()
    INSTANCE_METHOD_OF_CLASS = auto()
    STATIC_FUNCTION = auto()
    BUILTIN = auto()
    UNKNOWN = auto()


def get_func_type(callback: callable, cls=None) -> FuncType:
    if isinstance(callback, staticmethod):
        return FuncType.STATIC_METHOD

    if not callable(callback):
        raise ValueError("callback must be a callable object")

    if cls:
        for _, obj in cls.__dict__.items():
            if obj is callback:
                if isinstance(obj, staticmethod):
                    return FuncType.STATIC_METHOD
                elif isinstance(obj, classmethod):
                    return FuncType.CLASS_METHOD
                break
    elif isinstance(callback, staticmethod):
        return FuncType.STATIC_METHOD

    if hasattr(callback, "__name__") and callback.__name__ == "<lambda>":
        return FuncType.LAMBDA

    if inspect.ismethod(callback):
        if callback.__self__ is None:
            return FuncType.UNBOUND_METHOD
        elif isinstance(callback.__self__, type):
            return FuncType.CLASS_METHOD
        else:
            return FuncType.INSTANCE_METHOD

    if inspect.isfunction(callback):
        params_names = list(inspect.signature(callback).parameters.keys())
        if params_names and params_names[0] == "self":
            return FuncType.INSTANCE_METHOD_OF_CLASS
        return FuncType.STATIC_FUNCTION

    if inspect.isbuiltin(callback):
        return FuncType.BUILTIN

    return FuncType.UNKNOWN



class ChameleonTaskExecutor:
    """
    ChameleonTaskExecutor is a class for managing and executing tasks in parallel.
    It uses a ThreadPoolExecutor to run tasks concurrently.
    """
    def __init__(self, owner):
        """
        Initialize the ChameleonTaskExecutor with the owner of the tasks.
        """
        assert isinstance(owner.data, unreal.ChameleonData)
        self.owner = owner
        self.executor = ThreadPoolExecutor()
        self.futures_dict = {}
        self.lock = Lock()

    @staticmethod
    def _find_var_name_in_outer(target_var, by_type:bool=False)->str:
        frames = inspect.getouterframes(inspect.currentframe())
        top_frame = frames[-1]
        instance_name_in_global = ""
        for k, v in top_frame.frame.f_globals.items():
            if by_type:
                if isinstance(v, target_var):
                    # print(f"!! found: {k} @ frame: frame count: {len(frames)}")
                    instance_name_in_global = k
                    break
                if type(v) == target_var:
                    # print(f"!! found: {k} @ frame: frame count: {len(frames)}")
                    instance_name_in_global = k
                    break
            else:
                if v == target_var:
                    # print(f"!! found: {k} @ frame: frame count: {len(frames)}")
                    instance_name_in_global = k
                    break
        return instance_name_in_global

    @staticmethod
    def _number_of_param(callback)->int:
        try:
            if isinstance(callback, str):
                param_str = callback[callback.find("("): callback.find(")") + 1].strip()
                return param_str[1:-1].find(",")
            else:
                sig = inspect.signature(callback)
                param_count = len(sig.parameters)
                return param_count
        except Exception as e:
            print(e)
            return 0

    @staticmethod
    def _get_balanced_bracket_code(content, file_name, lineno):
        def _is_brackets_balanced(content):
            v = 0
            for c in content:
                if c == "(":
                    v += 1
                elif c == ")":
                    v -= 1
            return v == 0

        if "(" in content and _is_brackets_balanced(content):
            return content
        try:
            with open(file_name, 'r', encoding="utf-8") as f:
                lines = f.readlines()

                line = ""
                for i in range(lineno-1, len(lines)):
                    line += lines[i].strip()
                    if "(" in line and _is_brackets_balanced(line):
                        return line
        except Exception as e:
            raise RuntimeError(f"Failed to process file {file_name} line {lineno} : {e}")
        
        return None

    @staticmethod
    def get_cmd_str_from_callable(callback: Union[callable, str]) -> str:
        """Get the command string from a callable object. The command string is used to call the callable object"""
        if isinstance(callback, str):
            return callback
        callback_type = get_func_type(callback)
        if callback_type == FuncType.BUILTIN:
            return "{}(%)".format(callback.__qualname__)
        elif callback_type == FuncType.LAMBDA:
            raise ValueError("Lambda function is not supported")
        else:
            frames = inspect.getouterframes(inspect.currentframe())

            last_callable_frame_idx = -1
            for i, frame in enumerate(frames):
                for var_name, var_value in frame.frame.f_locals.items():
                    if callable(var_value) and hasattr(var_value, "__code__"):
                        if var_value.__code__ == callback.__code__:
                            last_callable_frame_idx = i

            # The upper frame of the last callable frame is the frame that contains the callback,
            # so we can get the code context of the callback from the upper frame
            upper_frame = frames[last_callable_frame_idx + 1] if len(frames) > last_callable_frame_idx + 1 else None

            code_context = "".join(upper_frame.code_context)
            code_line = ChameleonTaskExecutor._get_balanced_bracket_code(code_context, upper_frame.filename, upper_frame.lineno)

            callback_params = code_line[code_line.index("(") + 1: code_line.rfind(")")].split(",")

            callback_param = ""
            for param in callback_params:
                if callback.__name__ in param:
                    callback_param = param if "=" not in param else param[param.index('=')+1:]
                    break

            if callback_param:
                # found
                if callback_type == FuncType.INSTANCE_METHOD or callback_param.startswith("self."):
                    instance_name = ChameleonTaskExecutor._find_var_name_in_outer(upper_frame.frame.f_locals["self"])
                    cmd = f"{instance_name}.{callback_param[callback_param.index('.') + 1:]}(%)"
                else:
                    cmd = f"{callback_param}(%)"
                return cmd
        return f"{callback.__qualname__}(%)"




    def submit_task(self, task:Callable, args=None, kwargs=None, on_finish_callback: Union[Callable, str] = None)-> int:
        """
        Submit a task to be executed. The task should be a callable object.
        Args and kwargs are optional arguments to the task.
        Callback is an optional function to be called when the task is done.
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        future = self.executor.submit(task, *args, **kwargs)
        assert future is not None, "future is None"
        future_id = id(future)
        with self.lock:
            self.futures_dict[future_id] = future

            cmd = ChameleonTaskExecutor.get_cmd_str_from_callable(on_finish_callback)
            param_count = ChameleonTaskExecutor._number_of_param(on_finish_callback)

            cmd = cmd.replace("%", str(future_id) if param_count else "")

            def _func(_future):
                unreal.PythonBPLib.exec_python_command(cmd, force_game_thread=True)

            future.add_done_callback(_func)

        unreal.log(f"submit_task callback cmd: {cmd}, param_count: {param_count}")

        return future_id

    def get_future(self, future_id)-> Future:
        with self.lock:
            return self.futures_dict.get(future_id, None)

    def get_task_is_running(self, future_id)-> bool:
        future = self.get_future(future_id)
        if future is not None:
            return future.running()
        return False

    def is_any_task_running(self):
        for future_id in self.futures_dict.keys():
            if self.get_task_is_running(future_id):
                return True
        return False