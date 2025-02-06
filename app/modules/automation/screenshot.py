import ctypes
import math

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
        # 排除缩放干扰
        ctypes.windll.user32.SetProcessDPIAware()

    @staticmethod
    def get_window(title):
        hwnd = win32gui.FindWindow(None, title)  # 获取窗口句柄
        if hwnd:
            # logger.info(f"找到窗口‘{title}’的句柄为：{hwnd}")
            return hwnd
        else:
            logger.error(f"未找到窗口: {title}")
            return None

    def take_screenshot(self, window_name, crop=(0,0,1,1)):
        """
        截取特定区域
        :param window_name: 需要截图的窗口名
        :param crop: 截取区域, 格式为 (crop_left, crop_top, crop_right, crop_bottom)，范围是0到1之间，表示相对于窗口的比例
        :return:
        """
        hwnd = self.get_window(window_name)
        # 获取带标题的窗口尺寸
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        w = right - left
        h = bottom - top

        # 获取设备上下文
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        # 创建位图对象
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
        save_dc.SelectObject(bitmap)

        # 进行截图
        user32 = ctypes.windll.user32
        # 这里必须要是2,0和1都是黑屏，2: 捕捉包括窗口的边框、标题栏以及整个窗口的内容
        user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)  # PW_RENDERFULLCONTENT=2

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
        # 计算裁剪区域裁剪图像
        crop_left = int(crop[0] * w)
        crop_top = int(crop[1] * h)
        crop_right = int(crop[2] * w)
        crop_bottom = int(crop[3] * h)
        img_cropped = img[crop_top:crop_bottom, crop_left:crop_right]

        #缩放图像以自适应分辨率图像识别
        scale_x = round(self.base_width/w,3)
        scale_y = round(self.base_height/h,3)
        img_resized = cv2.resize(img_cropped, (int(img_cropped.shape[1]*scale_x), int(img_cropped.shape[0]*scale_y)))

        return img_resized


if __name__ == '__main__':
    # 替换成你的游戏窗口标题
    game_window = "尘白禁区"
    screen = Screenshot()
    screenshot = screen.take_screenshot(game_window,(0.5,0.5,1,1))

    if screenshot is not None:
        cv2.imshow("Game Screenshot", screenshot)
        cv2.waitKey(0)
        cv2.destroyAllWindows()