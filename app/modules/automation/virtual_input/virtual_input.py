import string
import win32api
import win32con
import threading
from ctypes import windll
from ctypes.wintypes import HWND

class VirtualInput:
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
            if not hasattr(VirtualInput, "_instance"):
                with VirtualInput._instance_lock:
                    if not hasattr(VirtualInput, "_instance"):
                        VirtualInput._instance = object.__new__(cls)  
            return VirtualInput._instance

    def __init__(self):
        self.__hwnd = None

    def __getitem__(self, key):
        key = key.upper()
        if not "VK_" in key:
            key = "VK_" + key
        printable = key.split("_")[1]
        if len(printable) == 1 and printable in string.printable:
            return windll.user32.VkKeyScanA(ord(printable)) & 0xff
        else:
            return getattr(win32con, key)

    @property   
    def hwnd(self) -> HWND:
        return self.__hwnd
    
    @hwnd.setter
    def hwnd(self, value: HWND) -> None:
        self.__hwnd = value
        
    def key_down(self, key: str) -> int:
        vk_code = self.__getitem__(key)
        scan_code = windll.user32.MapVirtualKeyW(vk_code, 0)
        # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-keydown
        wparam = vk_code
        lparam = (scan_code << 16) | 1
        code = win32api.SendMessage(self.__hwnd, win32con.WM_KEYDOWN, wparam, lparam)
        return code

    def key_up(self, key: str) -> int:
        vk_code = self.__getitem__(key)
        scan_code = windll.user32.MapVirtualKeyW(vk_code, 0)
        # https://docs.microsoft.com/en-us/windows/win32/inputdev/wm-keyup
        wparam = vk_code
        lparam = (scan_code << 16) | 0XC0000001
        code = win32api.SendMessage(self.__hwnd, win32con.WM_KEYUP, wparam, lparam)
        return code