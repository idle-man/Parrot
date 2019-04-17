# -*- coding: utf-8 -*-
# --------------------------------------
#   When        Who         What
# --------------------------------------
# Jan 22,2019   idle-man    Create, verify by comparing record.ini and replay.ini
# Mar 14,2019   idle-man    Add log and update usage
# Apr 10,2019   idle-man    Support html report
# Apr 15,2019   idle-man    Add -y|--yaml for project config
#
import getopt
from getopt import GetoptError
import json
import os
import re
import sys
import yaml
from copy import deepcopy

from module.common.configer import MyIniHelper
from module.common.configer import MyConfigHelper
from module.check.differ import MyDiffer
from module.common.logger import Logger
from config.config import *
from module.common.reportor import ParrotReport


def usage():
    print """
用法说明: python %s
            -s|--source <录制的文件名称，可附带相对或绝对路径，ini格式>  [\033[33m必要参数\033[0m]
            -t|--target <回放的文件名称, 可附带相对或绝对路径，ini格式>  [\033[33m必要参数\033[0m]
            -o|--output <输出的文件名称，可附带相对或绝对路径，html格式>  [\033[33m可选参数，默认值：data/report.html\033[0m]
            -y|--yaml   <项目配置文件，可参考config/template.yaml进行定义>  [\033[33m必要参数\033[0m]

用法示例：python %s -s data/demo-record.ini -t data/demo-replay.ini -o data/demo-report.html -y config/demo.yaml
        """ % (sys.argv[0], sys.argv[0])
    exit()


def diff_ini(file1, file2):
    # 读取ini文件，转为字典格式
    ini_dict1 = MyIniHelper.ini2dict(filename=file1)
    ini_dict2 = MyIniHelper.ini2dict(filename=file2)
    logger.debug("Dict1: " + json.dumps(ini_dict1, ensure_ascii=False))
    logger.debug("Dict2: " + json.dumps(ini_dict2, ensure_ascii=False))

    if not ('IDS' in ini_dict1.keys() and len(ini_dict1['IDS']) > 0
            and 'IDS' in ini_dict2.keys() and len(ini_dict2['IDS']) > 0):
        logger.error("Invalid input file, pls make sure it's your recorded/replayed ini file")
        return False

    # 获取项目的check配置
    select_list = config.check_select_list
    ignore_list = config.check_ignore_list
    rule_list = config.check_rule_list
    # logger.debug("Select config: " + json.dumps(select_list))
    # logger.debug("Ignore config: " + json.dumps(ignore_list))
    # logger.debug("Rule config: " + json.dumps(rule_list))

    total_ret = {
        'TOTAL': {
            'Sum': 0,
            'Pass': 0,
            'Fail': 0
        },
        'DETAIL': {
            'IDS': []
        }
    }

    # 以回放的文件作为diff基准（因为根据项目配置，部分录制的流量可能不会被回放）
    for t_id in ini_dict2['IDS']:
        t_dict = ini_dict2[t_id]
        s_dict = {}
        status_ret = {}
        resp_ret = {}
        logger.info("Check this request: " + t_id)
        s_id = re.findall(r"(.+) \w+$", t_id)[0]  # target id contains source id
        if s_id in ini_dict1.keys():
            s_dict = ini_dict1[s_id]
        else:
            logger.warn(" ** Source data is not found, ignore..")
            continue

        # 部分select/ignore/rule配置可能是单独针对个别api的，先做一遍筛选
        i_select = []
        i_ignore = []
        i_rule = {}
        for sel in select_list:
            if re.match(r".+::", sel):  # 指定了特定的api
                key_prefix = sel.split('::')[0]
                key_content = sel.split('::')[1]
                # 判定是否采用case id前缀
                if re.match(r"^__CASE_", str(key_prefix)):
                    if key_prefix == t_dict['id']:
                        i_select.append(key_content)
                elif re.match(r"[\/]?" + key_prefix + "[\/|\?]?.*", t_dict['url']):
                    i_select.append(key_content)
                else:
                    pass
            else:  # 默认针对所有api
                i_select.append(sel)
        for ig in ignore_list:
            if re.match(r".+::", ig):  # 指定了特定的api
                key_prefix = ig.split('::')[0]
                key_content = ig.split('::')[1]
                # 判定是否采用case id前缀
                if re.match(r"^__CASE_", str(key_prefix)):
                    if key_prefix == t_dict['id']:
                        i_ignore.append(key_content)
                elif re.match(r"[\/]?" + key_prefix + "[\/|\?]?.*", t_dict['url']):
                    i_ignore.append(key_content)
                else:
                    pass
            else:  # 默认针对所有api
                i_ignore.append(ig)
        for ru in rule_list.keys():
            if re.match(r".+::", ru):  # 指定了特定的api
                key_prefix = ru.split('::')[0]
                key_content = ru.split('::')[1]
                # 判定是否采用case id前缀
                if re.match(r"^__CASE_", str(key_prefix)):
                    if key_prefix == t_dict['id']:
                        i_rule[(key_content)] = rule_list[ru]
                if re.match(r"[\/]?" + key_prefix + "[\/|\?]?.*", t_dict['url']):
                    i_rule[(key_content)] = rule_list[ru]
                else:
                    pass
            else:  # 默认针对所有api
                i_rule[ru] = rule_list[ru]
        logger.info("Select config: " + json.dumps(i_select, ensure_ascii=False))
        logger.info("Ignore config: " + json.dumps(i_ignore, ensure_ascii=False))
        logger.info("Rule config: " + json.dumps(i_rule, ensure_ascii=False))

        if 'status' in t_dict.keys() and 'status' in s_dict.keys():
            status_ret = differ.str_diff(s_dict['status'], t_dict['status'])
        else:
            status_ret = differ.get_false("status not found")
            if 'status' not in s_dict.keys():
                s_dict['status'] = 'Unknown'
            if 'status' not in t_dict.keys():
                t_dict['status'] = 'Unknown'

        logger.info(" ** Diff http status: " + json.dumps(status_ret['ret'], ensure_ascii=False))

        resp_flag = 0
        if 'response' in t_dict.keys() and 'response' in s_dict.keys():
            try:
                res_dict1 = json.loads(s_dict['response'])
                try:
                    res_dict2 = json.loads(t_dict['response'])
                    # json to dict succeed, use dict diff
                    resp_flag = 1
                except ValueError:
                    # json to dict failed, use str diff
                    logger.debug("Response to dict failed, will do text diff")
            except ValueError:
                logger.debug("Response to dict failed, will do text diff")
            if resp_flag:
                resp_ret = differ.dict_diff(
                    dict1=res_dict1, dict2=res_dict2,
                    ignore=i_ignore, select=i_select, rule=i_rule)
            else:
                resp_ret = differ.str_diff(str1=s_dict['response'], str2=t_dict['response'])
        else:
            resp_ret = differ.get_false("response not found")
            if 'response' not in t_dict.keys():
                t_dict['response'] = 'Unknown'
            if 'response' not in s_dict.keys():
                s_dict['response'] = 'Unknown'
        logger.info(" ** Diff http response: " + json.dumps(resp_ret['ret'], ensure_ascii=False))
        if len(status_ret.keys()) == 0 or len(resp_ret.keys()) == 0:
            logger.error("Invalid input file, pls make sure it's your recorded/replayed ini file")
            return False
        total_ret['TOTAL']['Sum'] += 1
        total_ret[s_id] = {}
        total_ret[s_id]['RESULT'] = {}
        total_ret[s_id]['RESULT']['status'] = status_ret
        total_ret[s_id]['RESULT']['response'] = resp_ret
        total_ret['DETAIL'][s_id] = []  # 使用列表格式，以便保证输出顺序
        total_ret['DETAIL']['IDS'].append(s_id)

        if status_ret['ret'] and resp_ret['ret']:
            total_ret[s_id]['RESULT']['result'] = True
            total_ret['TOTAL']['Pass'] += 1
            total_ret['DETAIL'][s_id].append({'result': 'pass'})
        else:
            total_ret[s_id]['RESULT']['result'] = False
            total_ret['DETAIL'][s_id].append({'result': 'fail'})
            total_ret['TOTAL']['Fail'] += 1
        total_ret[s_id]['SOURCE'] = s_dict
        total_ret[s_id]['TARGET'] = t_dict
        total_ret['DETAIL'][s_id].append({'id': t_dict['id']})
        total_ret['DETAIL'][s_id].append({'protocol': t_dict['protocol']})
        total_ret['DETAIL'][s_id].append({'method': t_dict['method']})
        total_ret['DETAIL'][s_id].append({'host': t_dict['host']})
        total_ret['DETAIL'][s_id].append({'url': t_dict['url']})
        total_ret['DETAIL'][s_id].append({'parameter': t_dict['parameter']})
        total_ret['DETAIL'][s_id].append({'header': t_dict['header']})
        total_ret['DETAIL'][s_id].append({'start-time': t_dict['start-time']})
        total_ret['DETAIL'][s_id].append({'end-time': t_dict['end-time']})
        total_ret['DETAIL'][s_id].append({"expect.status": s_dict['status']})
        total_ret['DETAIL'][s_id].append({"actual.status": t_dict['status']})
        total_ret['DETAIL'][s_id].append({"old.duration_ms": s_dict['duration_ms']})
        total_ret['DETAIL'][s_id].append({"new.duration_ms": t_dict['duration_ms']})
        total_ret['DETAIL'][s_id].append({"expect.response": s_dict['response']})
        total_ret['DETAIL'][s_id].append({"actual.response": t_dict['response']})
        total_ret['DETAIL'][s_id].append({"response.diff": json.dumps(resp_ret['msg'])})
        total_ret['DETAIL'][s_id].append({"select.list": json.dumps(i_select)})
        total_ret['DETAIL'][s_id].append({"ignore.list": json.dumps(i_ignore)})
        total_ret['DETAIL'][s_id].append({"rule.list": json.dumps(i_rule)})

    return total_ret


def html_report(the_dict, out_file):
    fp = open(out_file, 'wb')
    runner = ParrotReport(stream=fp, title='Parrot流量回放测试报告', description='')
    result_dict = {'total_count': 0, 'succ_count': 0, 'fail_count': 0, 'result': []}

    s_time = e_time = 0
    for my_id in the_dict['IDS']:
        case_dict = the_dict[my_id]
        case_id = case_dict['id']
        case_protocol = case_dict['protocol']
        case_method = case_dict['method']
        case_host = case_dict['host']
        case_url = case_dict['url']
        case_parameter = case_dict['parameter']
        case_header = case_dict['header']
        case_name = "%s: %s" % (case_id, case_url)

        if s_time == 0: s_time = case_dict['start-time']
        e_time = case_dict['end-time']

        old_status = case_dict['expect.status']
        old_duration = case_dict['old.duration_ms']
        old_response = case_dict['expect.response']
        new_status = case_dict['actual.status']
        new_duration = case_dict['new.duration_ms']
        new_response = case_dict['actual.response']
        resp_diff = case_dict['response.diff']
        conf_select = case_dict['select.list']
        conf_ignore = case_dict['ignore.list']
        conf_rule = case_dict['rule.list']

        status_ret = 'pass' if str(old_status) == str(new_status) else 'fail'
        status_content = "Recorded status: %s\nReplayed status: %s" % (str(old_status), str(new_status))
        dura_ret = 'pass'
        dura_content = "Recorded duration(ms): %s\nReplayed duration(ms): %s" % (str(old_duration), str(new_duration))
        resp_ret = 'pass' if resp_diff == '[]' else 'fail'
        resp_content = "Recorded response: %s\nReplayed response: %s" % (old_response, new_response)
        resp_content += "\nDiff: %s\nselect conf: %s\nignore conf:%s\nrule conf:%s" % (
        resp_diff, conf_select, conf_ignore, conf_rule)
        detail_content = "id: %s\nprotocol: %s\nmethod: %s\nhost: %s\nurl: %s\nparameter: %s\nheader:%s" % (
        case_id, case_protocol, case_method, case_host, case_url, case_parameter, case_header)

        test_result = 'pass' if status_ret == 'pass' and dura_ret == 'pass' and resp_ret == 'pass' else 'fail'
        result_dict['total_count'] += 1
        if test_result == 'pass':
            result_dict['succ_count'] += 1
        else:
            result_dict['fail_count'] += 1
        result_dict['result'].append({'name': case_name,
                                      'id': "pt%s" % case_id.lower() if test_result == 'pass' else "ft%s" % case_id.lower(),
                                      'result': test_result,
                                      'status_ret': status_ret,
                                      'status_content': status_content,
                                      'dura_ret': dura_ret,
                                      'dura_content': dura_content,
                                      'resp_ret': resp_ret,
                                      'resp_content': resp_content,
                                      'detail_content': detail_content
                                      })

    # print json.dumps(result_dict)
    runner.run(result=result_dict, start_time=s_time, end_time=e_time)
    fp.close()


if __name__ == '__main__':
    project_path = re.findall(r"(.+Parrot)", os.path.abspath(__file__))[0]

    s_file = ''
    t_file = ''
    report = ''
    p_conf = ''
    y_file = ''
    debug = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:], "ds:t:o:c:y:", ["debug", "source=", "target=", "output=", "config=", "yaml="])
        for opt, value in opts:
            if opt in ('-s', '--source'):
                s_file = value.strip()
            elif opt in ('-t', '--target'):
                t_file = value.strip()
            elif opt in ('-o', '--output'):
                report = value.strip()
            elif opt in ('-c', '--config'):
                p_conf = value.strip()
            elif opt in ('-y', '--yaml'):
                y_file = value.strip()
            elif opt in ('-d', '--debug'):
                debug = 1
            else:
                usage()
    except GetoptError:
        usage()

    if not (s_file and os.path.exists(s_file) and t_file and os.path.exists(t_file)):
        usage()
    if not report:
        report = project_path + '/data/report.html'
    else:
        if re.match(r".+\.\w+$", report):
            report = str(re.findall(r"(.+)\.\w+$", report)[0]) + '.html'
        else:
            report = str(report) + '.html'

    # yaml conf
    if not y_file:
        usage()
    if not os.path.exists(y_file):
        print "Error: 指定给-y|--yaml的参数: %s 无效，请确认文件存在且路径正确." % y_file
        usage()

    # if not p_conf:  # 若未定义，使用默认值
    #     p_conf = 'default_conf'
    #
    # try:
    #     p_conf = eval(p_conf)
    # except NameError:
    #     if not re.match(r"\S+_conf", p_conf):
    #         p_conf = str(p_conf) + '_conf'
    #         try:
    #             p_conf = eval(p_conf)
    #         except NameError:
    #             print "Error: 指定给-c|--config的参数: %s 无效，请确认已在config/config.py中定义." % p_conf
    #             usage()
    #     else:
    #         print "Error: 指定给-c|--config的参数: %s 无效，请确认已在config/config.py中定义." % p_conf
    #         usage()

    p_conf = yaml.load(open(y_file), Loader=yaml.FullLoader)

    # 初始化logger
    if debug:
        logger = Logger(level='debug')
    else:
        logger = Logger(level='info')
    # 读取项目配置
    config = MyConfigHelper(project=p_conf, section='check', logger=logger)

    differ = MyDiffer(logger=logger)

    logger.info("Start to diff %s and %s" % (s_file, t_file))
    result = diff_ini(s_file, t_file)

    i_report = str(re.findall(r"(.+)\.\w+$", report)[0]) + '.ini'
    logger.info("Check finished, write ini report: %s" % i_report)
    MyIniHelper.dict2ini(content=result['DETAIL'], filename=i_report)

    logger.info("Generate html report: %s" % report)
    html_report(the_dict=MyIniHelper.ini2dict(filename=i_report), out_file=report)
    logger.info("Done.")
    logger.info("Summary result: " + json.dumps(result['TOTAL'], ensure_ascii=False))


