import ctypes
import win32gui
import win32ui
import win32con
import numpy as np
import cv2

from app.common.logger import logger


class Screenshot:
    def __init__(self):
        self.base_width = 1920
        self.base_height = 1080

    def get_game_scale_ratio(self,game_window_name:str):
        """
        获取游戏窗口的分辨率并计算缩放比例，用于自适应游戏窗口大小图像识别
        :param game_window_name: 游戏窗口名(非启动器)
        :return:
        """
        hwnd = win32gui.FindWindow(None, game_window_name)
        if hwnd:
            rect = win32gui.GetClientRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            return self.base_width / width, self.base_height / height
        else:
            logger.error(f"没有找到游戏窗口: {game_window_name}")

    def resize_image(self, image, target_size):
        """
        将图像缩放到指定大小
        :param image:
        :param target_size:
        :return:
        """
        # cv2.INTER_AREA：区域插值，适合缩小图像。
        return cv2.resize(image, target_size, interpolation=cv2.INTER_LINEAR)

    @staticmethod
    def get_dpi():
        """ 调用 Windows API 函数获取缩放比例，用于正确截取启动器大小画面 """
        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            dpi = user32.GetDpiForSystem()
            # print(dpi)
            return dpi
        except Exception as e:
            logger.error("获取缩放比例时出错:", e)
            return 96

    def take_screenshot(self, window_name, crop=(0,0,1,1), dpi_scale: bool = False):
        """
        截取特定区域
        :param window_name: 需要截图的窗口名
        :param crop: 截取区域, 格式为 (crop_left, crop_top, crop_right, crop_bottom)，范围是0到1之间，表示相对于窗口的比例
        :param dpi_scale: 截取启动器时需要用到，启动器会受系统dpi缩放的影响
        :return:
        """
        hwnd = win32gui.FindWindow(None, window_name)  # 获取窗口句柄
        if not hwnd:
            logger.error(f"未找到窗口: {window_name}")
            return None

        # 获取窗口尺寸
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        w = right - left
        h = bottom - top

        if dpi_scale:
            # 获取 DPI 缩放因子
            dpi = self.get_dpi()
            scale_factor = dpi / 96  # 96 是 100% DPI 的标准值

            # 根据 DPI 缩放因子调整截图尺寸
            w = int(w * scale_factor)
            h = int(h * scale_factor)
            # print(f"Adjusted width: {w}, Adjusted height: {h}")

        # 计算裁剪区域
        crop_left = int(crop[0] * w)
        crop_top = int(crop[1] * h)
        crop_right = int(crop[2] * w)
        crop_bottom = int(crop[3] * h)

        # 获取设备上下文
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        # 创建位图对象
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, crop_right - crop_left, crop_bottom - crop_top)
        save_dc.SelectObject(bitmap)

        # 进行截图，直接在截图时指定裁剪区域
        save_dc.BitBlt((0, 0), (crop_right - crop_left, crop_bottom - crop_top), mfc_dc, (crop_left, crop_top),
                       win32con.SRCCOPY)

        # 转换为 numpy 数组
        bmpinfo = bitmap.GetInfo()
        bmpstr = bitmap.GetBitmapBits(True)
        img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4))

        # 释放资源
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)

        # OpenCV 处理
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img


if __name__ == '__main__':
    # 替换成你的游戏窗口标题
    game_window = "西山居启动器-尘白禁区"
    screen = Screenshot()
    screenshot = screen.take_screenshot(game_window,(0.5,0.5,1,1), True)

    if screenshot is not None:
        cv2.imshow("Game Screenshot", screenshot)
        cv2.waitKey(0)
        cv2.destroyAllWindows()