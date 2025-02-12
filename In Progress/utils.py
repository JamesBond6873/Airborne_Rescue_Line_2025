# -------- Utilities -------- 
import time


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
            return time_val[0][0] == "True"
        else:
            return False