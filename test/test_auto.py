from app.common.config import config
from app.common.logger import logger
from app.modules.automation.automation import Automation, auto_starter

if __name__ == '__main__':
    # 启动器调用的自动类
    # 游戏窗口调用的自动类
    # auto_game = Automation(config.LineEdit_game_name.value, config.LineEdit_game_class.value, logger)
    auto_starter.click_element('./test_auto.png','image',take_screenshot=True,threshold=0.7,crop=(0.5,0.5,1,1),action='mouse_click')
    # auto_starter.click_element('开始游戏','text',include=True,threshold=0.7,crop=(0.5,0.5,1,1),action='mouse_click')