# -*- coding: utf-8 -*-
# --------------------------------------
#   When        Who         What
# --------------------------------------
# Jan 16,2019   idle-man    Create, replay using goreplay
# Jan 21,2019   idle-man    Replay using requests module, as the recorded time interval
# Jan 24,2019   idle-man    Support select and ignore settings in config
# Mar 14,2019   idle-man    Add log and update usage
# Apr 15,2019   idle-man    Add -y|--yaml for project config
#
import getopt
from getopt import GetoptError
import json
import os
import re
import sys
from time import sleep
import platform
import yaml
import threading
from multiprocessing import Pool

from module.common.configer import MyConfigHelper
from module.common.configer import MyIniHelper
from module.common.helper import MyFileHelper
from module.common.helper import MyTimeHelper
from module.common.logger import Logger
from module.replay.request import MyHttpHelper
from config.config import *


def usage():
    print """
用法说明: python %s
            -i|--input  <录制文件名称，可附带相对或绝对路径，ini格式>  [\033[33m必要参数\033[0m]
            -o|--output <输出文件名称, 可附带相对或绝对路径，ini格式>  [\033[33m可选参数, 默认值: data/replay.ini\033[0m]
            -y|--yaml   <项目配置文件，可参考config/template.yaml进行定义>  [\033[33m必要参数\033[0m]

用法示例：python %s -i data/demo-record.ini -o data/demo-replay.ini -y config/demo.yaml
        """ % (sys.argv[0], sys.argv[0])
    exit()


# 回放单个http请求
def run_http_req(r_id, r_dict):
    logger.info("Run against your select/ignore/store/replace config")
    # 根据配置，判定是选中，还是忽略
    if not config.if_selected(the_dict=r_dict):
        logger.info("Not selected by the config, ignore: " + r_dict['url'])
        return True
    # 回放前，做过程变量存储
    config.store_element(the_dict=r_dict, mode=['param', 'header', 'resp'], when='before')
    logger.debug("The global_var_dict: " + json.dumps(config.global_var_dict, ensure_ascii=False))
    # 回放前，根据配置进行文本替换
    logger.debug("The dict before replace: " + json.dumps(r_dict, ensure_ascii=False))
    p_dict = config.replace_element(the_dict=r_dict)
    logger.debug("The dict after replace: " + json.dumps(p_dict, ensure_ascii=False))

    the_http = p_dict['protocol'].lower()
    the_method = p_dict['method'].lower()
    the_host = p_dict['host']
    the_uri = p_dict['url']
    the_param = p_dict['parameter']
    the_header = json.loads(p_dict['header']) if isinstance(p_dict['header'], str) else p_dict['header']
    # old_status = r_dict['status']
    # old_resp = r_dict['response']

    if not re.match(r"http.+", the_host.lower()):
        the_url = "%s://%s%s" % (the_http, the_host, the_uri)
    else:
        the_url = "%s%s" % (the_host, the_uri)
        the_http = re.findall(r"(http[s]*)", the_host)[0]
        the_host = re.findall(r".+//(.+)", the_host)[0]

    logger.info("Replay this request: %s" % the_url)
    resp = MyHttpHelper().request(
        url=the_url,
        method=the_method,
        param=the_param,
        header=the_header,
        timeout=config.replay_timeout)

    # 将单次执行结果记录临时文件，以便后续汇总结果
    tmp_file = project_path + '/tmp/' + r_id.replace(' ', '_') + '.ini'
    s_dict = {}
    new_id = r_id + " %d" % MyTimeHelper.now_unix_timestamp_ms()
    s_dict[new_id] = {}
    s_dict[new_id]['id'] = r_dict['id']
    s_dict[new_id]['protocol'] = the_http
    s_dict[new_id]['method'] = the_method
    s_dict[new_id]['host'] = the_host
    s_dict[new_id]['url'] = the_uri
    s_dict[new_id]['parameter'] = the_param
    s_dict[new_id]['header'] = the_header  # resp['header']
    s_dict[new_id]['status'] = resp['status']
    s_dict[new_id]['start-time'] = resp['start-time']
    s_dict[new_id]['end-time'] = resp['end-time']
    s_dict[new_id]['duration_ms'] = resp['duration']
    s_dict[new_id]['response'] = resp['msg']

    # 回放后，判断是否需要额外wait，或验证response
    if not config.need_wait(the_dict=s_dict[new_id]):
        logger.debug("The response: " + json.dumps(s_dict[new_id]['response'], ensure_ascii=False))
        return False
    else:
        # 回放后，进行过程变量存储，以便后续接口replace使用
        config.store_element(the_dict=s_dict[new_id], mode=['resp',])
        logger.debug("The global_var_dict: " + json.dumps(config.global_var_dict, ensure_ascii=False))

        MyIniHelper.dict2ini(content=s_dict, filename=tmp_file)
        return True


# 回放主函数
def run_ini(in_file, out_file):
    logger.info("Start to replay your ini requests in %s" % in_file)
    req_dict = MyIniHelper.ini2dict(filename=in_file)
    logger.debug("The dict: " + json.dumps(req_dict, ensure_ascii=False))

    if not req_dict or 'IDS' not in req_dict.keys() or not req_dict['IDS']:
        logger.error("Invalid input file, pls make sure it's your recorded ini file")
        exit()

    run_type = int(config.replay_type)  # 1-串行, 2-多进程, 3-多线程
    if run_type == 2:
        pool = Pool(processes=5)  # 创建进程池，定义最大并发进程数

    # 获取当前时间戳，初始化时间间隔
    begin_time_now = MyTimeHelper.now_unix_timestamp_ms()
    global_interval = 0
    default_interval = 0.100  # 默认的时间间隔，减少可能的并发问题
    for req_id in req_dict['IDS']:  # 逐个回放
        i_retry = config.replay_max_retry  # 单次执行的最大重试次数，结合wait config使用
        # 获取录制流量的时间戳，计算时间间隔
        my_time_now = MyTimeHelper.now_unix_timestamp_ms()
        my_time_old = int(req_id.split(" ")[2][:13])
        req_interval = (my_time_now - my_time_old) / 1000.0 if my_time_now > my_time_old else default_interval
        if global_interval == 0:  # 计算历史时间间隔
            global_interval = (begin_time_now - my_time_old) / 1000.0 if begin_time_now > my_time_old else default_interval

        # 根据历史时间间隔，判断是否到了执行时间
        # 如果此前执行过程中有了额外的wait，需要纳入后续的时间间隔中
        if global_interval + config.replay_wait > req_interval:
            logger.info("Need to wait %.3f seconds" % (global_interval + config.replay_wait - req_interval))
            sleep(global_interval + config.replay_wait - req_interval)
        else:  # 默认做极短的sleep
            sleep(default_interval)
            config.replay_wait += default_interval

        if run_type == 2:  # 多进程方式
            pool.apply_async(func=run_http_req, args=(req_id, req_dict[req_id]))
        elif run_type == 3:  # 多线程方式
            t = threading.Thread(target=run_http_req, args=(req_id, req_dict[req_id]))
            t.setDaemon(True)
            t.start()
            t.join()
        else:  # 串行方式
            # i_flag = run_http_req(req_id, req_dict[req_id])
            i_flag = False
            while not i_flag:
                i_flag = run_http_req(req_id, req_dict[req_id])
                if i_flag:
                    break
                i_retry -= 1
                if i_retry <= 0:
                    break
                logger.info("Need to Re-run this request..")
                sleep(1)
                config.replay_wait += 1

    if run_type == 2:  # 关闭进程池
        sleep(3)
        pool.close()
        pool.join()

    logger.info("Replay finished, sum the result")
    # 汇总执行结果
    total_dict = {'IDS': []}
    for req_id in req_dict['IDS']:
        t_file = project_path + '/tmp/' + req_id.replace(' ', '_') + '.ini'
        t_dict = MyIniHelper.ini2dict(filename=t_file)
        for t_id in t_dict.keys():
            if t_id == 'IDS':
                total_dict['IDS'] += t_dict['IDS']
            else:
                # 使用list格式，以保证输出的顺序
                total_dict[t_id] = []
                total_dict[t_id].append({'id': t_dict[t_id]['id']})
                total_dict[t_id].append({'protocol': t_dict[t_id]['protocol']})
                total_dict[t_id].append({'method': t_dict[t_id]['method']})
                total_dict[t_id].append({'host': t_dict[t_id]['host']})
                total_dict[t_id].append({'url': t_dict[t_id]['url']})
                total_dict[t_id].append({'parameter': t_dict[t_id]['parameter']})
                total_dict[t_id].append({'header': t_dict[t_id]['header']})
                total_dict[t_id].append({'status': t_dict[t_id]['status']})
                total_dict[t_id].append({'start-time': t_dict[t_id]['start-time']})
                total_dict[t_id].append({'end-time': t_dict[t_id]['end-time']})
                total_dict[t_id].append({'duration_ms': t_dict[t_id]['duration_ms']})
                total_dict[t_id].append({'response': t_dict[t_id]['response']})
        # 清除临时文件
        if not debug:
            MyFileHelper.remove_file(filename=t_file)
    logger.debug("The result: " + json.dumps(total_dict, ensure_ascii=False))

    logger.info("Write replay info into ini file: " + out_file)
    MyIniHelper.dict2ini(content=total_dict, filename=out_file, summary='IDS')
    logger.info("Done.")

    return total_dict


if __name__ == '__main__':
    project_path = re.findall(r"(.+Parrot)", os.path.abspath(__file__))[0]

    # 接收并处理传参
    i_file = ''
    o_file = ''
    r_rate = 1
    p_conf = ''
    y_file = ''
    debug = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdi:o:r:c:y:", ["help", "debug", "input=", "output=", "rate=", "config=", "yaml="])
        for opt, value in opts:
            if opt in ('-h', '--help'):
                usage()
            elif opt in ('-d', '--debug'):
                debug = 1
            elif opt in ('-i', '--input'):
                i_file = value.strip()
            elif opt in ('-o', '--output'):
                o_file = value.strip()
            elif opt in ('-r', '--rate'):
                r_rate = value.strip()
            elif opt in ('-c', '--config'):
                p_conf = value.strip()
            elif opt in ('-y', '--yaml'):
                y_file = value.strip()
            else:
                usage()
    except GetoptError:
        usage()

    # input file
    if not i_file:
        usage()
    if not os.path.exists(i_file):
        print "Error: 指定给-i|--input的参数: %s 无效，请确认文件存在且路径正确." % i_file
        usage()

    # yaml conf
    if not y_file:
        usage()
    if not os.path.exists(y_file):
        print "Error: 指定给-y|--yaml的参数: %s 无效，请确认文件存在且路径正确." % y_file
        usage()

    # output file
    if not o_file:
        o_file = project_path + '/data/replay.ini'
    try:
        r_rate = int(r_rate)
    except ValueError:
        r_rate = 1

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
    config = MyConfigHelper(section='replay', project=p_conf, logger=logger)
    # 开始进行回放
    run_ini(in_file=i_file, out_file=o_file)
