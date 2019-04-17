# -*- coding: utf-8 -*-
# --------------------------------------------------------------
#   When        Who         What
# --------------------------------------------------------------
# Apr 02,2019   idle-man    Create
#
import time
import datetime

"""
日期&时间格式说明：
    %Y：年
    %m：月
    %d：日
    %H：时
    %M：分
    %S：秒
不同单位之间可自由设置连接符
"""


def Today(format='%Y-%m-%d'):  # 获取今天的日期
    return datetime.datetime.now().strftime(format)


def Tomorrow(format='%Y-%m-%d'):  # 获取明天的日期
    return DaysLater(later=1, format=format)


def Yesterday(format='%Y-%m-%d'):  # 获取昨天的日期
    return DaysAgo(ago=1, format=format)


def DaysLater(later=1, format='%Y-%m-%d'):  # 获取几天后的日期
    return (datetime.datetime.now() + datetime.timedelta(days=int(later))).strftime(format)


def DaysAgo(ago=1, format='%Y-%m-%d'):  # 获取几天前的日期
    return (datetime.datetime.now() - datetime.timedelta(days=int(ago))).strftime(format)


def Now(format='%Y%m%d%H%M%S'):  # 获取当前时间，精确到秒
    return datetime.datetime.now().strftime(format)


def TimeStamp():  # 获取当前时间戳，精确到秒
    return int(round(time.time()))


def TimeStampMs():  # 获取当前时间戳，精确到毫秒
    return int(round(time.time())) * 1000 + int(datetime.datetime.now().microsecond / 1000)

if __name__ == '__main__':
    pass
