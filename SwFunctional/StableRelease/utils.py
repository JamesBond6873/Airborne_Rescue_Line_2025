# -------- Utilities -------- 

import time
import numpy as np


print("Utilities: \t \t \t OK")

# Makes printDebug dependent on DEBUG flag
def printDebug(text, debug):
    if debug:
        print(text)


class Timer:
    def __init__(self):
        self.__timer_arr = np.array([["none", 1, 0, 0]])

    def remove_timer(self, name):
        self.__timer_arr = self.__timer_arr[np.where(self.__timer_arr[:, 0] != name)]

    def set_timer(self, name, set_time):
        self.remove_timer(name)
        self.__timer_arr = np.append(self.__timer_arr, [[name, time.perf_counter(), set_time, False]], axis=0)

    def __update_timer(self):
        for i, timer in enumerate(self.__timer_arr):
            if not timer[0] == "none":
                self.__timer_arr[i, 3] = (time.perf_counter() - float(timer[1])) > float(timer[2])

    def get_timer(self, name):
        self.__update_timer()
        time_val = self.__timer_arr[np.where(self.__timer_arr[:, 0] == name), 3]

        if time_val.size > 0:
            #print(f'CHECK ME_------------------------ {time_val[0][0] == True}')
            return time_val[0][0] == "True"
        else:
            return False


class TimerManager:
    def __init__(self):
        self.timers = {}  # Dictionary to store timers

    def add_timer(self, name, duration):
        #Add a new timer with a given name and duration (in seconds).
        self.timers[name] = {"start_time": time.perf_counter(), "duration": duration}

    def remove_timer(self, name):
        #Remove a timer by name if it exists.
        if name in self.timers:
            del self.timers[name]

    def update_timer_duration(self, name, new_duration):
        #Update the duration of an existing timer.
        if name in self.timers:
            self.timers[name]["duration"] = new_duration

    def set_timer(self, name, new_duration):
        if name in self.timers:
            self.timers[name]["start_time"] = time.perf_counter()
            self.timers[name]["duration"] = new_duration

    def is_timer_expired(self, name):
        #Check if a timer has expired.
        if name in self.timers:
            elapsed_time = time.perf_counter() - self.timers[name]["start_time"]
            return elapsed_time >= self.timers[name]["duration"]
        return False  # If the timer doesn't exist, return False

    def reset_timer(self, name):
        #Reset the timer start time while keeping the same duration.
        if name in self.timers:
            self.timers[name]["start_time"] = time.perf_counter()

    def get_remaining_time(self, name):
        #Get the remaining time until the timer expires.
        if name in self.timers:
            elapsed_time = time.perf_counter() - self.timers[name]["start_time"]
            return self.timers[name]["duration"] - elapsed_time
        return None  # Timer doesn't exist

    def clear_all_timers(self):
        # Force all timers to expire immediately by setting their duration to 0.
        for timer in self.timers.values():
            #print(f"here: {timer}")
            timer["duration"] = 0

