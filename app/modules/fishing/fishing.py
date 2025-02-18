import os
import time
from datetime import datetime

import cv2
import numpy as np

from app.common.config import config
from app.common.image_utils import ImageUtils
from app.modules.automation.timer import Timer
from app.modules.base_task.base_task import BaseTask


class FishingModule(BaseTask):
    def __init__(self):
        super().__init__()
        self.bite_time = None
        self.start_time = None
        self.is_use_time_judge = None
        self.previous_yellow_block_count = 0
        self.previous_pixels = 0
        self.save_path = os.path.abspath("./fish")
        self.press_key = None
        self.upper_yellow = None
        self.lower_yellow = None
        self.no_key = False

    def run(self):
        # 每次钓鱼前更新各种设置参数
        self.upper_yellow = np.array([int(value) for value in config.LineEdit_fish_upper.value.split(',')])
        self.lower_yellow = np.array([int(value) for value in config.LineEdit_fish_lower.value.split(',')])
        self.press_key = config.LineEdit_fish_key.value
        self.is_use_time_judge = config.CheckBox_is_limit_time.value
        self.start_time = time.time()

        if np.any(self.upper_yellow < self.lower_yellow):
            self.logger.error("运行错误，存在上限的值小于下限")
            return

        for i in range(config.SpinBox_fish_times.value):
            self.logger.info(f"开始第 {i + 1} 次钓鱼")
            self.enter_fish()
            self.start_fish()
            self.after_fish()


    def enter_fish(self):
        timeout = Timer(15).start()
        enter_flag = False
        while True:
            self.auto.take_screenshot()

            if self.auto.find_element(['饵','重量级','巨型','万能','普通','豪华','至尊'],'text',crop=(1658/1920,770/1080,1892/1920,829/1080)):
                enter_flag = True
            if enter_flag:
                # 还没甩竿
                if not self.is_spin_rod():
                    self.auto.press_key(self.press_key)
                    time.sleep(2)
                    continue
                # 甩杆后
                if self.auto.find_element('上钩了', 'text', crop=(787 / 1920, 234 / 1080, 1109 / 1920, 420 / 1080)):
                    self.auto.press_key(self.press_key)
                    self.bite_time = time.time()
                    time.sleep(0.2)
                    break
            if self.auto.find_element(['目标','今日'],'text',crop=(0,957/1080,460/1920,1)):
                self.auto.press_key('esc')
                time.sleep(0.5)
                continue
            if self.auto.find_element('使用','text',crop=(1405/1920,654/1080,1503/1920,747/1080)):
                self.auto.press_key('f')
                time.sleep(1)
                continue

            if timeout.reached():
                self.logger.error("进入钓鱼超时")
                break

    def start_fish(self):
        timeout = Timer(60).start()
        while True:
            self.auto.take_screenshot(crop=(1130 / 1920, 240 / 1080, 1500 / 1920, 570 / 1080))

            if config.ComboBox_fishing_mode.value == 0:
                blocks_num = self.count_yellow_blocks(self.auto.current_screenshot)
                if blocks_num >= 2:
                    self.logger.info("到点，收杆!")
                    if self.is_use_time_judge:
                        self.start_time = time.time()
                    self.auto.press_key(self.press_key)
                elif blocks_num == 0:
                    time.sleep(0.3)
                    self.auto.take_screenshot(crop=(1130 / 1920, 240 / 1080, 1500 / 1920, 570 / 1080))
                    blocks_num = self.count_yellow_blocks(self.auto.current_screenshot)
                    # 连续两次都是0才返回false,避免误判
                    if blocks_num == 0:
                        break
                else:
                    if self.is_use_time_judge:
                        # 识别出未进入黄色区域，则进行时间判断、
                        if time.time() - self.start_time > 2.2:
                            self.logger.warn("咋回事？强制收杆一次")
                            self.start_time = time.time()
                            self.auto.press_key(self.press_key)
            # 低性能模式判断方案
            else:
                if time.time() - self.bite_time > 1.8:
                    self.logger.info("到点，收杆!")
                    self.bite_time = time.time()
                    self.auto.press_key(self.press_key)

            if timeout.reached():
                self.logger.error("钓鱼环节超时")
                break

    def after_fish(self):
        timeout = Timer(20).start()
        save_flag = False
        while True:
            self.auto.take_screenshot()

            if save_flag:
                if self.auto.find_element("新纪录", "text") or self.auto.find_element(
                        "app/resource/images/fishing/new_record.png", "image", threshold=0.5,
                        crop=(1245 / 1920, 500 / 1080, 1366 / 1920, 578 / 1080)):
                    self.save_picture()
                break
            if self.auto.find_element('本次获得', 'text', crop=(832 / 1920, 290 / 1080, 1078 / 1920, 374 / 1080)):
                self.logger.info("钓鱼佬永不空军！")
                if config.CheckBox_is_save_fish.value:
                    save_flag = True
                    time.sleep(1)
                    continue
                self.auto.press_key('esc')
                time.sleep(1)
                break
            if self.auto.find_element('鱼跑掉了', 'text', crop=(858 / 1920, 151 / 1080, 1054 / 1920, 280 / 1080)):
                self.logger.warn("鱼跑了，空军！")
                break
            # 如果回到了未甩杆状态，也退出
            if not self.is_spin_rod():
                break

            if timeout.reached():
                self.logger.error("钓鱼结束环节超时")
                break

    def save_picture(self):
        current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = os.path.join(self.save_path, f"{current_date}.png")
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        self.auto.take_screenshot()
        self.auto.crrent_screenshot.save(file_path)
        self.logger.info(f"出了条大的！截图已保存至：{file_path}")

    def count_yellow_blocks(self, image):
        # 黄色的确切HSV值
        """计算图像中黄色像素的数量"""
        # 将图像转换为HSV颜色空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 创建黄色掩膜
        mask_yellow = cv2.inRange(hsv, self.lower_yellow, self.upper_yellow)

        # 查找轮廓
        contours_yellow, _ = cv2.findContours(mask_yellow, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        # self.logger.debug(f"黄色块数为：{len(contours_yellow)}")
        print(f"黄色块数为：{len(contours_yellow)}")

        return len(contours_yellow)


    def is_spin_rod(self):
        """
        判断是否已经甩杆，看不到图标后表示已甩杆
        :return:
        """
        self.auto.take_screenshot()
        crop_image,_ = ImageUtils.resize_screenshot(self.auto.hwnd,self.auto.first_screenshot,(51/1920,228/1080,89/1920,273/1080),self.auto.is_starter)
        ssim = ImageUtils.calculate_ssim('app/resource/images/fishing/fish.png',crop_image)
        if ssim>=0.5:
            return False
        return True

    def get_press_key(self):
        """
        自动获取钓鱼按键
        """
        return True