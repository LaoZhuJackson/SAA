import time
from datetime import datetime, timedelta

from app.modules.automation.timer import Timer
from app.modules.base_task.base_task import BaseTask


class ChasmModule(BaseTask):
    def __init__(self):
        super().__init__()

    def run(self):
        if not self.is_in_time_range():
            self.logger.info('当前未开放拟境')
        else:
            self.back_to_home()
            self.chasm()
            self.receive_reward()

    def chasm(self):
        timeout = Timer(30).start()
        first_finish_flag = False
        second_finish_flag = False
        while True:
            self.auto.take_screenshot()

            if self.auto.find_element('测评次数不足','text',crop=(0.25, 0.25, 0.75, 0.75)):
                break
            if first_finish_flag and second_finish_flag:
                break
            if not first_finish_flag and self.auto.find_element("准备作战", "text", crop=(1675 / 1920, 988 / 1080, 1833 / 1920, 1051/1080)):
                if not self.auto.find_element("快速测评", "text", crop=(1236 / 1920, 943 / 1080, 1552 / 1920, 1)):
                    first_finish_flag = True
            if first_finish_flag and self.is_after_wednesday_4am():
                self.auto.click_element("精神", "text", crop=(67/1920, 68 / 1080, 227/1920, 112 / 1080))
            if first_finish_flag and not self.auto.find_element("快速测评", "text", crop=(1236 / 1920, 943 / 1080, 1552 / 1920, 1)):
                second_finish_flag = True
            if self.auto.click_element('确定','text',crop=(0.5,0.5,1,1)):
                time.sleep(0.5)
                continue
            if self.auto.click_element("快速测评", "text", crop=(1236 / 1920, 943 / 1080, 1552 / 1920, 1)):
                time.sleep(0.3)
                continue
            if self.auto.click_element("精神", "text", crop=(0, 758 / 1080, 1, 828 / 1080)):
                continue
            if self.auto.click_element("特别派遣", "text", crop=(181 / 1920, 468 / 1080, 422 / 1920, 541 / 1080)):
                time.sleep(0.3)
                continue
            if self.auto.click_element("战斗", "text", crop=(1536 / 1920, 470 / 1080, 1632 / 1920, 516 / 1080)):
                time.sleep(0.3)
                continue

            if timeout.reached():
                self.logger.error("精神拟境超时")
                break

    def receive_reward(self):
        timeout = Timer(10).start()
        enter_flag = False
        while True:
            self.auto.take_screenshot()

            if enter_flag:
                if not self.auto.click_element('键领取','text',crop=(0,950/1080,321/1080,1)):
                    break
                if self.auto.find_element('获得道具', 'text', crop=(824 / 1920, 0, 1089 / 1920, 129 / 1080)):
                    break
            if self.auto.find_element('排行奖励','text',crop=(0, 0, 233/1920, 118/1080)):
                enter_flag = True
                self.auto.click_element('键领取','text',crop=(0,950/1080,321/1080,1))
            if not enter_flag:
                if self.auto.click_element('app/resource/images/chasm/reward.png','image',crop=(112/1920, 885/1080, 171/1920, 942/1080)):
                    time.sleep(0.5)
                    continue

            if timeout.reached():
                self.logger.error("精神拟境超时")
                break
        self.back_to_home()

    @staticmethod
    def is_after_wednesday_4am():
        now = datetime.now()  # 获取当前时间
        current_weekday = now.weekday()  # 获取当前是周几 (周一为0，周日为6)
        wednesday_4am = now.replace(hour=4, minute=0, second=0, microsecond=0) + timedelta(
            days=2 - current_weekday)
        # 判断当前时间是否在本周三凌晨4点之后
        return now > wednesday_4am

    @staticmethod
    def is_in_time_range():
        now = datetime.now()  # 获取当前时间
        current_weekday = now.weekday()  # 获取当前是周几 (周一为0，周日为6)
        # print(current_weekday)
        # 周二上午10点
        tuesday_10am = now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(
            days=1 - current_weekday)
        # 下周一凌晨4点
        next_monday_4am = now.replace(hour=4, minute=0, second=0, microsecond=0) + timedelta(
            days=(0 - current_weekday) + 7)
        # print(tuesday_10am, now, next_monday_4am)
        return tuesday_10am <= now < next_monday_4am
