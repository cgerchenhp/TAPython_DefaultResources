import time

import unreal

from Utilities.Utils import Singleton
from Utilities.ChameleonTaskExecutor import ChameleonTaskExecutor


class MinimalAsyncTaskExample(metaclass=Singleton):
    def __init__(self, json_path:str):
        self.json_path = json_path
        self.data:unreal.ChameleonData = unreal.PythonBPLib.get_chameleon_data(self.json_path)

        self.executor = ChameleonTaskExecutor(self)

        self.ui_text_block = "TextBlock"
        self.ui_throbber = "Throbber"


    def slow_async_task(self, seconds:float) -> float:
        # This slow asynchronous task may involve operations such as file I/O, web requests, or other time-consuming activities.
        # Operations involving Unreal Engine assets must be executed on the main thread, NOT within this function. Use unreal.ScopedSlowTask(seconds) and we can have a progress bar.
        #
        # DON'T modify any Slate widget in this function, as it's running in a different thread.
        # The Unreal Engine enforces restrictions on accessing Slate widgets from threads other than the main game thread. 
        # Refer to SlateGlobals.h: #define SLATE_CROSS_THREAD_CHECK() checkf(IsInGameThread() || IsInSlateThread(), TEXT("Access to Slate is restricted to the GameThread or the SlateLoadingThread!"));

        print(f"instance_fake_task started, it will cost {seconds} second(s).")
        time.sleep(seconds)
        print(f"instance_fake_task finished., {seconds}s")
        
        return seconds


    def show_busy_icon(self, b_busy:bool):
        if b_busy:
            self.data.set_text(self.ui_text_block, f"Running Task.")
            self.data.set_visibility(self.ui_throbber, "Visible")
        else:
            self.data.set_text(self.ui_text_block, f"All tasks finished.")
            self.data.set_visibility(self.ui_throbber, "Collapsed")
        
    
    def add_slow_task(self, seconds:float):
        # modify Slate widget in this function, as it's running in the main thread.
        self.show_busy_icon(True)
        self.executor.submit_task(self.slow_async_task, args=[seconds], on_finish_callback=self.on_task_finish)


    def on_task_finish(self, future_id:int):
        # This function will be called in the main thread. so it's safe to modify Slate widget here.
        future = self.executor.get_future(future_id)
        if future is None:
            unreal.log_warning(f"Can't find future: {future_id}")
        else:
            self.data.set_text(self.ui_text_block, f"Task done, result: {future.result()}")
            if not self.executor.is_any_task_running():
                self.show_busy_icon(False)

        print(f"on_task_finish. Future: {future_id}, result: {future.result()}")


    def some_slow_tasks(self):
        self.show_busy_icon(True)
        self.executor.submit_task(self.slow_async_task, args=[2], on_finish_callback=self.on_task_finish)
        self.executor.submit_task(self.slow_async_task, args=[3], on_finish_callback=self.on_task_finish)

