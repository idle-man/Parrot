# -*- coding: utf-8 -*-
# --------------------------------------------------------------
#   When        Who         What
# --------------------------------------------------------------
# Jan 11,2019   idle-man    Support Fiddler txt parsing
# Jan 24,2019   idle-man    Support select and ignore settings in config
# Feb 01,2019   idle-man    Support Charles trace parsing
# Mar 13,2019   idle-man    Remove .gor related code
#

import hashlib
import json
import os
import re
import sys
import time
import cchardet

from module.common.helper import MyRandomHelper
from module.common.configer import MyConfigHelper
from module.common.configer import MyIniHelper
from module.common.logger import Logger


class MyParser:
    __author__ = 'idle-man'
    __desc__ = "解析源文件，生成可供回放的ini格式"

    def __init__(self, conf=None, logger=None):
        if not logger:
            self.logger = Logger()
        else:
            self.logger = logger
        if not conf:
            self.mch = MyConfigHelper(logger=logger)
        else:
            self.mch = conf
        self.mch.set_section(section='record')

    def __timestamp(self, timestr):
        try:
            if re.match(r'(.+) \D+$', timestr.strip()):  # Fiddler time format: Wed, 30 Jan 2019 07:56:42
                t_str = re.findall(r'(.+) \D+$', timestr.strip())[0]
                return "%d%s" % (int(time.mktime(time.strptime(t_str, "%a, %d %b %Y %H:%M:%S"))), '000')
            else:  # Charles time format: 2019-01-30T14:18:54.937+08:00
                return "%d%s" % (
                    int(time.mktime(time.strptime(timestr.split('+')[0].split('.')[0], "%Y-%m-%dT%H:%M:%S"))),
                    timestr.split('+')[0].split('.')[1])
        except ValueError:  # unknown time format
            self.logger.error("Unexpected time format: ", str(timestr), ", pls report it to the author")
            return False

    def __gor_block_start(self, url, timestr):  # the beginning line of a gor block
        # The rule: Integer(1 as default) String(length=40, md5(url).high32+8random) timestamp(length=19)
        part1 = 1
        part2 = hashlib.md5(url).hexdigest() + str(MyRandomHelper.get_random_string(8)).lower()
        part3 = self.__timestamp(timestr)

        return "%d %s %s" % (part1, part2, part3)

    @staticmethod
    def __gor_block_end():  # the ending line of a gor block
        return "\n\n🐵🙈🙉"

    def __read_file(self, filename):  # Read text file and return content
        # print "Read content from your file: ", filename
        fr = open(filename)
        lines = fr.readlines()
        #
        # lines = []
        # for line in fr.readlines():
        #     try:
        #         # 文本转码
        #         f_encode = cchardet.detect(line).get('encoding')
        #         if f_encode and f_encode.lower() != 'utf-8':
        #             line = line.decode(cchardet.detect(line).get('encoding')).encode('UTF8')
        #     except Exception as e:
        #         self.logger.warn("Get wrong encoding line: " + str(line) + e)
        #         continue
        #     lines.append(line)
        fr.close()
        return lines

    # 解析Fiddler txt，获取回放和验证的必要内容
    def __parse_fiddler_blocks(self, lines):
        """fiddler txt文件关键信息示例：
POST http://x.x.x.x:8080/api HTTP/1.1
Host: x.x.x.x:8080
Connection: keep-alive
Accept: */*
X-Requested-With: XMLHttpRequest
User-Agent: Mozilla/5.0 (Linux; Android 9; MIX 2S Build/PKQ1.180729.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/66.0.3359.126 MQQBrowser/6.2 TBS/044504 Mobile Safari/537.36 MMWEBID/7049 MicroMessenger/7.0.3.1400(0x2700033A) Process/tools NetType/WIFI Language/zh_CN
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,en-US;q=0.9

para=%7B%22TimeStamp%22%3A1551422399000%2C%22UserId%22%3A%22083e29e59c0b257813af7cb454b1e0e9%22%2C%22Token%22%3A%22w6XCs4YqWnIEbJpDKvQHtMr7OZ8Rjkyl%22%2C%22From%22%3A%22SuZhou%22%2C%22To%22%3A%22ShangHai%22%7D&sign=ce29e93aa020b06a3289ee7e459d008c
HTTP/1.0 200 OK
Content-Type: text/html; charset=utf-8
Date: Fri, 01 Mar 2019 06:40:08 GMT

{"status": 200, "timestamp": 1551422409, "sign": "202cb962ac59075b964b07152d234b70", "token": "2X4kgOIJy5Y07MwltePZNqpvSFmBR1Vc", "message": "Success", "data": {"date": "20190301", "from": "SuZhou", "list": [{"status": ["Available"], "levels": {"A": 4, "C": 0, "B": 1}, "tag": "zkIbPYCZe4Sx8jwhnfE7OdKLr3NsRc", "number": 121, "time": "07:00"}, {"status": ["Available"], "levels": {"A": 2, "C": 0, "B": 1}, "tag": "9sTI5Ld01RABcK74kJDCtMwWhN8ouH", "number": 122, "time": "08:30"}, {"status": ["Busy"], "levels": {"A": 3, "C": 1, "B": 1}, "tag": "5qgpdvjPR8zGWiMYK4ANEmxSVsXLU7", "number": 123, "time": "10:15"}], "userid": 123456, "to": "ShangHai"}}

------------------------------------------------------------------
        """
        # Host的下一行开始为request header，直到最近的一个空行，再之后为request body，直到空行或HTTP/1.x行
        # HTTP/1.x本行开始为response header，直到最近的一个空行，再之后为response body，直到空行或结尾行

        case_id = 0  # 请求编号，递增
        block_flag = 0  # 标识是否读取到一个合规的block，0-No，1-Yes
        req_head_flag = 0  # 标识是否读取到Request-Header，0-No，1-Yes
        req_body_flag = 0  # 标识是否读取到Request-Body，0-No，1-Yes
        res_head_flag = 0  # 标识是否读取到Response-Header，0-No，1-Yes
        res_body_flag = 0  # 标识是否读取到Response-Body，0-No，1-Yes

        sum_dict = {'IDS': []}  # 存储解析后的汇总信息，IDS内容为各条block的key list，保证顺序
        first_line = ''  # 参考.gor，格式化后的首行，可作为单个block的key
        end_line = ''  # 参考.gor，尾行，暂不使用

        i_protocol = ''  # 从block首行解析出
        i_method = ''  # 从block首行解析出
        i_url = ''  # 从block首行解析出
        i_host = ''  # 对应Host行
        i_param = ''  # 对应Request-Body中的内容，或block首行中的get传参
        i_header = {}  # 对应Request-Header中的内容，匹配config中的global_conf定义
        i_status = 0  # 对应HTTP/1.x行中的status code
        i_resp = ''  # 对应Response-Body中的内容，可能一行或多行
        i_time = 0  # 对应Date行，作为请求的发生时间，供回放时参考
        e_time = 0  # 请求结束时间，目前Fiddler导出中实际对应了Date字段，无请求开始时间，因此本字段暂不用

        req_header = self.mch.record_header  # 取自config中global_conf中的配置

        lines.append("----------------------------")  # 如果是单个请求导出的txt可能没有分割行，自动追加一个

        for my_line in lines:
            my_line = my_line.rstrip()  # 去掉行尾的空格、换行符
            # if my_line == '':  # empty line, ignore
            #    continue

            if block_flag == 0 and re.search(r"^(\w+) http", my_line):  # get a new http request
                block_flag = 1
                tmp_re = re.findall(r"(\w+) (((http\w*):\/\/[\w\.:]+).+) .+", my_line)[0]
                i_protocol = tmp_re[3]
                i_method = tmp_re[0]
                i_url = tmp_re[1].replace(tmp_re[2], '')

            elif block_flag and re.match(r"-----------------------\S+", my_line):  # block尾部，进行清算
                tmp_dict = {}
                tmp_dict['protocol'] = i_protocol
                tmp_dict['method'] = i_method
                if not i_param and re.match(r".+\?.+", i_url):  # 从url中提取传参
                    tmp_dict['url'] = i_url.split('?')[0]
                    tmp_dict['parameter'] = i_url.split('?')[1]
                else:
                    tmp_dict['url'] = i_url
                    tmp_dict['parameter'] = i_param
                tmp_dict['host'] = i_host
                tmp_dict['response'] = i_resp
                tmp_dict['header'] = json.dumps(i_header, ensure_ascii=False)
                tmp_dict['status'] = i_status
                tmp_dict['duration'] = 0  # 暂缺少开始时间，无法计算

                if first_line:
                    self.logger.info("Get its content, run against select/ignore/replace config")
                    # 根据配置的record中select/ignore，判断是否所需
                    if self.mch.if_selected(the_dict=tmp_dict):
                        # 根据配置的record.replace规则进行文本替换
                        tmp_dict = self.mch.replace_element(the_dict=tmp_dict)

                        case_id += 1
                        sum_dict[first_line].append({'id': "__CASE_%d" % case_id})
                        sum_dict[first_line].append({'protocol': tmp_dict['protocol']})
                        sum_dict[first_line].append({'method': tmp_dict['method']})
                        sum_dict[first_line].append({'host': tmp_dict['host']})
                        sum_dict[first_line].append({'url': tmp_dict['url']})
                        sum_dict[first_line].append({'parameter': tmp_dict['parameter']})
                        sum_dict[first_line].append({'header': tmp_dict['header']})
                        sum_dict[first_line].append({'status': tmp_dict['status']})
                        sum_dict[first_line].append({'duration_ms': tmp_dict['duration']})
                        sum_dict[first_line].append({'response': tmp_dict['response']})
                    else:
                        self.logger.info("Not selected by the config, ignore")
                        del sum_dict[first_line]
                        sum_dict['IDS'].remove(first_line)
                else:
                    self.logger.info("Not enough info, ignore")

                # 重置所有过程变量
                block_flag = req_head_flag = req_body_flag = res_head_flag = res_body_flag = 0
                first_line = i_protocol = i_method = i_url = i_host = i_param = i_resp = ''
                i_header = {}
                i_status = i_time = 0

            elif block_flag and re.match(r"^[\w\-_]+:.*", my_line):
                if re.search(r"^Date: (.+)", my_line):  # 解析到请求时间
                    i_time = re.findall(r"^Date: (.+)", my_line)[0]
                    # 生成first_line，作为block的key
                    first_line = self.__gor_block_start(i_url, i_time)
                    if not first_line:  # exception, ignore this block
                        block_flag = 0
                        continue

                    sum_dict[first_line] = []
                    sum_dict['IDS'].append(first_line)

                elif re.match(r"Host: .+", my_line):
                    i_host = re.findall(r"Host: (.+)", my_line)[0].strip()
                    self.logger.info("Find a request: %s" % i_url.split('?')[0])
                    req_head_flag = 1  # mark，下一行开始为request header内容
                elif req_head_flag:
                    for h_key in req_header:
                        if re.match(r"^" + h_key + ":", my_line):
                            if h_key not in i_header.keys():
                                i_header[h_key] = re.findall(r"^\S+:(.+)", my_line)[0].strip()
                            break
                else:
                    pass
            elif block_flag and re.match(r"^HTTP/.+", my_line):  # i_status所需
                try:
                    i_status = re.findall(r"HTTP/.+ (\d+) .+", my_line)[0]
                except IndexError as e:
                    i_status = re.findall(r"HTTP/.+ (\d+).*", my_line)[0]
                res_head_flag = 1  # mark，本行开始为response header内容

            elif block_flag and my_line == '':  # 读取到空行，为header和body的间隔
                if res_body_flag:
                    res_body_flag = 0  # response body读取结束
                if req_body_flag:
                    req_body_flag = 0  # request body读取结束
                if req_head_flag:
                    req_body_flag = 1  # mark，后续的非空行为request body内容
                    req_head_flag = 0  # request header读取结束
                if res_head_flag:
                    res_body_flag = 1  # mark，后续的非空行为response body内容
                    res_head_flag = 0  # response header读取结束
                    req_body_flag = 0  # request body读取结束

            elif block_flag:  # 常规行
                if req_body_flag:
                    i_param += my_line
                if res_body_flag:
                    i_resp += my_line
            else:
                pass

        # print json.dumps(sum_dict, ensure_ascii=False)
        return sum_dict

    # 解析Charles trace，获取回放和验证的必要内容
    def __parse_charles_blocks(self, lines):
        """ charles trace文件关键信息示例：
Method: POST
Protocol: http
File: /api
Start-Time: 2019-02-28T20:00:44.850+08:00
End-Time: 2019-02-28T20:00:44.858+08:00

Request-Header:<<--EOF-1551355379344-
Host: x.x.x.x:8080
Accept: */*
X-Requested-With: XMLHttpRequest
User-Agent: Mozilla/5.0 (Linux; Android 9.0; MIX 2S Build/PKQ1.180729.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/6.2 TBS/044408 Mobile Safari/537.36 MMWEBID/7049 MicroMessenger/7.0.3.1400(0x2700033A) Process/tools NetType/WIFI Language/zh_CN
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,en-US;q=0.8
Connection: keep-alive
--EOF-1551355379344-

Response-Header:<<--EOF-1551355379344-
HTTP/1.0 200 OK
--EOF-1551355379344-

Request-Body:<<--EOF-1551355379345-
para=%7B%22TimeStamp%22%3A1551355237000%2C%22UserId%22%3A%22083e29e59c0b257813af7cb454b1e0e9%22%2C%22Token%22%3A%22w6XCs4YqWnIEbJpDKvQHtMr7OZ8Rjkyl%22%2C%22From%22%3A%22SuZhou%22%2C%22To%22%3A%22ShangHai%22%7D&sign=a1a701bba725365964ec7c5b79d988ed
--EOF-1551355379345-

Response-Body:<<--EOF-1551355379345-
{"status": 200, "timestamp": 1551355245, "sign": "202cb962ac59075b964b07152d234b70", "token": "02OwZTe7cLYDEA3JbXxRq1udijz4VGSM", "message": "Success", "data": {"date": "20190228", "from": "SuZhou", "list": [{"status": ["Unknown"], "levels": {"A": 5, "C": 1, "B": 1}, "tag": "YO3S58DuJAfbkoVt6epmyvazsl7RBj", "number": 121, "time": "07:00"}, {"status": ["Busy"], "levels": {"A": 5, "C": 0, "B": 1}, "tag": "bwaKROHZW2zFfLBC4QEet6VYDJGhk9", "number": 122, "time": "08:30"}, {"status": ["Available"], "levels": {"A": 4, "C": 0, "B": 2}, "tag": "p2N5CflD8OWajTKi9AIBRExnF4zubv", "number": 123, "time": "10:15"}], "userid": 123456, "to": "ShangHai"}}
--EOF-1551355379345-
        """
        case_id = 0  # 请求编号，递增
        block_flag = 0  # 标识是否读取到一个合规的block，0-No，1-Yes
        req_head_flag = 0  # 标识是否读取到Request-Header，0-No，1-Yes
        req_body_flag = 0  # 标识是否读取到Request-Body，0-No，1-Yes
        res_head_flag = 0  # 标识是否读取到Response-Header，0-No，1-Yes
        res_body_flag = 0  # 标识是否读取到Response-Body，0-No，1-Yes

        i_protocol = ''  # 对应Protocol行
        i_method = ''  # 对应Method行
        i_url = ''  # 对应File行
        i_host = ''  # 对应Request-Header中的Host行
        i_param = ''  # 对应Request-Body中的内容，或File中的get传参
        i_header = {}  # 对应Request-Header中的内容，匹配config中的global_conf定义
        i_status = 0  # 对应HTTP/1.x行中的status code
        i_resp = ''  # 对应Response-Body中的内容，可能一行或多行
        i_time = 0  # 对应Start-Time行，作为请求的发生时间，供回放时参考
        e_time = 0  # 对应End-Time行，作为请求的结束时间，计算请求整体耗时
        # 定义映射关系，方便解析时的赋值
        my_map = {
            'Method': 'i_method',
            'Protocol': 'i_protocol',
            # 'Host': 'i_host',
            'File': 'i_url',
            'Start-Time': 'i_time',
            'End-Time': 'e_time',
        }
        for my_key in my_map.keys():
            exec (my_map[my_key] + '=None')

        sum_dict = {'IDS': []}  # 存储解析后的汇总信息，IDS内容为各条block的key list，保证顺序
        first_line = ''  # 参考.gor，格式化后的首行，可作为单个block的key
        end_line = ''  # 参考.gor，尾行，暂不使用

        req_header = self.mch.record_header  # 取自config中global_conf中的配置

        for my_line in lines:
            my_line = my_line.rstrip()  # 去除行尾空格、回车符
            if my_line == '':  # 忽略空行
                continue

            if block_flag == 0 and re.match(r"^Method: \w+", my_line):  # 读取到一个新的block
                block_flag = 1  # flag做标记
                # 解析得到Method
                tmp_val = re.findall(r"Method: (\w+)", my_line)[0]
                exec(my_map['Method']+'=tmp_val')

            elif block_flag and re.match(r"Request-Header:.+", my_line):  # mark，后续行有i_header所需
                req_head_flag = 1
            elif block_flag and re.match(r"Request-Body:.+", my_line):  # mark，后续行有i_param所需
                req_body_flag = 1
            elif block_flag and re.match(r"Response-Header:.+", my_line):  # mark，后续行有i_status所需
                res_head_flag = 1
            elif block_flag and re.match(r"Response-Body:.+", my_line):  # mark，后续行有i_resp所需
                res_body_flag = 1
            elif block_flag and re.match(r"--EOF-.+", my_line):  # header或body结束，需做过程清算
                if not res_body_flag:  # 尚未到block结尾，重置部分flag
                    req_head_flag = req_body_flag = res_head_flag = 0
                    continue

                # 则此时已读取到一个block的末尾，做最终清算
                tmp_dict = {}
                tmp_dict['protocol'] = eval(my_map['Protocol'])
                tmp_dict['method'] = eval(my_map['Method'])
                tmp_dict['host'] = i_host
                if not i_param and re.match(r".+\?.+", eval(my_map['File'])):  # 从url中提取传参
                    tmp_dict['url'] = eval(my_map['File']).split('?')[0]
                    tmp_dict['parameter'] = eval(my_map['File']).split('?')[1]
                else:
                    tmp_dict['url'] = eval(my_map['File'])
                    tmp_dict['parameter'] = i_param
                tmp_dict['header'] = json.dumps(i_header, ensure_ascii=False)
                tmp_dict['status'] = i_status
                tmp_dict['response'] = i_resp
                tmp_dict['start-time'] = int(self.__timestamp(eval(my_map['Start-Time'])))
                tmp_dict['end-time'] = int(self.__timestamp(eval(my_map['End-Time'])))
                tmp_dict['duration'] = int(self.__timestamp(eval(my_map['End-Time']))) - int(self.__timestamp(eval(my_map['Start-Time'])))

                if first_line:
                    self.logger.info("Get its content, run against select/ignore/replace config")
                    # 根据配置的record中select/ignore，判断是否所需
                    if self.mch.if_selected(the_dict=tmp_dict):
                        # 根据配置的record.replace规则进行文本替换
                        tmp_dict = self.mch.replace_element(the_dict=tmp_dict)

                        case_id += 1
                        sum_dict[first_line].append({'id': "__CASE_%d" % case_id})
                        sum_dict[first_line].append({'protocol': tmp_dict['protocol']})
                        sum_dict[first_line].append({'method': tmp_dict['method']})
                        sum_dict[first_line].append({'host': tmp_dict['host']})
                        sum_dict[first_line].append({'url': tmp_dict['url']})
                        sum_dict[first_line].append({'parameter': tmp_dict['parameter']})
                        sum_dict[first_line].append({'header': tmp_dict['header']})
                        sum_dict[first_line].append({'status': tmp_dict['status']})
                        # sum_dict[first_line].append({'start-time': tmp_dict['start-time']})
                        # sum_dict[first_line].append({'end-time': tmp_dict['end-time']})
                        sum_dict[first_line].append({'duration_ms': tmp_dict['duration']})
                        sum_dict[first_line].append({'response': tmp_dict['response']})
                    else:
                        self.logger.info("Not selected by the config, ignore")
                        del sum_dict[first_line]
                        sum_dict['IDS'].remove(first_line)
                else:
                    self.logger.info("Not enough info, ignore")

                # 重置所有过程变量
                block_flag = req_head_flag = req_body_flag = res_head_flag = res_body_flag = 0
                first_line = i_protocol = i_method = i_url = i_host = i_param = i_resp = ''
                i_header = {}
                i_status = i_time = 0
                for my_key in my_map.keys():
                    exec (my_map[my_key] + '=None')
            elif block_flag and req_head_flag:  # 读取到i_host和i_header所需
                if re.match(r"^Host:", my_line):
                    i_host = re.findall(r"^\S+:\s*(\S+)", my_line)[0].strip()
                for h_key in req_header:
                    if re.match(r"^"+h_key+":", my_line):
                        i_header[h_key] = re.findall(r"^\S+:(.+)", my_line)[0].strip()
                        break
            elif block_flag and req_body_flag:  # 读取到i_param所需
                i_param = str(my_line) if i_param == '' else i_param + str(my_line)
            elif block_flag and res_head_flag and re.match(r"HTTP/.+", my_line):  # 读取到i_status所需
                try:
                    i_status = re.findall(r"HTTP/.+ (\d+) .+", my_line)[0]
                except IndexError:
                    i_status = re.findall(r"HTTP/.+ (\d+).*", my_line)[0]
            elif block_flag and res_body_flag:  # 读取到i_resp所需
                i_resp = str(my_line) if i_resp == '' else i_resp + str(my_line)

            elif block_flag and re.match(r"^(\S+):.+", my_line):  # 读取常规行
                the_item = re.findall(r"^(\S+):\s*(\S+)", my_line)
                the_key = the_item[0][0].strip()
                the_val = the_item[0][1].strip()

                if the_key in my_map.keys():  # 是所需，则留存
                    exec(my_map[the_key]+'=the_val')
                else:
                    continue

                if eval(my_map['File']) and eval(my_map['Start-Time']) and (not first_line):
                    # 生成first_line作为该block的key
                    first_line = self.__gor_block_start(eval(my_map['File']), eval(my_map['Start-Time']))
                    if not first_line:
                        block_flag = 0
                        for my_key in my_map.keys():  # 重置map字典
                            exec (my_map[my_key] + '=None')
                        continue
                    sum_dict[first_line] = []
                    sum_dict['IDS'].append(first_line)
                    self.logger.info("Find a request: %s" % eval(my_map['File']).split('?')[0])
            else:
                continue

        # print json.dumps(sum_dict, ensure_ascii=False)
        return sum_dict

    def fiddler_to_ini(self, source, target):
        """
        :param source: 源文件，要求是Fiddler导出的txt格式
        :param target: 目标文件名
        :return: 解析后的完整字典数据
        """
        self.logger.info("Start to parse %s" % source)

        my_lines = self.__read_file(source)
        self.logger.debug("The lines: %s" % json.dumps(my_lines, ensure_ascii=False))

        my_dict = self.__parse_fiddler_blocks(my_lines)
        self.logger.debug("The dict: %s" % json.dumps(my_dict, ensure_ascii=False))

        self.logger.info("Parser finished, write into ini file: %s" % target)
        MyIniHelper.dict2ini(content=my_dict, filename=target)
        self.logger.info("Done.")

        return my_dict

    def charles_to_ini(self, source, target):
        """
        :param source: 源文件，要求是Charles导出的trace格式
        :param target: 目标文件名
        :return: 解析后的完整字典数据
        """
        self.logger.info("Start to parse %s" % source)

        my_lines = self.__read_file(source)
        self.logger.debug("The lines: %s" % json.dumps(my_lines, ensure_ascii=False))

        my_dict = self.__parse_charles_blocks(lines=my_lines)
        self.logger.debug("The dict: %s" % json.dumps(my_dict, ensure_ascii=False))

        self.logger.info("Parser finished, write into ini file: %s" % target)
        MyIniHelper.dict2ini(content=my_dict, filename=target)
        self.logger.info("Done.")

        return my_dict


if __name__ == '__main__':
    from config.config import *
    import yaml
    print "Charles.trace to ini:", json.dumps(
        MyParser(conf=MyConfigHelper(project=yaml.load(open('../../config/demo.yaml'), Loader=yaml.FullLoader))).charles_to_ini(
            source='../../data/demo.trace',
            target='../../test/debug0.ini'),
        ensure_ascii=False)
    print "Fiddler.txt to ini:", json.dumps(
        MyParser(conf=MyConfigHelper(project=yaml.load(open('../../config/demo.yaml'), Loader=yaml.FullLoader))).fiddler_to_ini(
            source='../../test/sample.txt',
            target='../../test/debug1.ini'),
        ensure_ascii=False)
