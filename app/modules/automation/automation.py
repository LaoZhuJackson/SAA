from app.common.singleton import SingletonMeta


class Automation(metaclass=SingletonMeta):
    """
    自动化管理类，用于管理与游戏窗口相关的自动化操作。
    """

    def __init__(self,window_title,logger:None):
        """
        :param window_title: 游戏窗口的标题。
        :param logger: 用于记录日志的Logger对象，可选参数。
        """
        self.window_title = window_title
        self.logger = logger
        self.screenshot = None
        self._init_input()
        self.img_cache = {}