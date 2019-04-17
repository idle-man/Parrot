# -*- coding: utf-8 -*-
# --------------------------------------------------------------
#   When        Who         What
# --------------------------------------------------------------
# Jan 18,2019   idle-man    Create HttpHelper to support http get/post request
# Mar 12,2019   idle-man    Rebuild HttpHelper and make it simple
#

import json
import requests
from module.common.helper import MyTimeHelper


class MyHttpHelper:
    __author__ = 'idle-man'
    __desc__ = "对requests module做了简单封装，支持http和https请求"

    def __init__(self):
        pass

    @staticmethod
    def request(url, method='get', param=None, header=None, retry=1, timeout=5):
        while retry > 0:
            s_time = int(MyTimeHelper.now_unix_timestamp_ms())
            try:
                if method.lower().strip() in ('post', 'put', 'patch'):
                    response = requests.request(
                        url=url,
                        method=method.lower().strip(),
                        data=param,
                        headers=header,
                        timeout=timeout)
                else:
                    response = requests.request(
                        url=url,
                        method=method.lower().strip(),
                        params=param,
                        headers=header,
                        timeout=timeout)
                # print response.status_code, response.text, response.content, response.headers
                if response.status_code:
                    e_time = int(MyTimeHelper.now_unix_timestamp_ms())
                    msg = "".join(response.text.split("\n"))
                    return {"result": True,
                            "status": response.status_code,
                            "msg": msg,
                            "header": response.headers,
                            "start-time": s_time,
                            "end-time": e_time,
                            "duration": e_time - s_time}
            except Exception as e:
                msg = e.message

            retry -= 1  # 重试次数递减

            e_time = int(MyTimeHelper.now_unix_timestamp_ms())

        return {"result": False, "status": "Unknown", "msg": msg, "header": header, "start-time": s_time, "end-time": e_time, "duration": timeout*1000}


if __name__ == '__main__':
    my_url = 'http://httpbin.org/'
    my_param = 'TimeStamp=1551355237000&UserId=083e29e59c0b257813af7cb454b1e0e9&Token=w6XCs4YqWnIEbJpDKvQHtMr7OZ8Rjkyl&From=SuZhou&To=ShangHai'
    my_header = '{"Accept-Language": "zh-CN,en-US;q=0.8", "Accept-Encoding": "gzip,", "Accept": "*/*", "User-Agent": "Mozilla/5.0", "Connection": "keep-alive", "X-Requested-With": "XMLHttpRequest"}'

    print "http get:", MyHttpHelper.request(url=my_url+'get', method='get', param=my_param, header=json.loads(my_header))
    print "http post:", MyHttpHelper.request(url=my_url+'post', method='post', param=my_param, header=json.loads(my_header))
    print "http put:", MyHttpHelper.request(url=my_url + 'put', method='put', param=my_param, header=json.loads(my_header))
    print "http delete:", MyHttpHelper.request(url=my_url + 'delete', method='delete', param=my_param, header=json.loads(my_header))
    print "http head:", MyHttpHelper.request(url=my_url + 'head', method='head', param=my_param, header=json.loads(my_header))
    print "http options:", MyHttpHelper.request(url=my_url + 'options', method='options', param=my_param, header=json.loads(my_header))
    print "http patch:", MyHttpHelper.request(url=my_url + 'patch', method='patch', param=my_param, header=json.loads(my_header))
