# -*- coding: utf-8 -*-
# --------------------------------------------------------------
#   When        Who         What
# --------------------------------------------------------------
# Jan 18,2019   idle-man    Create IniHelper to read/write ini file
# Jan 28,2019   idle-man    Create ConfigHelper to handle config operations
# Mar 12,2019   idle-man    Rebuild ConfigHelper based on new config settings
# Mar 21,2019   idle-man    Support wait option in ConfigHelper
# Mar 27,2019   idle-man    Support id config in ConfigHelper
#

import json
import re
import ConfigParser
from copy import deepcopy
from time import sleep

from module.common.helper import MyDictHelper
from module.common.logger import Logger
from config.config import *
from module.tool import *


class MyConfigHelper:
    __author__ = 'idle-man'
    __desc__ = "项目配置文件的相关操作"

    def __init__(self, project=default_conf, section='record', logger=None):
        if not logger:
            self.logger = Logger()
        else:
            self.logger = logger
        self.project = project
        self.section = section
        (self.record_select_list,
         self.record_ignore_list,
         self.record_replace_list,
         self.record_store_list,
         self.record_rule_list,
         self.record_wait_list) = self.__init_list('record')
        (self.replay_select_list,
         self.replay_ignore_list,
         self.replay_replace_list,
         self.replay_store_list,
         self.replay_rule_list,
         self.replay_wait_list) = self.__init_list('replay')
        (self.check_select_list,
         self.check_ignore_list,
         self.check_replace_list,
         self.check_store_list,
         self.check_rule_list,
         self.check_wait_list) = self.__init_list('check')

        self.global_var_dict = {}  # 用于存储过程变量，store和replace使用
        self.record_header = global_conf['record']['header'] if 'header' in global_conf['record'].keys() else []
        self.replay_timeout = int(global_conf['replay']['timeout']) if 'timeout' in global_conf['replay'].keys() else 5
        self.replay_type = int(global_conf['replay']['type']) if 'type' in global_conf['replay'].keys() else 1
        self.replay_max_retry = int(global_conf['replay']['max_retry']) if 'max_retry' in global_conf['replay'].keys() else 1
        self.replay_wait = 0

    # 读取config配置，并进行默认值处理、格式补救
    def __init_list(self, section):
        p_conf = self.project

        if section == 'check':
            select_list = []
            ignore_list = []
        else:
            select_list = {'host': [], 'url': [], 'id': []}
            ignore_list = {'host': [], 'url': [], 'id': []}
        replace_list = {'host': [], 'url': [], 'param': [], 'header': []}
        store_list = []
        rule_list = {}
        wait_list = {'time': {}, 'rule': {}}

        if section in p_conf.keys():
            if 'select' in p_conf[section].keys():
                if section == 'check':
                    select_list = self.__list_format(p_conf[section]['select'])
                else:
                    if 'host' in p_conf[section]['select'] and p_conf[section]['select']['host'] > 0:
                        select_list['host'] = self.__list_format(p_conf[section]['select']['host'])
                    if 'url' in p_conf[section]['select'] and p_conf[section]['select']['url'] > 0:
                        select_list['url'] = self.__list_format(p_conf[section]['select']['url'])
                    if 'id' in p_conf[section]['select'] and p_conf[section]['select']['id'] > 0:
                        select_list['id'] = self.__list_format(p_conf[section]['select']['id'])

            if 'ignore' in p_conf[section].keys():
                if section == 'check':
                    ignore_list = self.__list_format(p_conf[section]['ignore'])
                else:
                    if 'host' in p_conf[section]['ignore'] and p_conf[section]['ignore']['host'] > 0:
                        ignore_list['host'] = self.__list_format(p_conf[section]['ignore']['host'])
                    if 'url' in p_conf[section]['ignore'] and p_conf[section]['ignore']['url'] > 0:
                        ignore_list['url'] = self.__list_format(p_conf[section]['ignore']['url'])
                    if 'id' in p_conf[section]['ignore'] and p_conf[section]['ignore']['id'] > 0:
                        ignore_list['id'] = self.__list_format(p_conf[section]['ignore']['id'])

            if 'replace' in p_conf[section].keys():
                if 'host' in p_conf[section]['replace'].keys() and p_conf[section]['replace']['host'] > 0:
                    replace_list['host'] = self.__list_format(p_conf[section]['replace']['host'])
                if 'url' in p_conf[section]['replace'].keys() and p_conf[section]['replace']['url'] > 0:
                    replace_list['url'] = self.__list_format(p_conf[section]['replace']['url'])
                if 'param' in p_conf[section]['replace'].keys() and p_conf[section]['replace']['param'] > 0:
                    replace_list['param'] = self.__list_format(p_conf[section]['replace']['param'])
                if 'header' in p_conf[section]['replace'].keys() and p_conf[section]['replace']['header'] > 0:
                    replace_list['header'] = self.__list_format(p_conf[section]['replace']['header'])

            if 'store' in p_conf[section].keys() and p_conf[section]['store'] > 0:
                store_list = self.__list_format(p_conf[section]['store'])

            if 'rule' in p_conf[section].keys() and p_conf[section]['rule'] > 0:
                rule_list = self.__dict_format(p_conf[section]['rule'])

            if 'wait' in p_conf[section].keys():
                if 'time' in p_conf[section]['wait'].keys() and p_conf[section]['wait']['time'] > 0:
                    wait_list['time'] = self.__dict_format(p_conf[section]['wait']['time'])
                if 'rule' in p_conf[section]['wait'].keys() and p_conf[section]['wait']['rule'] > 0:
                    wait_list['rule'] = self.__dict_format(p_conf[section]['wait']['rule'])

        return select_list, ignore_list, replace_list, store_list, rule_list, wait_list

    @staticmethod
    def __list_format(my_list):
        if isinstance(my_list, (set, tuple)):
            my_list = list(my_list)
        elif isinstance(my_list, (str, int, float, bool)):
            my_list = [my_list, ]
        elif isinstance(my_list, dict):
            my_list = my_list.keys()
        if not isinstance(my_list, list):  # 补救失败，默认为空
            my_list = []
        return my_list

    @staticmethod
    def __dict_format(my_dict):
        tmp_dict = {}
        if isinstance(my_dict, (set, list, tuple)):
            for my_item in my_dict:
                tmp_dict[str(my_item.split('=>')[0]).strip()] = str(my_item.split('=>')[1]).strip()
        if not isinstance(my_dict, dict):
            my_dict = tmp_dict
        return my_dict

    # set section at runtime
    def set_section(self, section):
        self.section = section

    # 根据配置，匹配一个请求是选中，还是忽略
    def if_selected(self, the_dict):
        """
        :param the_dict: 完整的request字典，可由ini解析而来
        :return: True-选中 or False-忽略
        """
        if not ('host' in the_dict.keys() and 'url' in the_dict.keys()):
            return True  # 默认选中

        if self.section.lower() == 'replay':
            select_list = self.replay_select_list
            ignore_list = self.replay_ignore_list
        else:  # 默认为record
            select_list = self.record_select_list
            ignore_list = self.record_ignore_list

        # 先匹配host，完整匹配
        if len(select_list['host']) > 0 and the_dict['host'] not in select_list['host']:
            return False
        if len(ignore_list['host']) > 0 and the_dict['host'] in ignore_list['host']:
            return False

        # 再匹配id，完整匹配
        if len(select_list['id']) > 0 and the_dict['id'] not in select_list['id']:
            return False
        if len(ignore_list['id']) > 0 and the_dict['id'] in ignore_list['id']:
            return False

        # 再匹配url，局部匹配
        if len(select_list['url']) > 0:
            for select_req in select_list['url']:
                if re.match(r"[\/]?" + select_req + "[\/|\?]?.*", the_dict['url']):
                    return True
            return False  # 定义了select，但都未匹配到，则可理解为需要忽略
        if len(ignore_list['url']) > 0:
            for ignore_req in ignore_list['url']:
                if re.search(r"[\/]?" + ignore_req + "[\/|\?]?.*", the_dict['url']):
                    return False

        return True  # 默认为选中

    # 根据配置，对请求的url进行文本替换
    def replace_element(self, the_dict):
        """
        :param the_dict: 完整的request字典，可由ini解析而来
        :return: 按规则进行文本替换后的字典
        """
        if self.section == 'replay':
            replace_list = self.replay_replace_list
        else:  # 'record' as default
            replace_list = self.record_replace_list

        my_dict = deepcopy(the_dict)

        try:
            for my_ele in replace_list['host']:  # 对host的替换
                if len(my_ele.split('=>')) > 1:
                    rp_key = my_ele.split('=>')[0].strip()
                    rp_val = my_ele.split('=>')[1].strip()
                    my_dict['host'] = my_dict['host'].replace(rp_key, rp_val)
                else:  # 未按格式定义，忽略
                    continue
            for my_ele in replace_list['url']:  # 对url的替换
                if len(my_ele.split('=>')) > 1:
                    rp_key = my_ele.split('=>')[0].strip()
                    rp_val = my_ele.split('=>')[1].strip()
                    my_dict['url'] = my_dict['url'].replace(rp_key, rp_val)
                else:  # 未按格式定义，忽略
                    continue
            for my_ele in replace_list['header']:
                if not isinstance(my_dict['header'], dict):
                    my_dict['header'] = json.loads(my_dict['header'])

                if len(my_ele.split('=>')) > 1:
                    rp_key = my_ele.split('=>')[0].strip()
                    rp_val = my_ele.split('=>')[1].strip()
                    # print rp_key, rp_val, self.global_var_dict
                    # 判定val有无使用{{}}函数调用格式
                    if re.match(r"^{{.+}}$", rp_val):
                        try:
                            _val = str(eval(str(re.findall(r"^{{(.+)}}$", rp_val)[0]).strip()))
                        except NameError or TypeError as e:
                            self.logger.error("Failed to execute %s with exception: %s" %
                                              (str(re.findall(r"^{{(.+)}}$", rp_val)[0]).strip(), e))
                            continue
                    # 判定val有无使用{}全局变量格式
                    elif re.match(r"^{\S+}$", rp_val):
                        _val = re.findall(r"^{(\S+)}$", rp_val)[0]
                        if _val not in self.global_var_dict.keys():  # 若该过程变量此前未存储，则不做替换
                            continue
                        else:
                            _val = str(self.global_var_dict[_val])
                    else:
                        _val = rp_val

                    # 判定key有无使用{{}}函数调用格式
                    if re.match(r"^{{.+}}$", rp_key):
                        try:
                            _key = str(eval(str(re.findall(r"^{{(.+)}}$", rp_key)[0]).strip()))
                            my_dict['header'] = json.loads(json.dumps(my_dict['header']).replace(_key, _val))
                        except NameError or TypeError as e:
                            self.logger.error("Failed to execute %s with exception: %s" %
                                              (str(re.findall(r"^{{(.+)}}$", rp_key)[0]).strip(), e))
                            continue
                    # 先判定key是否为{}全局变量格式
                    elif re.match(r"^.*{\S+}$", rp_key):
                        _prefix = re.findall(r"^(.*){(\S+)}$", rp_key)[0][0]
                        _key = re.findall(r"^(.*){(\S+)}$", rp_key)[0][1]
                        if _prefix != '':  # 指定了特定的api
                            _prefix = _prefix.split('::')[0]
                            # 判定是否采用case id前缀
                            if re.match(r"^__CASE_", str(_prefix)):
                                if _prefix != the_dict['id']:  # id不匹配，忽略
                                    continue
                            # 判定是否匹配url
                            elif not re.match(r".*" + _prefix + ".*", the_dict['url']):  # url不匹配，忽略
                                continue

                        if re.match(r".+::.+", _key):  # 使用的是过程变量
                            if _key in self.global_var_dict.keys():
                                _key = str(self.global_var_dict[_key])
                                my_dict['header'] = json.loads(json.dumps(my_dict['header']).replace(_key, _val))
                            else:
                                continue
                        else:  # 使用的是传参中的key
                            my_dict['header'][_key] = _val

                    else:
                        if len(rp_key.split('::')) > 1:  # 指定了特定的api
                            _prefix = rp_key.split('::')[0]
                            _key = rp_key.split('::')[1]
                            # 判定是否采用case id前缀
                            if re.match(r"^__CASE_", str(_prefix)):
                                if _prefix != the_dict['id']:  # id不匹配，忽略
                                    continue
                            # 判定是否匹配url
                            elif not re.match(r".*" + _prefix + ".*", the_dict['url']):  # url不匹配，忽略
                                continue
                        else:
                            _key = rp_key

                        my_dict['header'] = json.loads(json.dumps(my_dict['header']).replace(_key, _val))

                else:  # 未按格式定义，忽略
                    continue
            for my_ele in replace_list['param']:
                if len(my_ele.split('=>')) > 1:
                    rp_key = my_ele.split('=>')[0].strip()
                    rp_val = my_ele.split('=>')[1].strip()
                    # print rp_key, rp_val, self.global_var_dict
                    # 判定val有无使用{{}}函数调用格式
                    if re.match(r"^{{.+}}$", rp_val):
                        try:
                            _val = str(eval(str(re.findall(r"^{{(.+)}}$", rp_val)[0]).strip()))
                        except NameError or TypeError as e:
                            self.logger.error("Failed to execute %s with exception: %s" %
                                              (str(re.findall(r"^{{(.+)}}$", rp_val)[0]).strip(), e))
                            continue
                    # 判定val有无使用{}全局变量格式
                    elif re.match(r"^{\S+}$", rp_val):
                        _val = re.findall(r"^{(\S+)}$", rp_val)[0]
                        if _val not in self.global_var_dict.keys():  # 若该过程变量此前未存储，则不做替换
                            continue
                        else:
                            _val = str(self.global_var_dict[_val])
                    else:
                        _val = rp_val

                    # 判定key有无使用{{}}函数调用格式
                    if re.match(r"^{{.+}}$", rp_key):
                        try:
                            _key = str(eval(str(re.findall(r"^{{(.+)}}$", rp_key)[0]).strip()))
                            my_dict['parameter'] = my_dict['parameter'].replace(_key, _val)
                        except NameError or TypeError as e:
                            self.logger.error("Failed to execute %s with exception: %s" %
                                              (str(re.findall(r"^{{(.+)}}$", rp_key)[0]).strip(), e))
                            continue
                    # 判定key是否为{}全局变量格式
                    elif re.match(r"^.*{\S+}$", rp_key):
                        _prefix = re.findall(r"^(.*){(\S+)}$", rp_key)[0][0]
                        _key = re.findall(r"^(.*){(\S+)}$", rp_key)[0][1]
                        if _prefix != '':  # 指定了特定的api
                            _prefix = _prefix.split('::')[0]
                            # 判定是否采用case id前缀
                            if re.match(r"^__CASE_", str(_prefix)):
                                if _prefix != the_dict['id']:  # id不匹配，忽略
                                    continue
                            # 判定是否匹配url
                            elif not re.match(r".*" + _prefix + ".*", the_dict['url']):  # url不匹配，忽略
                                continue

                        if re.match(r".+::.+", _key):  # 使用的是过程变量
                            if _key in self.global_var_dict.keys():
                                _key = str(self.global_var_dict[_key])
                                my_dict['parameter'] = my_dict['parameter'].replace(_key, _val)
                            else:
                                continue
                        else:  # 使用的是传参中的key
                            _param = MyDictHelper.param2dict(item=my_dict['parameter'])
                            _param[_key] = _val
                            my_dict['parameter'] = MyDictHelper.dict2param(item=_param)

                    else:
                        if len(rp_key.split('::')) > 1:  # 指定了特定的api
                            _prefix = rp_key.split('::')[0]
                            _key = rp_key.split('::')[1]
                            # 判定是否采用case id前缀
                            if re.match(r"^__CASE_", str(_prefix)):
                                if _prefix != the_dict['id']:  # id不匹配，忽略
                                    continue
                            # 判定是否匹配url
                            elif not re.match(r".*" + _prefix + ".*", the_dict['url']):  # url不匹配，忽略
                                continue
                        else:
                            _key = rp_key

                        my_dict['parameter'] = my_dict['parameter'].replace(_key, _val)

                else:  # 未按格式定义，忽略
                    continue
        except Exception as e:
            # print "Exception:", e.message
            pass

        return my_dict

    # 根据配置，对请求的传参和响应结果进行过程存储，用于replace之用
    def store_element(self, the_dict, mode=None, when='after'):
        """
        :param the_dict: 完整的request字典，可由ini解析而来
        :param mode: 列表，有效值：resp、param、header，默认为全部
        :param when: 存储发生在request之前or之后，有效值：after、before
        :return: 
        """
        if self.section.lower() == 'replay':
            store_list = self.replay_store_list
        else:
            return False
        if not (store_list and the_dict):
            return False

        for my_ele in store_list:
            my_keys = my_ele.split('::')
            if len(my_keys) == 3:  # 标准格式
                my_api = my_keys[0]
                my_mod = my_keys[1]
                my_key = my_keys[2]
            elif len(my_keys) == 2:  # 缺省为resp
                my_api = my_keys[0]
                my_mod = 'resp'
                my_key = my_keys[1]
            else:  # 无效配置，忽略
                continue

            # 若指定了mode，且mode有效，则根据mode进行判断，不在mode中的无需执行
            if mode and isinstance(mode, (list, set, tuple)) and my_mod not in mode:
                continue

            try:
                # 判定是否采用case id前缀
                if re.match(r"^__CASE_", str(my_api)):
                    if my_api != the_dict['id']:
                        continue
                # 根据url判定是否需要执行store，未命中则下一个
                elif not re.match(r".*"+my_api+".*", the_dict['url']):
                    continue
                if my_mod in ('param', 'parameter'):  # 匹配传参，单层级
                    my_dict = MyDictHelper.param2dict(item=the_dict['parameter'])
                elif my_mod in ('resp', 'response'):  # 匹配响应结果，多层级
                    if when.lower() == 'before':  # 执行前存储的话，仅对__OLD__标识的生效
                        if not re.match(r"^__OLD__\.", str(my_key)):
                            continue
                    elif re.match(r"^__OLD__\.", str(my_key)):
                        continue
                    else:
                        pass
                    my_dict = MyDictHelper().get_all_items(item=json.loads(the_dict['response']))
                elif my_mod in ('header', 'head'):  # 匹配header，单层级
                    if isinstance(the_dict['header'], dict):
                        my_dict = the_dict['header']
                    else:
                        my_dict = json.loads(the_dict['header'])
                else:  # 无效配置，忽略
                    continue
                # 判定是否使用了__OLD__.前缀
                if re.match(r"^__old__\.", str(my_key).lower()):
                    my_key = re.findall(r"^__OLD__\.(.+)", str(my_key))[0]
                if my_key in my_dict.keys():
                    self.global_var_dict[my_ele] = my_dict[my_key]
                else:  # key定义不匹配，忽略
                    continue
            except Exception as e:  # 集中捕获异常
                continue
        return True

    # 根据配置，判断一个请求执行后是否需要wait，若需要则执行wait操作
    def need_wait(self, the_dict):
        """
        :param the_dict: 完整的request字典，可由ini解析而来
        :return: True - 成功，False - 失败，需要重复执行
        """
        if self.section.lower() == 'replay':
            wait_list = self.replay_wait_list
        else:  # 默认不需要wait
            return True

        try:
            # wait固定时长
            for my_api, my_time in wait_list['time'].items():
                if re.match(r"^__CASE_", str(my_api)):
                    if my_api != the_dict['id']:
                        continue
                # 根据url判断是否为需要wait的api
                elif not re.match(r".*" + my_api + ".*", the_dict['url']):
                    continue
                self.logger.info("Run wait action as config %s: %s" % (str(my_api), str(my_time)))
                sleep(int(my_time))
                self.replay_wait += int(my_time)
                return True
            # 按rule判断是否需要重试
            if len(wait_list['rule'].keys()) == 0:
                return True
            _my_dict = MyDictHelper().get_all_items(item=json.loads(the_dict['response']), mode=0)
            for my_key, my_rule in wait_list['rule'].items():  # 验证response是否符合预期，不符合则重复执行
                if len(my_key.split('::')) != 2:
                    self.logger.warn("Invalid wait rule config %s: %s" % (str(my_key), str(my_rule)))
                    continue
                w_api = my_key.split('::')[0]
                w_key = my_key.split('::')[1]
                # 先判定是否采用case id前缀
                if re.match(r"^__CASE_", str(w_api)):
                    if w_api != the_dict['id']:
                        continue
                # 根据url判断是否为需要wait的api
                elif not re.match(r".*" + w_api + ".*", the_dict['url']):
                    continue
                if w_key not in _my_dict.keys():
                    self.logger.warn("Invalid wait rule config %s: %s" % (str(my_key), str(my_rule)))
                    continue
                if not self.__match_rule(item=_my_dict[w_key], rule=my_rule):
                    self.logger.info("Run rule match %s:%s %s failed" % (str(w_key), str(_my_dict[w_key]), str(my_rule)))
                    return False
                self.logger.info("OK. Run rule match %s:%s %s succeed" % (str(w_key), str(_my_dict[w_key]),str(my_rule)))

        except Exception as e:
            self.logger.error("Exception in MyConfigHelper::need_wait: %s" % str(e))
            pass

        return True

    def __match_rule(self, item, rule):
        if isinstance(item, (int, long, float, dict, list, tuple, set)):
            i_rule = "%s" % item + str(rule)
        else:
            if len(str(item).split(' ')) == 1:
                i_rule = "%s" % item + str(rule)
            else:
                i_rule = "\'%s\'" % str(item) + str(rule)
        try:
            if not eval(i_rule):
                return False
        except SyntaxError or NameError as e:
            self.logger.warn(" * Match %s rule failed: %s" % (i_rule, e))
            pass
        return True


class MyIniHelper:
    __author__ = 'idle-man'
    __desc__ = "ini文件和字典数据的转换"

    def __init__(self):
        pass

    @staticmethod
    def ini2dict(filename, summary='IDS'):
        """
        :param filename: ini文件名称，附带路径
        :param summary: 一级key的汇总名称，可不关注
        :return: 字典数据
        """
        if summary == '':
            summary = 'IDS'
        else:
            summary = str(summary).strip()

        cfg_dic = {summary: []}
        cp = ConfigParser.ConfigParser()
        cp.read(filename)
        sec = cp.sections()
        for k1 in sec:
            cfg_dic[summary].append(k1)
            op = cp.options(k1)
            cfg_dic[k1.lower()] = {}
            for k2 in op:
                val = cp.get(k1, k2)
                # print k1, k2, val
                cfg_dic[k1.strip()][k2.strip()] = val
        return cfg_dic

    @staticmethod
    def dict2ini(content, filename, summary='IDS'):
        """
        :param content: 字典内容
        :param filename: ini文件名称，附带路径
        :param summary: 一级key的汇总名称，可不关注
        :return: filename
        """
        if summary == '':
            summary = 'IDS'
        else:
            summary = str(summary).strip()

        if re.match(r".+\.\w+$", filename):
            filename = str(re.findall(r"(.+)\.\w+$", filename)[0]) + '.ini'
        else:
            filename = str(filename) + '.ini'

        fw = open(filename, 'w')

        cp = ConfigParser.ConfigParser()
        if summary in content.keys():
            k_arr = content[summary]
        else:
            k_arr = content.keys()
        for k1 in k_arr:
            cp.add_section(k1)
            if isinstance(content[k1], (list, tuple, set)):
                for i in content[k1]:
                    for k2, val in i.items():
                        if isinstance(val, dict):
                            val = json.dumps(val, ensure_ascii=False)
                        if isinstance(val, unicode):  # 处理中文问题
                            val = val.encode('utf8')
                        cp.set(k1, k2, val)
            elif isinstance(content[k1], dict):
                for k2, val in content[k1].items():
                    if isinstance(val, dict):
                        val = json.dumps(val, ensure_ascii=False)
                    if isinstance(val, unicode):  # 处理中文问题
                        val = val.encode('utf8')
                    cp.set(k1, k2, val)
        cp.write(fw)

        fw.close()
        return filename


if __name__ == '__main__':
    mch = MyConfigHelper()
    mch.set_section(section='replay')
    mch.replay_ignore_list = {'url': ['apiA', ], 'id': [], 'host': []}
    mch.replay_store_list = [
        'api::resp::__OLD__.data.responseMessageKey',
        '__CASE_5::resp::data.responseMessageKey'
    ]
    mch.replay_replace_list = {
        'host': ['10.101.130.21:8080 => 10.101.130.21:8088'],
        'url': ['api => apiX'],
        'param': ['{api::resp::__OLD__.data.responseMessageKey} => {__CASE_5::resp::data.responseMessageKey}',
                  '1551355237000 => {{DaysLater(later=5, format="%Y%m%d")}}'],
        'header': ['__CASE_5::{token} => {__CASE_5::resp::data.responseMessageKey}',
                   '{date} => {{DaysAgo(ago=5, format="%Y-%m-%d")}}']
    }
    mch.replay_wait_list = {
        'time': {'api': 3},
        'rule': {'__CASE_5::status': '==200'}
    }
    my_dict = {
        'id': '__CASE_5',
        'protocol': 'http',
        'method': 'GET',
        'url': '/api',
        'host': '10.101.130.21:8080',
        'parameter': 'TimeStamp=1551355237000&UserId=e5fa4b0a-7b93-44e0-8840-c767ca4fb994&Token=w6XCs4YqWnIEbJpDKvQHtMr7OZ8Rjkyl&From=SuZhou&To=ShangHai',
        'header': '{"Accept-Language": "zh-CN,en-US;q=0.8", "Accept-Encoding": "gzip,", "Accept": "*/*", "User-Agent": "Mozilla/5.0", "Connection": "keep-alive", "X-Requested-With": "XMLHttpRequest"}',
        'status': 200,
        'duration_ms': 6,
        'response': '{"status": 200, "timestamp": 1551355242, "sign": "202cb962ac59075b964b07152d234b70", "token": "joFpAyZgTQ167lb3vthPDxVu8Y9eLd4J", "message": "Success", "data": {"responseMessageKey": "e5fa4b0a-7b93-44e0-8840-c767ca4fb994", "date": "20190228", "from": "SuZhou", "list": [{"status": ["Unknown"], "levels": {"A": 4, "C": 0, "B": 2}, "tag": "OiIMULbFc3v1HzrNu7CkWphXyt8V2q", "number": 121, "time": "07:00"}, {"status": ["Busy"], "levels": {"A": 2, "C": 1, "B": 2}, "tag": "DKUEOJxuk3yVTr4NGg0Zh6sdb1QW9R", "number": 122, "time": "08:30"}, {"status": ["Unknown"], "levels": {"A": 4, "C": 0, "B": 0}, "tag": "l4khiBSav9AwMIgeU5tTjqRWz3s8Q0", "number": 123, "time": "10:15"}], "userid": 123456, "to": "ShangHai"}}',
    }
    print mch.if_selected(the_dict=my_dict)
    mch.store_element(the_dict=my_dict, mode=['param', 'resp', 'header'], when='before')
    print mch.global_var_dict
    mch.store_element(the_dict=my_dict, mode=['param', 'resp', 'header'])
    print mch.global_var_dict
    mch.global_var_dict['__CASE_5::resp::data.responseMessageKey'] = 'abcdefghijklmn'
    print json.dumps(mch.replace_element(the_dict=my_dict))
    print mch.need_wait(the_dict=my_dict)
