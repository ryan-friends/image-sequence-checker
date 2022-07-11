import window
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import sys
import time
from utils import *
from loguru import logger
from queue import Queue
from threading import Thread

# Hign DPI
QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)


def thread_it(func, *args):
    '''将函数打包进线程'''
    # 创建
    t = Thread(target=func, args=args)
    # 守护
    t.daemon = True
    # 启动
    t.start()


global msg_queue
msg_queue = Queue()


class WorkerThread(QThread):
    trigger = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        """
        从msg_queue读取消息打印到textBrowser
        """
        global msg_queue
        while 1:
            if msg_queue.empty():
                time.sleep(1)
                continue
            msg = msg_queue.get()
            self.trigger.emit(str(msg))


class MainWindow(QMainWindow, window.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.init()

    def init(self):
        """
        初始化
        """
        self.doubleSpinBoxThreshold.setValue(1024*3)
        # 设置拖拽事件
        self.textBrowser.setAcceptDrops(True)
        self.textBrowser.dragEnterEvent = self.drop_event
        # 设置按钮点击事件
        self.pushButtonDir.clicked.connect(self.select_dir)
        self.pushButtonStart.clicked.connect(
            lambda: thread_it(self.start_detect))
        #
        self.worker = WorkerThread()
        self.worker.trigger.connect(self.print_msg)
        self.worker.start()

    def print_msg(self, msg):
        """
        打印消息
        """
        if msg == 'clear':
            self.textBrowser.clear()
            return
        self.textBrowser.append(msg)

    def drop_event(self, event):
        """
        拖拽事件
        当拖拽文件夹到TextBrowser时，将文件夹路径赋值给self.lineEditDir
        """
        self.lineEditDir.setText(
            event.mimeData().text().replace('file:///', ''))

    def select_dir(self):
        """
        选择文件夹
        """
        dir_path = QFileDialog.getExistingDirectory(self, "选择文件夹", "./")
        if dir_path:
            self.lineEditDir.setText(dir_path)

    def start_detect(self):
        """
        开始检测
        """
        dir = self.lineEditDir.text()
        threshold = self.doubleSpinBoxThreshold.value()
        #序号位数
        num_digits = self.spinBox.value()
        if dir == '':
            logger.error('请选择文件夹')
            self.print_msg('请选择文件夹')
            return

        # 检查文件夹是否存在
        if not os.path.exists(dir):
            logger.error(f'{dir}文件夹不存在')
            self.print_msg(f'{dir}文件夹不存在')
            return
        msg_queue.put('clear')
        msg_queue.put(f'开始检测"{dir}"文件夹...')
        # 开始检测
        tool = Util(num_digits)
        # 缺失序列
        missing_files, threshold_files = tool.check_dir_files(dir, threshold)
        msg_queue.put('clear')

        #
        msg_queue.put('一、缺失帧：')
        if missing_files:
            for file in missing_files:
                msg_queue.put(file)
        else:
            msg_queue.put('无')
        if self.checkBox.isChecked():
            msg_queue.put(f'\n二、 疑似坏帧（< {threshold} KB）：')
            if threshold_files:
                for file in threshold_files:
                    msg_queue.put(file)
            else:
                msg_queue.put('无')

        msg_queue.put(f'\n检测结果:')
        msg_queue.put(f'总帧数: {tool.total_files}')
        msg_queue.put(f'缺失帧数: {len(missing_files)}')
        if self.checkBox.isChecked():
            msg_queue.put(f'疑似坏帧数: {len(threshold_files)}')
        msg_queue.put('\n检测完成')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
