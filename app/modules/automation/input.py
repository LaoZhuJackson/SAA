import pyautogui


class Input:
    def __init__(self):
        pass

    def mouse_click(self, x, y):
        """单击"""
        pass

    def move_click(self, x, y):
        """先瞬移，再单击（尘白特供）"""
        pass

    def double_click(self, x, y):
        """双击"""
        pass

    def mouse_down(self, key):
        """鼠标不移动，原地按下key键"""
        pass

    def mouse_up(self, key):
        """鼠标不移动，原地松开key键"""
        pass

    def move_down(self, x, y, key):
        """鼠标移动到（x,y）后按下key键"""
        pass

    def move_up(self, x, y, key):
        """鼠标移动到（x,y）后松开key键"""
        pass

    def mouse_scroll(self, count, direction=-1, pause=True):
        """
        滚动鼠标滚轮，方向和次数由参数指定
        :param count: 滚动次数
        :param direction: 每次滚动长度，正数表示向上滚动。负数向下
        :param pause:
        :return:
        """
        # for _ in range(count):
        #     pyautogui.scroll(direction, _pause=pause)
        # self.logger.debug(f"滚轮滚动 {count * direction} 次")
        pass

    def press_key(self, key, wait_time=0.2):
        """模拟键盘按键长按"""
        pass

    def key_down(self, key):
        """在屏幕上的（x，y）位置执行鼠标点击操作"""
        # try:
        #     pydirectinput.keyDown(key)
        #     self.logger.debug(f"键盘按下 {key}")
        # except Exception as e:
        #     self.logger.error(f"键盘按下 {key} 出错：{e}")
        pass

    def key_up(self, key):
        """在屏幕上的（x，y）位置执行鼠标点击操作"""
        # try:
        #     pydirectinput.keyUp(key)
        #     self.logger.debug(f"键盘松开 {key}")
        # except Exception as e:
        #     self.logger.error(f"键盘松开 {key} 出错：{e}")
        pass