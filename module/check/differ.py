# -*- coding: utf-8 -*-
# --------------------------------------------------------------
#   When        Who         What
# --------------------------------------------------------------
# Jan 17,2019   idle-man    Create
# Feb 27,2019   idle-man    Rebuild dict diff and support select / rule option
#
import json
from copy import deepcopy
from module.common.helper import MyDictHelper
from module.common.logger import Logger


class MyDiffer:
    __author__ = 'idle-man'
    __desc__ = "对比两个字典/列表，输出差异"

    def __init__(self, logger=None):
        self.dh = MyDictHelper()
        if not logger:
            self.logger = Logger()
        else:
            self.logger = logger

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

    def __my_dict_diff(self, first, second, select=None, ignore=None, rule=None):
        """
        :param first: 基准字典
        :param second: 对比字典
        :param select: select配置列表
        :param ignore: ignore配置列表
        :param rule: rule配置列表
        :param api: 特定接口，默认全部
        :return: 
        """
        dict1 = self.dh.get_all_items(item=first)
        dict2 = self.dh.get_all_items(item=second)
        self.logger.debug("Dict1: " + json.dumps(dict1, ensure_ascii=False))
        self.logger.debug("Dict2: " + json.dumps(dict2, ensure_ascii=False))

        diff_ret = {}
        add_keys = []
        change_keys = []
        remove_keys = []
        match_keys = []
        unmatch_keys = []
        right_keys = []

        if rule and len(rule.keys()) > 0:  # 先执行规则匹配
            # 规则匹配仅针对回放结果
            r_dict = self.dh.get_all_items(item=second, mode=0)

            # print json.dumps(r_dict)
            for r_k, r_v in rule.items():
                # 如果配置中定义了select，则仅被指定的节点及其子节点需要diff，其余ignore
                if select and not self.dh.is_descendant_node(r_k, select):
                    continue
                # 如果配置中定义了ignore，则被指定的节点及其子节点都需要ignore
                if ignore and self.dh.is_descendant_node(r_k, ignore):
                    continue

                if r_k not in r_dict.keys():
                    self.logger.warn("Invalid rule config %s: %s" % (str(r_k), str(r_v)))
                    continue
                if not self.__match_rule(item=r_dict[r_k], rule=r_v):
                    diff_ret[r_k] = ('unmatch', r_k, (r_v, r_dict[r_k]))
                    self.logger.debug("This key: " + str(r_k) + " does not match this rule: " + str(r_v))
                    unmatch_keys.append(r_k)
                else:
                    self.logger.debug("OK. This key: " + str(r_k) + " matches this rule: " + str(r_v))
                    match_keys.append(r_k)
                    right_keys.append(r_k)

        # 先遍历回放结果
        for key2 in dict2:
            # 如果配置中定义了select，则仅被指定的节点及其子节点需要diff，其余ignore
            if select and not self.dh.is_descendant_node(key2, select):
                self.logger.debug("Based on select config, ignore this key: " + str(key2))
                right_keys.append(key2)
                continue
            # 如果配置中定义了ignore，则被指定的节点及其子节点都需要ignore
            if ignore and self.dh.is_descendant_node(key2, ignore):
                self.logger.debug("Based on ignore config, ignore this key: " + str(key2))
                right_keys.append(key2)
                continue
            # 如果已经在rule中进行了验证，则该节点及其子节点无需再diff
            if self.dh.is_descendant_node(key2, match_keys + unmatch_keys):
                continue

            if key2 not in dict1:  # added
                self.logger.debug("New key: " + str(key2) + " with value: " + json.dumps(dict2[key2], ensure_ascii=False) + " was added")
                # self.logger.debug("New key: %s was added" % str(key2))
                diff_ret[key2] = ('add', key2, (dict2[key2],))
                add_keys.append(key2)
            # 文本diff
            elif dict1[key2] != dict2[key2]:  # changed
                self.logger.debug(
                    "The value of " + str(key2) + " was changed from " + json.dumps(dict1[key2], ensure_ascii=False)
                    + " to " + json.dumps(dict2[key2], ensure_ascii=False))
                diff_ret[key2] = ('change', key2, (dict1[key2], dict2[key2]))
                change_keys.append(key2)
            else:  # 无差异
                self.logger.debug("OK. The value of " + str(key2) + " was kept as " + json.dumps(dict1[key2], ensure_ascii=False))
                right_keys.append(key2)

        # 再补充遍历录制结果
        for key1 in dict1:
            # 开始进行diff
            if key1 not in dict2:  # removed
                # 如果配置中定义了select，则仅被指定的节点及其子节点需要diff，其余ignore
                if select and not self.dh.is_descendant_node(key1, select):
                    self.logger.debug("Based on select config, ignore this key: " + str(key1))
                    right_keys.append(key1)
                    continue
                # 如果配置中定义了ignore，则被指定的节点及其子节点都需要ignore
                if ignore and self.dh.is_descendant_node(key1, ignore):
                    self.logger.debug("Based on ignore config, ignore this key: " + str(key1))
                    right_keys.append(key1)
                    continue

                diff_ret[key1] = ('remove', key1, (dict1[key1],))
                self.logger.debug("This key: " + str(key1) + " with value: " + json.dumps(dict1[key1], ensure_ascii=False) + " was removed")
                # self.logger.debug("This key: %s was removed" % str(key1))
                remove_keys.append(key1)
            else:  # 已diff过
                pass

        # # for add and remove case, filter out descendant diff
        # tmp_ret = deepcopy(diff_ret)
        # for key0 in tmp_ret.keys():
        #     if self.dh.is_descendant_node(key0, add_keys + remove_keys) == 1:
        #         del diff_ret[key0]
        #     else:
        #         pass
        # # for change case, filter out ancestral diff
        # for key0 in change_keys:
        #     if self.dh.is_ancestral_node(key0, tmp_ret.keys()) == 1:
        #         del diff_ret[key0]
        #     else:
        #         pass
        # # for match case, filter out descendant diff unless it in unmatch list
        # for key0 in tmp_ret.keys():
        #     if self.dh.is_descendant_node(key0, match_keys) == 1 and (key0 not in unmatch_keys):
        #         del diff_ret[key0]
        #     else:
        #         pass

        return diff_ret.values()

    def dict_diff(self, dict1, dict2, ignore=None, select=None, rule=None):
        result = {}
        result['diff'] = self.__my_dict_diff(first=dict1, second=dict2, ignore=ignore, select=select, rule=rule)
        self.logger.debug("Dict diff result: " + json.dumps(result['diff'], ensure_ascii=False))

        result['msg'] = []
        for i in range(0, len(result['diff'])):
            item = result['diff'][i]
            if item[0] == 'change':  # ('change', u'iswork', (True, False))
                result['msg'].append(
                    " * The value of \"%s\" was changed from \"%s\" to \"%s\"" % (item[1], item[2][0], item[2][1]))
            elif item[0] == 'add':
                result['msg'].append(" * The key \"%s: %s\" was added" % (item[1], item[2][0]))
            elif item[0] == 'remove':
                result['msg'].append(
                    " * The key \"%s: %s\" was removed" % (item[1], item[2][0]))
            elif item[0] == 'unmatch':
                result['msg'].append(" * \"%s\":  \"%s\" does not match the rule: \"%s\"" % (item[1], item[2][1], item[2][0]))

        result['ret'] = False if result['msg'] else True
        return result

    def list_diff(self, list1, list2, ignore=None, select=None, rule=None):
        if not (isinstance(list1, list) and isinstance(list2, list)):
            return {'ret': False, 'msg': '', 'diff': ''}

        # convert list to dict, value is count
        dict1 = {}
        dict2 = {}
        for x in list1:
            dict1[x] = dict1[x] + 1 if x in dict1 else 1
        for x in list2:
            dict2[x] = dict2[x] + 1 if x in dict2 else 1
        # use dictdiff format
        result = {}
        result['diff'] = self.__my_dict_diff(first=dict1, second=dict2, ignore=ignore, select=select, rule=rule)
        result['msg'] = []
        for i in range(0, len(result['diff'])):
            item = result['diff'][i]
            if item[0] == 'change':
                result['msg'].append(
                    " * The count of \"%s\" was changed \"%s => %s\"" % (item[1], item[2][0], item[2][1]))
            elif item[0] == 'add':
                result['msg'].append(" * The key \"%s\" * %s was added" % (item[1], item[2][0]))
            elif item[0] == 'remove':
                result['msg'].append(" * The key \"%s\" * %s was removed" % (item[1], item[2][0]))

        result['ret'] = False if result['msg'] else True
        return result

    @staticmethod
    def str_diff(str1, str2):
        try:
            str1 = str(str1).strip()
            str2 = str(str2).strip()
        except Exception:
            return {'ret': False, 'msg': '', 'diff': ''}
        if str1 == str2:
            return {'ret': True, 'msg': '', 'diff': ''}
        else:  # use dictdiff format
            return {
                'ret': False,
                'msg': " * The value was changed from \"%s\" to \"%s\"" % (str1, str2),
                'diff': ('change', str1, (str1, str2))
            }

    @staticmethod
    def get_false(f_msg=''):
        return {
            'ret': False,
            'msg': str(f_msg),
            'diff': ''
        }


if __name__ == "__main__":
    d1 = """
            {"error": "", "status": 200, "time": 0, "srvtime1": "2018-10-18 11:54:32", "islogin": 0, "iswork": true,
         "tag": null, "data": {"isSuccess": true, "isHotLine": false, "msg": ""}}
         """
    d2 = """
            {"error": "", "status": 200, "usedtime": 1e3, "srvtime": "2019-1-17 10:20:32", "islogin": 0, "iswork": true,
         "tag": null, "data": {"isSuccess": false, "isHotLine": false, "msg": ""}}
         """

    l1 = ["a", "b", "cd", "c", "c"]
    l2 = ["a", "c", "ce", "a"]

    df = MyDiffer()
    print json.dumps(df.str_diff('abc', 'abd'), ensure_ascii=False)
    print json.dumps(
        df.dict_diff(json.loads(d1), json.loads(d2), ignore=['time'], rule={'srvtime': '==\'111\''}), ensure_ascii=False)
    print json.dumps(df.list_diff(l1, l2, ignore=['a']), ensure_ascii=False)


