import ctypes
from ctypes import wintypes, WINFUNCTYPE, POINTER, byref

# 定义钩子回调函数类型
HOOKPROC = WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

# 定义消息结构
class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT)
    ]

# 钩子回调函数
@HOOKPROC
def hook_callback(nCode, wParam, lParam):
    if nCode >= 0:
        msg = ctypes.cast(lParam, POINTER(MSG)).contents
        hwnd = msg.hwnd
        message = msg.message
        wParam = msg.wParam
        lParam = msg.lParam
        print(f"Message: {message}, hwnd: {hwnd}, wParam: {wParam}, lParam: {lParam}")
    return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

# 获取目标窗口句柄和线程 ID
def get_window_thread_id(window_title):
    hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
    if hwnd == 0:
        raise Exception(f"Window with title '{window_title}' not found")
    thread_id = wintypes.DWORD()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, byref(thread_id))
    return hwnd, thread_id.value

# 设置钩子
def set_hook(hwnd, thread_id):
    hook_id = ctypes.windll.user32.SetWindowsHookExW(
        4,  # 钩子类型
        hook_callback,           # 钩子回调函数
        ctypes.windll.kernel32.GetModuleHandleW(None),  # 当前模块句柄
        thread_id                # 目标线程 ID
    )
    if hook_id == 0:
        raise Exception("Failed to set hook")
    return hook_id

# 消息循环
def run_message_loop():
    msg = MSG()
    while ctypes.windll.user32.GetMessageW(byref(msg), 0, 0, 0) != 0:
        ctypes.windll.user32.TranslateMessage(byref(msg))
        ctypes.windll.user32.DispatchMessageW(byref(msg))

# 卸载钩子
def remove_hook(hook_id):
    ctypes.windll.user32.UnhookWindowsHookEx(hook_id)

# 示例：监听特定窗口
if __name__ == "__main__":
    window_title = "尘白禁区"  # 替换为目标窗口的标题
    hwnd, thread_id = get_window_thread_id(window_title)
    hook_id = set_hook(hwnd, thread_id)
    try:
        run_message_loop()
    finally:
        remove_hook(hook_id)