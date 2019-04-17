# -*- coding: utf-8 -*-
# --------------------------------------------------------------
#   When        Who         What
# --------------------------------------------------------------
# Jan 10,2019   idle-man    Create TimeHelper、FileHelper、RandomHelper
# Mar 01,2019   idle-man    Create DictHelper
# Mar 05,2019   idle-man    Add unit_test for each helper
#

import os
import sys
import time
import datetime
import shutil
import random
import string
import platform
import json
import re
from copy import deepcopy


class MyTimeHelper:
    __author__ = 'idle-man'
    __desc__ = "获取常用格式的日期、时间"

    def __init__(self):
        pass

    # 自测用例
    def unit_test(self):
        print "Test MyTimeHelper.."
        print " * now_date:", self.now_date()
        print " * now_date_int:", self.now_date_int()
        print " * now_time:", self.now_time()
        print " * now_time_int:", self.now_time_int()
        print " * now_time_ms:", self.now_time_ms()
        print " * now_time_ms_int:", self.now_time_ms_int()
        print " * now_datetime:", self.now_datetime()
        print " * now_datetime_utc:", self.now_datetime_utc()
        print " * now_datetime_int:", self.now_datetime_int()
        print " * now_datetime_ms:", self.now_datetime_ms()
        print " * now_unix_timestamp:", self.now_unix_timestamp()
        print " * now_unix_timestamp_ms:", self.now_unix_timestamp_ms()
        print " * time_days_ago(5):", self.time_days_ago(5)
        print " * time_days_later(30):", self.time_days_later(30)
        print " * time_hours_ago(15):", self.time_hours_ago(15)
        print " * time_hours_later(12):", self.time_hours_later(12)

    @staticmethod
    def now_date():  # e.g. 2019-01-01
        return datetime.datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def now_date_int():  # e.g. 20190101
        return datetime.datetime.now().strftime("%Y%m%d")

    @staticmethod
    def now_time():  # e.g. 01:01:01
        return datetime.datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def now_time_int():  # e.g. 010101
        return datetime.datetime.now().strftime("%H%M%S")

    @staticmethod
    def now_time_ms():  # e.g. 01:01:01.012
        now = datetime.datetime.now()
        return now.strftime("%H:%M:%S") + '.' + "%03d" % round(float(now.microsecond) / 1000)

    @staticmethod
    def now_time_ms_int():  # e.g. 010101
        now = datetime.datetime.now()
        return now.strftime("%H%M%S") + "%03d" % round(float(now.microsecond) / 1000)

    @staticmethod
    def now_datetime():  # e.g. 2016-01-01 01:01:01
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def now_datetime_int():  # e.g. 20160101010101
        return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    @staticmethod
    def now_datetime_utc():
        return datetime.datetime.utcnow()

    @staticmethod
    def now_datetime_ms():  # e.g. 2016-01-01 01:01:01.012
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S") + '.' + "%03d" % round(float(now.microsecond) / 1000)

    @staticmethod
    def now_unix_timestamp():  # e.g. 1451581261
        return int(round(time.time()))

    @staticmethod
    def now_unix_timestamp_ms():  # e.g. 1451581261339
        return int(round(time.time()))*1000 + int(datetime.datetime.now().microsecond / 1000)

    @staticmethod
    def time_days_ago(num=0):
        if int(num) < 1:
            return False
        return (datetime.datetime.now() - datetime.timedelta(days=num)).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def time_days_later(num=0):
        if int(num) < 1:
            return False
        return (datetime.datetime.now() + datetime.timedelta(days=num)).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def time_hours_ago(num=0):
        if int(num) < 1:
            return False
        return (datetime.datetime.now() - datetime.timedelta(hours=num)).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def time_hours_later(num=0):
        if int(num) < 1:
            return False
        return (datetime.datetime.now() + datetime.timedelta(hours=num)).strftime("%Y-%m-%d %H:%M:%S")


class MyFileHelper:
    __author__ = "idle-man"
    __desc__ = "常用的文件夹和文件操作"

    def __init__(self):
        pass

    # 自测用例
    def unit_test(self):
        print "Test MyFileHelper.."
        print " * make_dir:", self.make_dir("MyFileHelper_UnitTest")
        print " * copy_file:", self.copy_file("MyFileHelper_UnitTest", "MyFileHelper_UnitTest_Copied")
        print " * get_sub_folders:", self.get_sub_folders('.')
        print " * remove_dir:", self.remove_dir("MyFileHelper_UnitTest")
        print " * remove_file:", self.remove_file("MyFileHelper_UnitTest_Copied")

    @staticmethod
    def make_dir(directory):
        """
        :param directory: 
        :return: directory / False
        """
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except Exception as e:
                return False
        else:
            pass

        return directory

    @staticmethod
    def remove_dir(directory):
        """
        :param directory: 
        :return: directory / False
        """
        if os.path.exists(directory):
            if os.path.isfile(directory):
                try:
                    os.remove(directory)
                except Exception as e:
                    return False
            elif os.path.isdir(directory):
                try:
                    shutil.rmtree(directory)
                except Exception as e:
                    return False
            else:
                pass

        return directory

    @staticmethod
    def remove_file(filename):
        """
        :param filename: 
        :return: filename / False
        """
        if os.path.exists(filename):
            if os.path.isfile(filename):
                try:
                    os.remove(filename)
                except Exception as e:
                    return False
            elif os.path.isdir(filename):
                try:
                    shutil.rmtree(filename)
                except Exception as e:
                    return False
            else:
                pass

        return filename

    @staticmethod
    def copy_file(source, target):
        """
        :param source: 
        :param target: 
        :return: target / False
        """
        try:
            if os.path.isdir(source):
                shutil.copytree(source, target)
            else:
                shutil.copy(source, target)
        except Exception as e:
            return False

        return target

    @staticmethod
    def get_sub_folders(directory):
        """
        :param directory: 
        :return: list / []
        """
        if os.path.isdir(directory):
            return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
        else:
            return []


class MyRandomHelper:
    __author__ = "idle-man"
    __desc__ = "常用的随机串生成，支持头部和尾部定义"

    def __init__(self):
        pass

    # 自测用例
    def unit_test(self):
        print "Test MyRandomHelper.."
        print " * get_random_integer(length=8):", self.get_random_integer(length=8)
        print " * get_random_integer(length=8, head=1, tail=5):", self.get_random_integer(length=8, head=1, tail=5)
        print " * get_random_string():", self.get_random_string()
        print " * get_random_string(length=50, simple=3, head='Hello ', tail=' World!'):", self.get_random_string(length=50, simple=3, head='Hello ', tail=' World!')
        print " * get_random_chinese(length=30, head='你好 ', tail=' 世界！'):", self.get_random_chinese(length=30, head='你好 ', tail=' 世界！')
        print " * get_random_phone():", self.get_random_phone()
        print " * get_random_phone(tail=888):", self.get_random_phone(tail=888)

    @staticmethod
    def get_random_integer(length=10, head='', tail=''):
        if not (isinstance(length, int) and length > 0):  # 异常传参的兜底
            length = len(str(length))

        my_str = random.randint(10 ** (length-1), 10 ** length - 1)

        if head != '':
            if len(str(head)) > length:
                return head
            my_str = int(str(head) + str(str(my_str)[len(str(head)):]))  # 指定的头部，从前面开始替换
        if tail != '':
            if len(str(tail)) > length:
                return tail
            my_str = int(str(str(my_str)[:-len(str(tail))]) + str(tail))  # 指定的尾部，从后面开始替换

        return my_str

    @staticmethod
    def get_random_string(length=10, simple=1, head='', tail=''):
        if not (isinstance(length, int) and length > 0):  # 异常传参的兜底
            length = len(str(length))

        if simple == 1:  # 常规模式，字母和数字组合
            src = str(string.digits) + string.letters
        elif simple == 2:  # 在常规模式基础上，去除视觉上易混淆的字符: 0&O&o c&C I&l&1 k&K p&P s&S v&V w&W x&X z&Z
            src = 'abdefghijmnqrtuyABDEFGHJLMNQRTUY23456789'
        else:  # 在常规模式基础上，增加常见特殊字符
            src = str(string.digits) + string.letters + '~`!@#$%^&*()[]{}\|<>?/,.-_=+'

        # 防止length超长，进行扩容
        src = src * (length / len(src) + 1)

        my_str = string.join(random.sample(src, length)).replace(' ', '')

        if head != '':
            if len(str(head)) > length:
                return head
            my_str = str(head) + str(my_str[len(str(head)):])  # 指定的头部，从前面开始替换
        if tail != '':
            if len(str(tail)) > length:
                return tail
            my_str = str(my_str[:-len(str(tail))]) + str(tail)  # 指定的尾部，从后面开始替换

        return str(my_str)

    @staticmethod
    def __gb2312():  # 得到一个中文字符
        head = random.randint(0xB0, 0xCF)
        body = random.randint(0xA, 0xF)
        tail = random.randint(0, 0xF)
        val = (head << 8) | (body << 4) | tail
        try:
            return ("%x" % val).decode('hex').decode('gb2312')
        except Exception as e:
            return False

    @classmethod
    def get_random_chinese(cls, length=10, head='', tail=''):
        if not (isinstance(length, int) and length > 0):  # 异常传参的兜底
            length = len(str(length))

        my_str = ''
        for i in range(0, length):
            str_a = cls.__gb2312()
            while not str_a:  # 偶尔会失败...
                str_a = cls.__gb2312()
                if str_a:
                    break
            my_str = "%s%s" % (my_str, str_a)

        # 字符长度：1 Chinese character == 3 unicode characters
        if head != '':  # 指定的头部，从前面开始替换
            if isinstance(head, (unicode, int, float, bool)):
                my_str = str(head) + my_str[len(str(head)):]
            else:
                my_str = unicode(str(head), "utf-8") + my_str[len(str(head))/3:]
        if tail != '':  # 指定的尾部，从后面开始替换
            if isinstance(tail, (unicode, int, float, bool)):
                my_str = my_str[:-len(str(tail))] + str(tail)
            else:
                my_str = my_str[:-len(str(tail))/3] + unicode(str(tail), "utf-8")
        return my_str

    @staticmethod
    def get_random_phone(head='', tail=''):  # 中国国内手机号, length = 11
        length = 11
        p_head = ''
        p_tail = ''
        if head != '' and len(str(head)) < 11:
            length -= len(str(head))
            p_head = str(head)
        if tail != '' and len(str(tail)) < 11:
            length -= len(str(tail))
            p_tail = str(tail)
        if length > 0:
            if p_head:
                return p_head + "".join(random.choice(string.digits) for i in range(length)) + p_tail
            else:
                return '1' + "".join(random.choice('345678')) + "".join(random.choice(string.digits) for i in range(length-2)) + p_tail
        else:
            return (p_head + p_tail)[:11]


class MyDictHelper:
    __author__ = 'idle-man'
    __desc__ = "遍历字典/列表，变为层级深度为1的key/value组合，便于进行diff"
    
    def __init__(self):
        self.global_item = None
        pass

    # 自测用例
    def unit_test(self):
        print "Test MyDictHelper.."
        my_dict = json.loads('{"status": 200, "timestamp": 1551355242, "sign": "202cb962ac59075b964b07152d234b70", "token": "joFpAyZgTQ167lb3vthPDxVu8Y9eLd4J", "message": "Success", "data": {"date": "20190228", "from": "SuZhou", "list": [{"status": ["Unknown"], "levels": {"A": 4, "C": 0, "B": 2}, "tag": "OiIMULbFc3v1HzrNu7CkWphXyt8V2q", "number": 121, "time": "07:00"}, {"status": ["Busy"], "levels": {"A": 2, "C": 1, "B": 2}, "tag": "DKUEOJxuk3yVTr4NGg0Zh6sdb1QW9R", "number": 122, "time": "08:30"}, {"status": ["Unknown"], "levels": {"A": 4, "C": 0, "B": 0}, "tag": "l4khiBSav9AwMIgeU5tTjqRWz3s8Q0", "number": 123, "time": "10:15"}], "userid": 123456, "to": "ShangHai"}}')
        my_list = json.loads('[{"status": ["Unknown"], "levels": {"A": 4, "C": 0, "B": 2}, "tag": "OiIMULbFc3v1HzrNu7CkWphXyt8V2q", "number": 121, "time": "07:00"}, {"status": ["Busy"], "levels": {"A": 2, "C": 1, "B": 2}, "tag": "DKUEOJxuk3yVTr4NGg0Zh6sdb1QW9R", "number": 122, "time": "08:30"}, {"status": ["Unknown"], "levels": {"A": 4, "C": 0, "B": 0}, "tag": "l4khiBSav9AwMIgeU5tTjqRWz3s8Q0", "number": 123, "time": "10:15"}]')

        print " * Test get_all_items.."
        print "   - Dict:", json.dumps(self.get_all_items(item=my_dict))
        print "   - List:", json.dumps(self.get_all_items(item=my_list))

        print " * Test get_all_keys.."
        print "   - Dict:", json.dumps(self.get_all_keys(item=my_dict))
        print "   - List:", json.dumps(self.get_all_keys(item=my_list))

        print " * Test revert_items.."
        print "   - Dict:", json.dumps(self.revert_items(item={'a.b.c.d': 1, 'a.b.e': 2}))

        my_nodes = ['data', 'data.list', 'data.list[0]', 'data.list[0].number']
        print " * Test is_descendant_node.."
        print "   - 1:", self.is_descendant_node(node='data.list[0].key', nodes=my_nodes) == 1
        print "   - 2:", self.is_descendant_node(node='data', nodes=my_nodes) == 2
        print "   - 0:", self.is_descendant_node(node='key', nodes=my_nodes) == 0

        print " * Test is_ancestral_node.."
        print "   - 1:", self.is_ancestral_node(node='data.list[0]', nodes=my_nodes) == 1
        print "   - 2:", self.is_ancestral_node(node='data.list[0].number', nodes=my_nodes) == 2
        print "   - 0:", self.is_ancestral_node(node='key', nodes=my_nodes) == 0

        print " * Test param2dict.."
        print "   - date=0305&tag=abcd&id=123 =>", self.param2dict(item='date=0305&tag=abcd&id=123')

        print " * Test dict2param.."
        print "   - {'date': '0305', 'tag': 'abcd', 'id': 123} =>", self.dict2param(item={'date': '0305', 'tag': 'abcd', 'id': 123})

    # 遍历字典/列表，以层级深度为1的目标，获取到所有的key/value对
    def get_all_items(self, item, prefix='', mode=1):
        """
        :param item: 一个字典或列表，无论深度如何
        :param prefix: key的前缀，默认为空，递归时会用到
        :param mode: 输出模式，1-value为纯扁平模式，0-各级value均保存
        :return: 字典，深度为1的key/value对
        """
        my_items = {}
        if isinstance(item, dict):
            if len(item) == 0:
                my_items[prefix] = {}
            for x in range(len(item)):
                t_key = item.keys()[x]
                t_val = item[t_key]
                if prefix != '':
                    t_key = str(prefix) + "." + str(t_key)
                else:
                    pass
                if not (mode and isinstance(t_val, (dict, list, tuple, set))):
                    my_items[t_key] = t_val
                my_items = dict(my_items.items() + self.get_all_items(item=t_val, prefix=t_key).items())
        elif isinstance(item, (list, set, tuple)):
            if len(item) == 0:
                my_items[prefix] = []
            for x in range(len(item)):
                if prefix != '':
                    t_key = "%s[%d]" % (prefix, x)
                else:
                    t_key = "[%d]" % x
                if not (mode and isinstance(item[x], (dict, list, tuple, set))):
                    my_items[t_key] = item[x]
                my_items = dict(my_items.items() + self.get_all_items(item=item[x], prefix=t_key).items())
        else:  # the end level
            if prefix == '':
                my_items[item] = ''

        return my_items

    # 遍历字典/列表，以层级深度为1的目标，获取到所有的key
    def get_all_keys(self, item):
        return self.get_all_items(item=item).keys()

    # 将层级深度为1的字典/列表，还原为原始层级格式
    def revert_items(self, item):
        """
        :param item: 按照get_all_items格式处理的深度为1的字典/列表
        :param mode: 输入模式，1-value为纯扁平模式，0-各级value均保存
        :return: 原始层次的dict/list
        """
        my_dict = {}
        my_list = []
        if not isinstance(item, dict):
            return {}
        for k in sorted(item.keys()):  # 先sort，防止列表格式的数据后排序号出现在前面
            if re.match(r"^\[\d+\]", k):  # 列表格式
                self.revert_one_key(key=k, val=item[k])
                my_list.append(deepcopy(self.global_item))
                self.global_item = None  # 重置，以便下一次存储
            else:  # 字典格式
                self.revert_one_key(key=k, val=item[k])
                my_dict = self.merge_dict(dict1=my_dict, dict2=deepcopy(self.global_item))
                self.global_item = None  # 重置，以便下一次存储
        if my_dict:
            return my_dict
        return my_list

    # 还原一个key
    # 如：a.b.c.d: 1 => {'a': {'b': {'c': {'d': 1}}}}
    def revert_one_key(self, key, val):
        my_item = None
        k_arr = re.findall(r"(.+)\.(.+)", key)
        if not k_arr:  # 只有一层
            if re.match(r".*\[\d+\]", key):  # 列表格式
                l_arr = re.findall(r"(.*)\[(\d+)\]$", key)
                if not re.match(r".*\[\d+\]", l_arr[0][0]):  # 已递归到最后一层
                    my_item = [val]
                    if not self.global_item:  # 为了顺利逃出深层递归...
                        self.global_item = my_item
                    return my_item
                else:  # 不止一层
                    my_item = self.revert_one_key(key=l_arr[0][0], val=[val])
            else:  # 已递归到最后一层
                my_item = {key: val}
                if not self.global_item:  # 为了顺利逃出深层递归...
                    self.global_item = my_item
                return my_item
        else:  # 不止一层
            # my_dict[k_arr[0][0]] = {k_arr[0][1]: val}
            if re.match(r".*\[\d+\]$", k_arr[0][1]):  # value也是列表格式...
                t_k = str(k_arr[0][0]) + '.' + str(re.findall(r"(.*)\[\d+\]$", k_arr[0][1])[0])
                my_item = self.revert_one_key(key=t_k, val=[val])
            else:
                my_item = self.revert_one_key(key=k_arr[0][0], val={k_arr[0][1]: val})

    # 合并两个字典
    # 如：{'a': {'b': {'c': {'d': 1}}}} + {'a': {'b': {'c': {'e': 2}}}} => {'a': {'b': {'c': {'e': 2, 'd': 1}}}}
    # todo: 需要支持dict和list混编对象的merge，复杂度过高，放一放……
    def merge_dict(self, dict1, dict2):
        for key in dict2.keys():
            if key not in dict1.keys():
                dict1[key] = dict2[key]
            else:
                self.merge_dict(dict1=dict1[key], dict2=dict2[key])
        return dict1

    # 检查某个key是否为某个/某组key之一的后代节点
    @staticmethod
    def is_descendant_node(node, nodes):
        """
        :param node: 一个节点key
        :param nodes: 一个或一组节点key
        :return: 1-后代节点, 2-节点本尊, 0-其他情况
        """
        node = str(node.strip())
        if not isinstance(nodes, (list, set, tuple)):
            nodes = [str(nodes), ]
        if nodes:
            for i_node in nodes:
                i_node = str(i_node.strip()).replace('[', '\[').replace(']', '\]')
                if re.match(r"^" + i_node + "\..+", node) or re.match(r"^" + i_node + "\[\d+\].*", node):
                    return 1
            for i_node in nodes:
                if str(i_node.strip()) == node:
                    return 2
        return 0

    # 检查某个key是否为某个/某组key之一的祖辈节点
    @staticmethod
    def is_ancestral_node(node, nodes):
        """
        :param node: 一个节点key
        :param nodes: 一个或一组节点key
        :return: 1-祖辈节点, 2-节点本尊, 0-其他情况
        """
        node = str(node.strip()).replace('[', '\[').replace(']', '\]')
        if not isinstance(nodes, (list, set, tuple)):
            nodes = [str(nodes), ]
        if nodes:
            for i_node in nodes:
                i_node = str(i_node.strip())
                if re.match(r"^" + node + "\..+", i_node) or re.match(r"^" + node + "\[\d+\].*", i_node):
                    return 1
            for i_node in nodes:
                if str(i_node.strip()).replace('[', '\[').replace(']', '\]') == node:
                    return 2

        return 0

    # 将标准化传参转为字典格式，如：date=0305&tag=abcd&id=123 => {'date': '0305', 'tag': 'abcd', 'id': 123}
    @staticmethod
    def param2dict(item):
        my_dict = {}
        for i_item in str(item).split('&'):
            i_arr = re.findall(r"^([^=]+)=(.+)", i_item)
            if i_arr:
                my_dict[i_arr[0][0]] = i_arr[0][1]
        return my_dict

    # 将字典转化为标准化传参，如：{'date': '0305', 'tag': 'abcd', 'id': 123} => date=0305&tag=abcd&id=123
    @staticmethod
    def dict2param(item):
        if not isinstance(item, dict):
            return str(item)
        my_param = ''
        for key, val in item.items():
            if my_param == '':
                my_param = "%s=%s" % (str(key), str(val))
            else:
                my_param += "&%s=%s" % (str(key), str(val))
        return my_param

if __name__ == "__main__":
    MyTimeHelper().unit_test()
    MyFileHelper().unit_test()
    MyRandomHelper().unit_test()
    MyDictHelper().unit_test()
