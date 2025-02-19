import sys
from PyQt5.QtCore import pyqtSignal, QThread, QCoreApplication
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget
import time
import functools


def atoms(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if args[0].running == False:
            raise Exception("break")
        return func(*args, **kwargs)

    return wrapper


class AutomationThread(QThread):
    stop_signal = pyqtSignal()  # 定义一个停止信号

    def __init__(self):
        super().__init__()
        self.running = True  # 用来控制线程是否运行

    @atoms
    def do(self, i):
        time.sleep(1)
        print(f'do:{i}')

    def run(self):
        """
        自动化任务的执行部分
        """
        print("自动化任务开始...")
        try:
            i = 0
            while True:
                # 这里放你要执行的任务，例如截图、模拟点击等
                print("执行任务中...")
                self.do(i)  # 模拟任务执行中的延时
                i += 1
        except Exception as e:
            if str(e) == "break":
                print("停止任务...")
                return

        print("任务结束.")

    def stop(self):
        """
        停止线程
        """
        self.running = False
        print("停止线程.")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('自动化助手')
        self.setGeometry(100, 100, 300, 200)

        # 启动按钮
        self.start_button = QPushButton('启动自动化', self)
        self.start_button.clicked.connect(self.start_automation)
        self.start_button.setGeometry(50, 50, 200, 40)

        # 停止按钮
        self.stop_button = QPushButton('停止自动化', self)
        self.stop_button.clicked.connect(self.stop_automation)
        self.stop_button.setGeometry(50, 100, 200, 40)

        # 线程对象
        self.automation_thread = None

    def start_automation(self):
        """启动自动化线程"""
        if not self.automation_thread:
            self.automation_thread = AutomationThread()
            self.automation_thread.start()  # 启动线程
        else:
            print("自动化任务已经在运行中...")

    def stop_automation(self):
        """停止自动化线程"""
        if self.automation_thread:
            self.automation_thread.stop()  # 调用线程的停止方法
            self.automation_thread.wait()  # 等待线程结束
            self.automation_thread = None  # 清理线程对象
        else:
            print("没有正在运行的自动化任务.")


# 运行应用
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
