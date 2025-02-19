import cv2
import numpy as np

from app.common.config import config

upper_yellow = np.array([int(value) for value in config.LineEdit_fish_upper.value.split(',')])
lower_yellow = np.array([int(value) for value in config.LineEdit_fish_lower.value.split(',')])
print(upper_yellow)
print(lower_yellow)


from PIL import Image
import pyautogui
import win32gui


class Screenshot:
    @staticmethod
    def is_application_fullscreen(window):
        """
        判断是否全屏
        :param window: 游戏窗口
        :return:
        """
        screen_width, screen_height = pyautogui.size()
        return (window.width, window.height) == (screen_width, screen_height)

    @staticmethod
    def get_window_real_resolution(window):
        left, top, right, bottom = win32gui.GetClientRect(window._hWnd)
        return right - left, bottom - top

    @staticmethod
    def get_window_region(window):
        """
        获取窗口区域
        :param window: 游戏窗口
        :return:
        """
        if Screenshot.is_application_fullscreen(window):
            return window.left, window.top, window.width, window.height
        else:
            real_width, real_height = Screenshot.get_window_real_resolution(window)
            other_border = (window.width - real_width) // 2
            up_border = window.height - real_height - other_border
            return window.left + other_border, window.top + up_border, window.width - other_border - other_border, window.height - up_border - other_border

    @staticmethod
    def get_window(title):
        """
        获取窗口
        :param title: 窗口名
        :return:
        """
        windows = pyautogui.getWindowsWithTitle(title)
        if windows:
            window = windows[0]
            return window
        return False

    @staticmethod
    def take_screenshot(title, crop=(0, 0, 1, 1)):
        """
        截图窗口区域
        :param title: 窗口名
        :param crop: 截图的裁剪区域。
        :return:
        """
        window = Screenshot.get_window(title)
        if window:
            left, top, width, height = Screenshot.get_window_region(window)

            screenshot = pyautogui.screenshot(region=(
                int(left + width * crop[0]),
                int(top + height * crop[1]),
                int(width * crop[2]),
                int(height * crop[3])
            ))

            real_width, _ = Screenshot.get_window_real_resolution(window)
            if real_width > 1920:
                screenshot_scale_factor = 1920 / real_width
                screenshot = screenshot.resize((int(1920 * crop[2]), int(1080 * crop[3])))
            else:
                screenshot_scale_factor = 1

            screenshot_pos = (
                int(left + width * crop[0]),
                int(top + height * crop[1]),
                int(width * crop[2] * screenshot_scale_factor),
                int(height * crop[3] * screenshot_scale_factor)
            )
            # 预览截图
            # screenshot.show()

            return screenshot, screenshot_pos, screenshot_scale_factor

        return False


def count_yellow_blocks(image):
    # 黄色的确切HSV值
    """计算图像中黄色像素的数量"""
    # 将图像转换为HSV颜色空间
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 创建黄色掩膜
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    # mask_white = cv2.inRange(hsv, self.lower_white, self.upper_white)

    # 查找轮廓
    contours_yellow, _ = cv2.findContours(mask_yellow, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    print(f"黄色块数为：{len(contours_yellow)}")

    return len(contours_yellow)

# screenshot = Screenshot()
# i,_,_ = screenshot.take_screenshot('尘白禁区',crop=(1130 / 1920, 240 / 1080, 370 / 1920, 330 / 1080))
i = cv2.imread('../app/resource/images/fishing/test.png')
# i = cv2.imread('../app/resource/images/fishing/test_day.png')
print(type(i))
# img_np = np.array(i)
# print(type(img_np))

count_yellow_blocks(image=i)