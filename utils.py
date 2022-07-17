import os
import re
from loguru import logger


class Util:

    def __init__(self, num_digits):
        self.num_digits = num_digits

    def analysis_file_serial(self, filename):
        """
        获取文件名的数字序列
        """
        serial = re.findall('\d{%s,}'%(self.num_digits,), filename)
        if serial:
            return int(serial[-1])
        else:
            logger.error(f'{filename}文件名格式不正确,无法获取序列号')
            return None

    def check_file_size(self, filepath, threshold):
        """
        检查文件大小是否小于阈值
        """
        file_size = os.path.getsize(filepath)
        # 转为KB
        file_size = file_size/1024
        if file_size < threshold:
            return True
        else:
            return False

    def check_dir_files(self, dir_path, threshold):
        """
        检测文件夹内图片编号是否连续
        """
        missing_files = []
        threshold_files = []
        # 获取文件夹内所有文件名
        files = os.listdir(dir_path)
        self.total_files = len(files)
        # 排序
        files.sort()
        # 获取文件名的数字序列
        serials = [self.analysis_file_serial(file) for file in files if self.analysis_file_serial(file)]
        min_serial = min(serials)
        max_serial = max(serials)
        # 检查是否连续
        for s in range(min_serial, max_serial+1):
            if s not in serials:
                missing_files.append(s)

        # 检测文件大小
        for file in files:
            file_path = os.path.join(dir_path, file)
            if self.check_file_size(file_path, threshold):
                threshold_files.append(file)

        return missing_files, threshold_files
