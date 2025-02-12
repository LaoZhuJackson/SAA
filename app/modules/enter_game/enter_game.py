import time

import win32gui

from app.common.config import config
from app.common.logger import logger
from app.modules.automation.automation import Automation, instantiate_automation
from app.modules.automation.timer import Timer


class EnterGameModule:
    def __init__(self):
        self.enter_game_flag = False
        # 对游戏和启动器的不同自动化类
        self.auto = None

    def run(self):
        auto_type = self.chose_auto()
        # 当游戏和启动器都开着的时候，auto_type="game",跳过handle_starter
        if auto_type=="starter":
            self.handle_starter_new()
            # 切换成auto_game
            time.sleep(10)
            self.chose_auto(only_game=True)
        self.handle_game()

    def handle_starter_new(self):
        """
        处理官方新启动器启动器窗口部分
        :return:
        """
        while self.auto:
            # 截图
            self.auto.take_screenshot()
            # 对截图内容做对应处理
            if self.auto.click_element('开始游戏', 'text', crop=(0.5, 0.5, 1, 1), action='mouse_click'):
                logger.info("游戏无需更新或更新完毕")
                self.auto = None
                break
            if self.auto.find_element('游戏运行中', 'text', crop=(0.5, 0.5, 1, 1)):
                break
            if self.auto.find_element('正在更新', 'text', crop=(0.5, 0.5, 1, 1)):
                # 还在更新
                time.sleep(5)
                continue
            if self.auto.click_element('继续更新', 'text', crop=(0.5, 0.5, 1, 1),action='mouse_click'):
                time.sleep(5)
                continue
            if self.auto.click_element('更新', 'text', include=False, crop=(0.5, 0.5, 1, 1), action='mouse_click'):
                logger.info("需要更新")
                continue
            # if self.auto.click_element('确定', 'text', crop=(0, 0.5, 1, 1), action='mouse_click'):
            #     # 跳过后续，直接截新图
            #     continue


    def handle_game(self):
        esc_flag = False
        """处理游戏窗口部分"""
        while self.auto:
            # 截图
            self.auto.take_screenshot()

            # 对不同情况进行处理
            if self.auto.find_element('基地', 'text', (1598 / 1920, 678 / 1080, 1661 / 1920, 736 / 1080)) and self.auto.find_element('任务', 'text', (1452 / 1920, 327 / 1080, 1529 / 1920, 376 / 1080)):
                logger.info("已进入游戏")
                break
            if self.auto.click_element('开始游戏','text', crop=(852/1920, 920/1080, 1046/1920, 981/1080)):
                time.sleep(5)
                continue
            if self.auto.click_element(['X','x'],'text',crop=(1271/1920,88/1080,1890/1920,367/1080),action='move_click'):
                continue
            if self.auto.click_element("../app/resource/images/start_game/newbird_cancel.png", "image"):
                continue



    def chose_auto(self,only_game=False):
        """
        自动选择auto，有游戏窗口时选游戏，没有游戏窗口时选启动器，都没有的时候循环，寻找频率1次/s
        :return:
        """
        timeout = Timer(20).start()
        flag = ''
        while True:
            # 每次循环重新导入
            from app.modules.automation.automation import auto_starter, auto_game
            if win32gui.FindWindow(None, config.LineEdit_game_name.value) or only_game:
                if not auto_game:
                    instantiate_automation(auto_type='game')  # 尝试实例化 auto_game
                self.auto = auto_game
                flag = 'game'
            else:
                if not auto_starter:
                    instantiate_automation(auto_type='starter')  # 尝试实例化 auto_starter
                self.auto = auto_starter
                flag = 'starter'
            if self.auto:
                print(f"{flag=}")
                return flag
            if timeout.reached():
                logger.error("获取auto超时")
                break
            time.sleep(1)

if __name__ == '__main__':
    EnterGameModule().run()