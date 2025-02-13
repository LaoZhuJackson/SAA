import functools
import math
import threading
import time
import traceback

import cv2
import win32gui

from app.common.config import config
from app.common.image_utils import ImageUtils
from app.common.logger import logger
from app.common.singleton import SingletonMeta
from app.common.utils import random_rectangle_point
from app.modules.automation.input import Input
from app.modules.automation.screenshot import Screenshot
from app.modules.automation.timer import Timer
from app.modules.ocr import ocr


def atoms(func):
    """
    用于各种原子操作中实现立即停止的装饰器
    :param func:
    :return:
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 检查self.running是否为false
        if not args[0].running:
            raise Exception("break")
        else:
            # 判断是否暂停
            if  args[0].pause:
                # 每次执行完原子函数后，等待外部条件重新开始
                args[0].pause_event.wait()  # 等待外部触发继续执行
        return func(*args, **kwargs)
    return wrapper


class Automation:
    """
    自动化管理类，用于管理与游戏窗口相关的自动化操作。
    """
    # _screenshot_interval = Timer(0.1)

    def __init__(self,window_title,window_class,logger):
        """
        :param window_title: 游戏窗口的标题。
        :param window_class: 是启动器还是游戏窗口
        :param logger: 用于记录日志的Logger对象，可选参数。
        """
        # 启动器截图和操作的窗口句柄不同
        self.screenshot_hwnd = None
        self.window_title = window_title
        self.window_class = window_class
        self.is_starter = window_class != config.LineEdit_game_class.value
        self.logger = logger
        self.hwnd = self.get_hwnd()
        self.img_cache = {}
        self.screenshot = Screenshot(self.logger)
        # 当前截图
        self.current_screenshot = None
        # 保存状态机的第一张截图，为了让current_screenshot可以肆无忌惮的裁切
        self.first_screenshot = None
        self.scale_x = 1
        self.scale_y = 1
        self.relative_pos = None
        self.ocr_result = None

        self.running = True
        self.pause = False
        self.pause_event = threading.Event()  # 用来控制暂停

        self._init_input()


    def _init_input(self):
        self.input_handler = Input(self.hwnd, self.logger)
        # 鼠标部分
        self.move_click = self.input_handler.move_click
        self.mouse_click = self.input_handler.mouse_click
        self.mouse_down = self.input_handler.mouse_down
        self.mouse_up = self.input_handler.mouse_up
        self.mouse_scroll = self.input_handler.mouse_scroll
        self.move_to = self.input_handler.move_to
        # 按键部分
        self.press_key = self.input_handler.press_key
        self.key_down = self.input_handler.key_down
        self.key_up = self.input_handler.key_up

    def enumerate_child_windows(self,parent_hwnd):
        def callback(handle, windows):
            windows.append(handle)
            return True

        child_windows = []
        win32gui.EnumChildWindows(parent_hwnd, callback, child_windows)
        return child_windows

    def get_hwnd(self):
        """根据传入的窗口名和类型确定可操作的句柄"""
        hwnd = win32gui.FindWindow(None, self.window_title)
        handle_list = []
        if hwnd:
            handle_list.append(hwnd)
            self.screenshot_hwnd = hwnd
            handle_list.extend(self.enumerate_child_windows(hwnd))
            for handle in handle_list:
                class_name = win32gui.GetClassName(handle)
                if class_name == self.window_class:
                    # 找到需要的窗口句柄
                    self.logger.info(f"找到窗口 {self.window_title} 的句柄为：{handle}")
                    return handle
        else:
            raise ValueError(f"未找到{self.window_title}的句柄，请确保对应窗口已打开")

    @atoms
    def take_screenshot(self,crop=(0,0,1,1)):
        """
        捕获游戏窗口的截图。
        :param crop: 截图的裁剪区域，格式为(x1, y1, width, height)，默认为全屏。
        :return: 成功时返回截图及其位置和缩放因子，失败时抛出异常。
        """
        timeout = Timer(0.5, count=3).start()
        while True:
            try:
                result = self.screenshot.screenshot(self.screenshot_hwnd, crop, self.is_starter)
                if result:
                    self.current_screenshot,self.scale_x,self.scale_y,self.relative_pos = result
                    self.first_screenshot = self.current_screenshot
                    # self.logger.debug(f"缩放比例为：({self.scale_x},{self.scale_y})")
                    return result
                else:
                    # 为none的时候已经在screenshot中log了，此处无需再log
                    self.current_screenshot = None
                if timeout.reached():
                    raise RuntimeError("截图超时")
            except Exception as e:
                print(traceback.format_exc())
                self.logger.error(f"截图失败：{e}")
                break  # 退出循环

    def calculate_positions(self,template,max_loc):
        """
        找到图片后计算相对位置，input_handler接收的均为相对窗口的相对坐标，所以这里要返回的也是相对坐标
        :param template:
        :param max_loc:
        :return:
        """
        try:
            channels, width, height = template.shape[::-1]
        except:
            width, height = template.shape[::-1]
        # print(f"{max_loc=}")
        # print(f"{width=},{height=},{self.scale_x=},{self.scale_y=}")

        # scale_x = base_width/window_width,max_loc是经过统一尺度后从区域截图中获得的坐标，需要把尺度转回去再加上self.relative_pos
        top_left = (
            int(max_loc[0] / self.scale_x + self.relative_pos[0]),
            int(max_loc[1] / self.scale_y + self.relative_pos[1]),
        )
        bottom_right = (
            top_left[0] + int(width / self.scale_x),
            top_left[1] + int(height / self.scale_y),
        )
        # print(f"{top_left=}")
        # print(f"{bottom_right=}")
        return top_left, bottom_right


    def find_image_element(self,target,threshold,cacheable=True):
        """
        寻找图像
        :param target: 图片路径
        :param threshold: 置信度
        :param cacheable: 是否存入内存
        :return: 左上，右下相对坐标，寻找到的目标的置信度
        """
        try:
            if target in self.img_cache:
                mask = self.img_cache[target]['mask']
                template = self.img_cache[target]['template']
            else:
                # 获取透明部分的掩码（允许模版图像有透明处理）
                mask = ImageUtils.get_template_mask(target)
                template = cv2.imread(target)  # 读取模板图片
                if cacheable:
                    # 存入字典缓存
                    self.img_cache[target] = {'mask': mask, 'template': template}
            if mask is not None:
                matchVal,matchLoc = ImageUtils.match_template(self.current_screenshot, template, self.hwnd, mask)
            else:
                matchVal, matchLoc = ImageUtils.match_template(self.current_screenshot, template, self.hwnd)
            self.logger.info(f"目标图片：{target.replace('app/resource/images/', '')} 相似度：{matchVal:.2f}")
            if not math.isinf(matchVal) and (threshold is None or matchVal >= threshold):
                top_left, bottom_right = self.calculate_positions(template,matchLoc)
                return top_left, bottom_right, matchVal
            self.logger.debug(f"没有找到相似度大于 {threshold} 的结果")
        except Exception as e:
            self.logger.error(f"寻找图片出错：{e}")
        return None, None, None

    @atoms
    def perform_ocr(self,extract):
        """执行OCR识别，并更新OCR结果列表。如果未识别到文字，保留ocr_result为一个空列表。"""
        try:
            self.ocr_result = ocr.run(self.current_screenshot, extract)
            if not self.ocr_result:
                self.logger.error(f"未识别出任何文字")
                self.ocr_result = []
        except Exception as e:
            self.logger.error(f"OCR识别失败：{e}")
            self.ocr_result = []  # 确保在异常情况下，ocr_result为列表类型

    def calculate_text_position(self,result):
        """
        计算文本所在的相对位置
        :param result: 格式=['适龄提示', 1.0, [[10.0, 92.0], [71.0, 106.0]]],单条结果
        :return: 左上，右下相对坐标
        """
        result_pos = result[2]
        result_width = result_pos[1][0] - result_pos[0][0]
        result_height = result_pos[1][1] - result_pos[0][1]

        # self.relative_pos格式：(800, 480, 1600, 960),转回用户尺度后再加相对窗口坐标
        top_left = (
            self.relative_pos[0] + result_pos[0][0] / self.scale_x,
            self.relative_pos[1] + result_pos[0][1] / self.scale_x
        )
        bottom_right = (
            top_left[0] + int(result_width / self.scale_x),
            top_left[1] + int(result_height / self.scale_y),
        )
        # print(f"{top_left=}")
        # print(f"{bottom_right=}")
        return top_left, bottom_right
        

    def is_text_match(self, text, targets, include):
        """
        判断文本是否符合搜索条件，并返回匹配的文本。
        :param text: OCR识别出的文本。
        :param targets: 目标文本列表。
        :param include: 是否包含目标字符串。
        :return: (是否匹配, 匹配的目标文本)
        """
        if include:
            for target in targets:
                if target in text:
                    return True, target  # 直接返回匹配成功及匹配的目标文本
            return False, None  # 如果没有匹配，返回False和None
        else:
            return text in targets, text if text in targets else None

    def search_text_in_ocr_results(self, targets, include):
        for result in self.ocr_result:
            match,matched_text = self.is_text_match(result[0], targets, include)
            if match:
                self.matched_text = matched_text  # 更新匹配的文本变量
                self.logger.info(f"目标文字：{matched_text} 相似度：{result[1]:.2f}")
                return self.calculate_text_position(result)
        self.logger.info(f"目标文字：{', '.join(targets)} 未找到匹配文字")
        return None, None

    def find_text_element(self,target,include,need_ocr=True,extract=None):
        """

        :param target:
        :param include:
        :param need_ocr:
        :param extract: 是否提取文字，[(文字rgb颜色),threshold数值]
        :return:
        """
        target_texts = [target] if isinstance(target, str) else list(target)  # 确保目标文本是列表格式
        if need_ocr:
            self.perform_ocr(extract)
        return self.search_text_in_ocr_results(target_texts, include)


    @atoms
    def find_element(self,target,find_type:str,threshold:float=0.7,crop:tuple=(0,0,1,1),take_screenshot=False,include:bool=True,need_ocr:bool=True,extract:list=None):
        top_left = bottom_right = image_threshold = None
        if take_screenshot:
            # 调用take_screenshot更新self.current_screenshot,self.scale_x,self.scale_y,self.relative_pos
            screenshot_result = self.take_screenshot(crop)
            if not screenshot_result:
                return None
        else:
            # 不截图的时候做相应的裁切，使外部可以不写参数
            if self.current_screenshot is not None:
                # 更新当前裁切后的截图和相对位置坐标
                self.current_screenshot,self.relative_pos = ImageUtils.resize_screenshot(self.hwnd,self.first_screenshot,crop,self.is_starter)
                # ImageUtils.show_ndarray(self.current_screenshot,'show_current')
            else:
                self.logger.error(f"当前没有current_screenshot,裁切失败")
        if find_type in ['image', 'text', 'image_threshold']:
            if find_type == 'image':
                top_left, bottom_right, image_threshold = self.find_image_element(target,threshold)
            elif find_type == 'text':
                top_left, bottom_right = self.find_text_element(target, include, need_ocr, extract)
            if top_left and bottom_right:
                if find_type == 'image_threshold':
                    return image_threshold
                return top_left,bottom_right
        else:
            raise ValueError(f"错误的类型{find_type}")

    def click_element_with_pos(self,coordinates,action="move_click",offset=(0,0)):
        # 范围内正态分布取点
        x,y = random_rectangle_point(coordinates)
        print(f"{x=},{y=}")
        # 加上手动设置的偏移量
        click_x = x + offset[0]
        click_y = y + offset[1]
        # 动作到方法的映射
        action_map = {
            "mouse_click": self.mouse_click,
            "down": self.mouse_down,
            "move": self.move_to,
            "move_click": self.move_click,
        }
        if action in action_map:
            action_map[action](click_x,click_y)
        else:
            raise ValueError(f"未知的动作类型: {action}")
        return True

    def click_element(self,target,find_type:str,threshold:float=0.7,crop:tuple=(0,0,1,1),take_screenshot=False,include:bool=True,need_ocr:bool=True,extract:list=None,action:str='move_click',offset:tuple=(0, 0)):
        """
        寻找目标位置，并在位置做出对应action
        :param target: 寻找目标
        :param find_type: 寻找类型
        :param threshold: 置信度
        :param crop: 截图区域，take_screenshot为任何值crop都生效，为true时直接得到裁剪后的截图，为false时将根据crop对current_screenshot进行二次裁剪
        :param take_screenshot: 是否截图
        :param include: 是否允许target含于ocr结果
        :param need_ocr: 是否ocr
        :param extract: 是否使截图转换成白底黑字，只有find_type=="text"且需要ocr的时候才生效，[(文字rgb颜色),threshold数值]
        :param action: 默认假后台点击，可选'mouse_click','mouse_down','move','move_click'
        :param offset: 点击位置偏移量，默认不偏移
        :return:
        """
        coordinates = self.find_element(target,find_type,threshold,crop,take_screenshot,include,need_ocr,extract)
        # print(f"{coordinates=}")
        if coordinates:
            return self.click_element_with_pos(coordinates,action,offset)
        return False

    def stop(self):
        self.running = False

    def pause(self):
        self.pause = True
        # 清除事件，线程会暂停
        self.pause_event.clear()

    def resume(self):
        self.pause = False
        # 设置事件，线程会继续
        self.pause_event.set()

# 用于保存是否已实例化
auto_starter = None
auto_game = None

def instantiate_automation(auto_type:str):
    global auto_starter, auto_game

    # 尝试实例化 starter
    if auto_type == 'starter':
        try:
            auto_starter = Automation(config.LineEdit_starter_name.value, config.LineEdit_starter_class.value, logger)
        except Exception as e:
            logger.warn(f"未能成功实例化starter：{e}")

    elif auto_type == 'game':
        try:
            auto_game = Automation(config.LineEdit_game_name.value, config.LineEdit_game_class.value, logger)
        except Exception as e:
            logger.warn(f"未能成功实例化game：{e}")
    else:
        try:
            auto_starter = Automation(config.LineEdit_starter_name.value, config.LineEdit_starter_class.value, logger)
        except Exception as e:
            logger.warn(f"未能成功实例化starter：{e}")
        try:
            auto_game = Automation(config.LineEdit_game_name.value, config.LineEdit_game_class.value, logger)
        except Exception as e:
            logger.warn(f"未能成功实例化game：{e}")


# 调用实例化方法
instantiate_automation('all')

if __name__ == '__main__':
    pass