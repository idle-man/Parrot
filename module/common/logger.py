# -*- coding: utf-8 -*-
# --------------------------------------------------------------
#   When        Who         What
# --------------------------------------------------------------
# Mar 05,2019   idle-man    Create
#

import os
import re
import platform
import logging
from logging import handlers


class Logger:
    __author__ = 'idle-man'
    __desc__ = 'log printer based on logging'

    def __init__(self, path='', level='info'):
        """
        :param path: 指定的日志路径，''则使用项目默认路径
        :param level: 日志级别，debug / info / warn / error
        """
        level_map = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warn': logging.WARN,
            'error': logging.ERROR
        }

        if path == '':
            self.path = re.findall(r"(.+Parrot)", os.path.abspath(__file__))[0] + "/log"
        else:
            self.path = path
        if str(level).lower() in level_map.keys():
            self.level = level
        else:
            self.level = 'info'

        if platform.system() == 'Windows':
            log_file = "%s\\%s\\" % (self.path, 'parrot.log')
        else:
            log_file = "%s/%s/" % (self.path, 'parrot.log')

        self.logger = logging.getLogger(log_file)
        # 定义日志格式
        self.fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        self.logger.setLevel(level_map.get(level))
        # 定义屏幕输出句柄
        sh = logging.StreamHandler()
        sh.setFormatter(self.fmt)
        # 定义文件写入句柄，每周一备份，最多保留4个备份
        th = handlers.TimedRotatingFileHandler(filename=log_file, when='W0', backupCount=4)  #, encoding='utf-8')
        th.setFormatter(self.fmt)
        # 多句柄加入
        self.logger.addHandler(sh)
        self.logger.addHandler(th)

    def debug(self, message):
        self.logger.debug(msg=message)

    def info(self, message):
        self.logger.info(msg=message)

    def warn(self, message):
        self.logger.warning(msg=message)

    def error(self, message):
        self.logger.error(msg=message)


if __name__ == "__main__":
    logger = Logger(path='')
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warn("Warn message")
    logger.error("Error message")

