# -*- coding: utf-8 -*-
# --------------------------------------
#   When        Who         What
# --------------------------------------
# Jan 10,2019   idle-man    Create, fiddler txt to .gor
# Jan 15,2019   idle-man    Add -h|--host argument
# Jan 18,2019   idle-man    Add -t|--type argument, support fiddler and charles
# Mar 14,2019   idle-man    Remove -h&-t argument, update usage, add log
# Apr 15,2019   idle-man    Add -y|--yaml for project config
#
import getopt
from getopt import GetoptError
import json
import os
import sys
import re
import yaml

from module.common.configer import MyConfigHelper
from module.record.parser import MyParser
from module.common.logger import Logger
from config.config import *


def usage():
    print """
用法说明: python %s
            -i|--input  <源文件名称，可附带相对或绝对路径，目前仅支持Fiddler txt和Charles trace格式>  [\033[33m必要参数\033[0m]
            -o|--output <录制文件名称, 可附带相对或绝对路径，ini格式>  [\033[33m可选参数, 默认值: data/record.ini\033[0m]
            -y|--yaml   <项目配置文件，可参考config/template.yaml进行定义>  [\033[33m必要参数\033[0m]

用法示例：python %s -i data/demo.trace -o data/demo-record.ini -y config/demo.yaml
        """ % (sys.argv[0], sys.argv[0])
    exit()

if __name__ == '__main__':
    project_path = re.findall(r"(.+Parrot)", os.path.abspath(__file__))[0]

    # 接收并处理传参
    i_file = ''
    o_file = ''
    h_filter = ''
    p_conf = ''
    y_file = ''
    debug = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdi:o:c:y:", ["help", "debug", "input=", "output=", "config=", "yaml="])
        for opt, value in opts:
            if opt in ('-h', '--help'):
                usage()
            elif opt in ('-d', '--debug'):
                debug = 1
            elif opt in ('-i', '--input'):
                i_file = value.strip()
            elif opt in ('-o', '--output'):
                o_file = value.strip()
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
    f_ext = re.findall(r".+\.(\w+$)", i_file)[0].lower()
    if f_ext == 'trace':
        r_type = 'charles'
    else:
        r_type = 'fiddler'
    if not o_file:
        o_file = project_path + '/data/record.ini'

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
    config = MyConfigHelper(project=p_conf, section='record', logger=logger)
    # 开始进行解析
    parser = MyParser(conf=config, logger=logger)
    if r_type == 'fiddler':
        my_dict = parser.fiddler_to_ini(source=i_file, target=o_file)
    else:
        my_dict = parser.charles_to_ini(source=i_file, target=o_file)
    # print json.dumps(my_dict, ensure_ascii=False)
