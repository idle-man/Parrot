# -*- coding: utf-8 -*-
# --------------------------------------------------------------
#   When        Who         What
# --------------------------------------------------------------
# Jan 24,2019   idle-man    Add project_conf and support select and ignore settings in project_conf
# Jan 30,2019   idle-man    Support store settings in project_conf
# Feb 12,2019   idle-man    Add global_conf
#

import json

"""
特别声明：
    * 请不要随意修改下方的结构和所有变量名、数据类型
    * 使用中可复制default_conf完整字典，粘贴到下方段落并重新命名（包含_conf后缀，例如：test_conf）
    * 之后，test_conf中的值需要结合自己项目的实际情况进行修改
"""

# 全局通用配置，和项目完全无关
global_conf = {
    'record': {  # Step 1 - 录制阶段配置
        'header': [  # 录制时需要留存的header列表，如有自定义header，可添加到其中
            'Accept', 'Accept-Encoding', 'Accept-Language',
            'User-Agent', 'Content-Type', 'X-Requested-With', 'Connection',
        ]
    },
    'replay': {  # Step 2 - 回放阶段配置
        'timeout': 5,  # 回放请求的超时时间，单位：秒，默认：5
        'type': 1,  # 执行方式，1-串行，2-异步并行，默认：1
        'max_retry': 10000,  # 某个请求的最大尝试次数
    },
    'check': {  # Step 3 - 验证阶段配置，还没想好放些什么

    }
}

# 项目级配置模板，请不要修改；可基于此复制自己的项目配置(例如test_conf)，在自己的配置上进行修改
default_conf = {
    'record': {  # Step 1 - 录制阶段配置
        'select': {  # 若填写非空，则录制时仅选取匹配列表的流量，其余会被忽略
            'host': [  # 列表格式，会同源数据中的host进行完全匹配，如example.com、10.10.10.10:8080
                # 你的值可以写在这里，或者保持为空
            ],
            'url': [  # 列表格式，会同源数据中的url进行部分匹配，如：/api会匹配到/apiA A/apiB等
                # 你的值可以写在这里，或者保持为空
            ],
        },
        'ignore': {  # 若填写非空，则录制时匹配列表的流量会被忽略，优先级低于select
            'host': [  # 列表格式，会同源数据中的host进行完全匹配，如example.com、10.10.10.10:8080
                # 你的值可以写在这里，或者保持为空
            ],
            'url': [  # 列表格式，会同源数据中的url进行部分匹配，如：/api会匹配到/apiA A/apiB等
                # 你的值可以写在这里，或者保持为空
            ],
        },
        'replace': {  # 若填写非空，则录制时会按照匹配的规则进行文本替换，统一格式：oldValue => newValue
            'host': [  # 列表格式，会同源数据中的host进行完全匹配，例如：example.com => t.example.com
                # 你的值可以写在这里，或者保持为空
            ],
            'url': [  # 列表格式，会同源数据中的url进行部分匹配，例如：/api => /apiA
                # 你的值可以写在这里，或者保持为空
            ],
            'param': [  # 列表格式，会同录制数据中的传参进行完全匹配，支持全局变量模式，# 例如：apiA::0301 => 0305, apiA::{date} => 0305, apiA::{date} => apiB::{data.items[0].number}，函数调用请用{{}}包围，目前支持的函数请见module/tool.py
                # 你的值可以写在这里，或者保持为空
            ],
            'header': [  # 列表格式，会同录制数据中的header进行完全匹配，支持全局变量模式，# 例如：abc => abd, apiA::{token} => abc，函数调用请用{{}}包围，目前支持的函数请见module/tool.py

            ],
        },
    },
    'replay': {  # Step 2 - 回放阶段配置
        'select': {  # 若填写非空，则回放时仅选取匹配列表的流量，其余会被忽略
            'host': [  # 列表格式，会同录制数据中的host进行完全匹配，如example.com、10.10.10.10:8080
                # 你的值可以写在这里，或者保持为空
            ],
            'url': [  # 列表格式，会同录制数据中的url进行部分匹配，如：/api会匹配到/apiA A/apiB等
                # 你的值可以写在这里，或者保持为空
            ],
        },
        'ignore': {  # 若填写非空，则回放时匹配列表的流量会被忽略，优先级低于select
            'host': [  # 列表格式，会同录制数据中的host进行完全匹配，如example.com、10.10.10.10:8080
                # 你的值可以写在这里，或者保持为空
            ],
            'url': [  # 列表格式，会同录制数据中的url进行部分匹配，如：/api会匹配到/apiA A/apiB等
                # 你的值可以写在这里，或者保持为空
            ],
        },
        'store': [  # 列表格式，若填写非空，则回放前/后会对列表中的字段的值进行提取后存储于运行态的全局变量中，供replace使用
            # 你的值可以写在这里，或者保持为空，格式：api::[where]::key，where可选值：param、resp、header，默认为resp
            # 例如：apiA::param::date, apiB::resp::data.items[0].date, apiC::header::token
        ],
        'replace': {  # 若填写非空，则回放时会按照匹配的规则进行文本替换，统一格式：oldValue => newValue
            'host': [  # 列表格式，会同回放数据中的host进行完全匹配，例如：example.com => t.example.com
                # 你的值可以写在这里，或者保持为空
            ],
            'url': [  # 列表格式，会同回放数据中的url进行部分匹配，例如：/api => /apiA
                # 你的值可以写在这里，或者保持为空
            ],
            'param': [  # 列表格式，会同回放数据中的传参进行完全匹配，支持全局变量模式，# 例如：apiA::0301 => 0305, apiA::{date} => 0305, apiA::{date} => apiB::{data.items[0].number}，函数调用请用{{}}包围，目前支持的函数请见module/tool.py
                # 你的值可以写在这里，或者保持为空
            ],
            'header': [  # 列表格式，会同回放数据中的header进行完全匹配，支持全局变量模式，# 例如：abc => abd, apiA::{token} => abc, apiB::{token} => {apiA::resp::token}，函数调用请用{{}}包围，目前支持的函数请见module/tool.py
                # 你的值可以写在这里，或者保持为空
            ]
        },
        'wait': {  # 若填写非空，则回放时匹配到的接口执行后进行额外的wait操作，time执行优先级高于rule，二者互斥
            'time': {  # 字典格式，指定某接口执行后额外增加wait时长，单位：秒，例如：'apiA': 5
                # 你的值可以写在这里，或者保持为空
            },
            'rule': {  # 字典格式，指定某接口执行后响应信息中某key匹配到某个规则，若未匹配成功，则一直重复执行该接口，例如：'apiA::data.orderId': 'is True'
                # 你的值可以写在这里，或者保持为空
            }
        },

    },
    'check': {  # Step 3 - 验证阶段配置，若填写非空，则进行response对比时匹配如下规则
        'select': [  # 列表格式，仅对比这些key及其后代层级，单项格式为response的全路径匹配，例如：status, data.items[0], data.items[0].number
            # 你的值可以写在这里，或者保持为空
        ],
        'ignore': [  # 列表格式，会忽略这些key及其后代层级，单项格式为response的全路径匹配，例如：timestamp, data.items[1], data.items[1].tag
            # 你的值可以写在这里，或者保持为空
        ],
        'rule': {  # 字典格式，这些key的验证由diff转为代码匹配，单项格式为response的全路径匹配，例如：'status': '==200', apiA::'data.items': '!=[]', 'data.items[0].number': '>=5'
            # 你的值可以写在这里，或者保持为空
        },
    }
}


if __name__ == '__main__':
    pass
    print json.dumps(default_conf)


