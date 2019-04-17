# -*- coding: utf-8 -*-
# --------------------------------------------------------------
#   When        Who         What
# --------------------------------------------------------------
# Apr 08,2019   idle-man    Create based on BSTestRunner
#

import sys
import cgi
import json
import time

from module.common.configer import MyIniHelper


# ----------------------------------------------------------------------
# Template
class ParrotTemplate(object):
    """
    Define a HTML template for report customerization and generation.
    Overall structure of an HTML report
    HTML
    +------------------------+
    |<html>                  |
    |  <head>                |
    |                        |
    |   STYLESHEET           |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |  </head>               |
    |                        |
    |  <body>                |
    |                        |
    |   HEADING              |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |   REPORT               |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |   ENDING               |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |  </body>               |
    |</html>                 |
    +------------------------+
    """
    STATUS = {
        0: 'pass',
        1: 'fail',
        2: 'error',
    }
    DEFAULT_TITLE = 'Test Report'
    DEFAULT_DESCRIPTION = ''
    # ------------------------------------------------------------------------
    # HTML Template
    HTML_TMPL = r"""<!DOCTYPE html>
<html lang="zh-cn">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    <title>%(title)s</title>
    <link rel="stylesheet" href="http://cdn.bootcss.com/bootstrap/3.3.0/css/bootstrap.min.css">
    %(stylesheet)s
    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="http://cdn.bootcss.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="http://cdn.bootcss.com/respond.js/1.4.2/respond.min.js"></script>
    <![endif]-->
  </head>
<body>
<script language="javascript" type="text/javascript">
    output_list = Array();
    /* level - 0:Pass; 1:Fail; 2:All */
    function showCase(level) {
        trs = document.getElementsByTagName("tr");
        for (var i = 0; i < trs.length; i++) {
            tr = trs[i];
            id = tr.id;
            if (id.substr(0,2) == 'ft') {
                if (level < 1) {
                    tr.className = 'hiddenRow';
                }
                else {
                    tr.className = '';
                }
            }
            if (id.substr(0,2) == 'pt') {
                if (level == 1) {
                    tr.className = 'hiddenRow';
                }
                else {
                    tr.className = '';
                }
            }
        }
    }
    function showTestDetail(div_id){
        var details_div = document.getElementById(div_id)
        var displayState = details_div.style.display
        // alert(displayState)
        if (displayState != 'block' ) {
            displayState = 'block'
            details_div.style.display = 'block'
        }
        else {
            details_div.style.display = 'none'
        }
    }
    function html_escape(s) {
        s = s.replace(/&/g,'&amp;');
        s = s.replace(/</g,'&lt;');
        s = s.replace(/>/g,'&gt;');
        return s;
    }
</script>
<div class="container">
    %(heading)s
    %(report)s
    %(ending)s
</div>
</body>
</html>
"""
    # variables: (title, generator, stylesheet, heading, report, ending)
    # ------------------------------------------------------------------------
    # Stylesheet
    #
    # alternatively use a <link> for external style sheet, e.g.
    #   <link rel="stylesheet" href="$url" type="text/css">
    STYLESHEET_TMPL = """
<style type="text/css" media="screen">
/* -- css div popup ------------------------------------------------------------------------ */
.popup_window_small {
    display: none;
    position: relative;
    left: 0px;
    top: 0px;
    /*border: solid #627173 1px; */
    padding: 10px;
    background-color: #ddd; /*#99CCFF;*/
    font-family: "Lucida Console", "Courier New", Courier, monospace;
    text-align: left;
    font-size: 10pt;
    width: 250px;
}
.popup_window_middle {
    display: none;
    position: relative;
    left: 0px;
    top: 0px;
    /*border: solid #627173 1px; */
    padding: 10px;
    background-color: #ddd; /*#99CCFF;*/
    font-family: "Lucida Console", "Courier New", Courier, monospace;
    text-align: left;
    font-size: 10pt;
    width: 500px;
}
.popup_window {
    display: none;
    position: relative;
    left: 0px;
    top: 0px;
    /*border: solid #627173 1px; */
    padding: 10px;
    background-color: #ddd; /*#99CCFF;*/
    font-family: "Lucida Console", "Courier New", Courier, monospace;
    text-align: left;
    font-size: 10pt;
    width: 900px;
}
/* -- report ------------------------------------------------------------------------ */
#show_detail_line .label {
    font-size: 85%;
    cursor: pointer;
}
#show_detail_line {
    margin: 2em auto 1em auto;
}
#total_row  { font-weight: bold; }
.hiddenRow  { display: none; }
.testcase   { margin-left: 0em; }
</style>
"""
    # ------------------------------------------------------------------------
    # Heading
    #
    HEADING_TMPL = """<div class='heading'>
<h1>%(title)s</h1>
%(parameters)s
<p class='description'>%(description)s</p>
</div>
""" # variables: (title, parameters, description)
    HEADING_ATTRIBUTE_TMPL = """<p><strong>%(name)s:</strong> %(value)s</p>
""" # variables: (name, value)
    # ------------------------------------------------------------------------
    # Report
    #
    REPORT_TMPL = """
<p id='show_detail_line'>
    <span class="label label-default" onclick="showCase(2)">All</span>
    <span class="label label-success" onclick="showCase(0)">Pass</span>
    <span class="label label-danger" onclick="showCase(1)">Fail</span>
</p>
<table id='result_table' class="table">
    <thead>
        <tr id='header_row'>
            <th>Test Case</td>
            <th>Result</td>
            <th>Status</td>
            <th>Duration</td>
            <th>Response</td>
            <th>Detail</td>
        </tr>
    </thead>
    <tbody>
        %(test_list)s
    </tbody>
    <tfoot>
        <tr id='total_row'>
            <td>&nbsp;</td>
            <td>&nbsp;</td>
            <td>&nbsp;</td>
            <td>&nbsp;</td>
            <td>&nbsp;</td>
            <td>&nbsp;</td>
        </tr>
    </tfoot>
</table>
""" # variables: (test_list)
    REPORT_CLASS_TMPL = r"""
<tr class='%(style)s'>
    <td>%(name)s</td>
    <td>%(result)s</td>
    <td>%(status)s</td>
    <td>%(duration)s</td>
    <td>%(response)s</td>
    <td>request</td>
</tr>
""" # variables: (style, name, result, status, duration, response)
    # align='center'
    REPORT_CASE_TMPL = r"""
<tr id='%(tid)s' class='%(case_style)s'>
    <td class='%(case_style)s'><div class='testcase'>%(name)s</div></td>
    <td class='%(case_style)s'><strong>%(result)s</strong></td>
    <td>
        <!--css div popup start-->
        <a style='width: 40px' class='%(status_style)s' onfocus='this.blur();' href="javascript:showTestDetail('div_%(tid)s_status')" >
            %(status_ret)s</a>
        <div id='div_%(tid)s_status' class="popup_window_small">
            <div style='text-align: right;cursor:pointer'>
            <a onfocus='this.blur();' onclick="document.getElementById('div_%(tid)s_status').style.display = 'none' " >
               [x]</a>
            </div>
            <pre>
%(status_content)s
            </pre>
        </div>
        <!--css div popup end-->
    </td>
    <td>
        <!--css div popup start-->
        <a style='width: 40px' class='%(dura_style)s' onfocus='this.blur();' href="javascript:showTestDetail('div_%(tid)s_duration')" >
            %(dura_ret)s</a>
        <div id='div_%(tid)s_duration' class="popup_window_small">
            <div style='text-align: right;cursor:pointer'>
            <a onfocus='this.blur();' onclick="document.getElementById('div_%(tid)s_duration').style.display = 'none' " >
               [x]</a>
            </div>
            <pre>
%(dura_content)s
            </pre>
        </div>
        <!--css div popup end-->
    </td>
    <td>
        <!--css div popup start-->
        <a style='width: 40px' class='%(resp_style)s' onfocus='this.blur();' href="javascript:showTestDetail('div_%(tid)s_response')" >
            %(resp_ret)s</a>
        <div id='div_%(tid)s_response' class="popup_window_middle">
            <div style='text-align: right;cursor:pointer'>
            <a onfocus='this.blur();' onclick="document.getElementById('div_%(tid)s_response').style.display = 'none' " >
               [x]</a>
            </div>
            <pre>
%(resp_content)s
            </pre>
        </div>
        <!--css div popup end-->
    </td>
    <td>
        <!--css div popup start-->
        <a class="popup_link btn btn-xs btn-primary" onfocus='this.blur();' href="javascript:showTestDetail('div_%(tid)s_detail')" >
            request</a>
        <div id='div_%(tid)s_detail' class="popup_window_middle">
            <div style='text-align: right;cursor:pointer'>
            <a onfocus='this.blur();' onclick="document.getElementById('div_%(tid)s_detail').style.display = 'none' " >
               [x]</a>
            </div>
            <pre>
%(detail_content)s
            </pre>
        </div>
        <!--css div popup end-->
    </td>
</tr>
""" # variables: (tid, case_style, name, result, status_style, status_ret, status_content, dura_style, dura_ret, dura_content, resp_style, resp_ret, resp_content, detail_content)
    REPORT_TEST_OUTPUT_TMPL = r"""
%(id)s: %(output)s
""" # variables: (id, output)
    # ------------------------------------------------------------------------
    # ENDING
    #
    ENDING_TMPL = """<div id='ending'>&nbsp;</div>"""
# -------------------- The end of the Template class -------------------


class ParrotReport(ParrotTemplate):
    """
    """
    def __init__(self, stream=sys.stdout, title=None, description=None):
        self.stream = stream
        if title is None:
            self.title = self.DEFAULT_TITLE
        else:
            self.title = title
        if description is None:
            self.description = self.DEFAULT_DESCRIPTION
        else:
            self.description = description

        self.STYLE = {
            'text_pass': 'text text-success',
            'text_fail': 'text text-danger',
            'text_default': 'text text-default',
            'btn_pass': 'popup_link btn btn-xs btn-success',
            'btn_fail': 'popup_link btn btn-xs btn-danger',
            'btn_default': 'popup_link btn btn-xs btn-default',
        }

    def run(self, result, start_time=0, end_time=0):
        self.START_TIME = start_time
        self.END_TIME = end_time
        self.generate_report(result)
        return result

    def generate_report(self, result):
        report_attrs = self._get_report_attributes(result)
        stylesheet = self._generate_stylesheet()
        heading = self._generate_heading(report_attrs)
        report = self._generate_report(result)
        ending = self._generate_ending()
        output = self.HTML_TMPL % dict(
            title = cgi.escape(self.title, quote=True),
            stylesheet = stylesheet,
            heading = heading,
            report = report,
            ending = ending,
        )
        try:
            self.stream.write(output.encode('utf8'))
        except:
            self.stream.write(output)

    def _get_report_attributes(self, result):
        """
        Return report attributes as a list of (name, value).
        Override this to add custom attributes.
        """
        status = []
        if result['total_count']: status.append('<span class="%s">Total <strong>%s</strong></span>' % (self.STYLE['text_default'], result['total_count']))
        if result['succ_count']: status.append('<span class="%s">Pass <strong>%s</strong></span>' % (self.STYLE['text_pass'], result['succ_count']))
        if result['fail_count']: status.append('<span class="%s">Fail <strong>%s</strong></span>' % (self.STYLE['text_fail'], result['fail_count']))

        if status:
            status = ' '.join(status)
        else:
            status = 'none'

        start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(str(self.START_TIME)[:-3]))) if self.START_TIME else 0
        end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(str(self.END_TIME)[:-3]))) if self.END_TIME else 0

        return [
            ('Start-Time', start_time),
            ('End-Time', end_time),
            ('Status', status),
        ]

    def _generate_stylesheet(self):
        return self.STYLESHEET_TMPL

    def _generate_heading(self, report_attrs):
        a_lines = []
        for name, value in report_attrs:
            line = self.HEADING_ATTRIBUTE_TMPL % dict(
                    # name=cgi.escape(name, quote=True),
                    # value=cgi.escape(value, quote=True),
                    name=name,
                    value=value,
                )
            a_lines.append(line)
        heading = self.HEADING_TMPL % dict(
            title=cgi.escape(self.title, quote=True),
            parameters=''.join(a_lines),
            description=cgi.escape(self.description, quote=True),
        )
        return heading

    def _generate_report(self, result):
        rows = []
        for case_result in result['result']:
            # style, name, result, status, duration, response
            # row = self.REPORT_CLASS_TMPL % dict(
            #     style = self.STYLE['text_pass'] if case_result['result'] == 'pass' else self.STYLE['text_fail'],
            #     name = case_result['name'],
            #     result = case_result['result'],
            #     status = case_result['status_ret'],
            #     duration = case_result['dura_ret'],
            #     response = case_result['resp_ret'],
            # )
            # rows.append(row)
            self._generate_report_test(rows, case_result)
        report = self.REPORT_TMPL % dict(
            test_list = ''.join(rows),
        )
        return report

    def _generate_report_test(self, rows, case_result):
        # print json.dumps(case_result)
        tmpl = self.REPORT_CASE_TMPL
        # tid, case_style, name, result, status_style, status_ret, status_content, dura_style, dura_ret, dura_content, resp_style, resp_ret, resp_content, detail_content
        row = tmpl % dict(
            tid = case_result['id'],
            case_style = self.STYLE['text_pass'] if case_result['result'] == 'pass' else self.STYLE['text_fail'],
            name = case_result['name'],
            result = case_result['result'],
            status_style = self.STYLE['btn_pass'] if case_result['status_ret'] == 'pass' else self.STYLE['btn_fail'],
            status_ret = case_result['status_ret'],
            status_content = cgi.escape(case_result['status_content'], quote=True),
            dura_style=self.STYLE['btn_pass'] if case_result['dura_ret'] == 'pass' else self.STYLE['btn_fail'],
            dura_ret=case_result['dura_ret'],
            dura_content=cgi.escape(case_result['dura_content'], quote=True),
            resp_style=self.STYLE['btn_pass'] if case_result['resp_ret'] == 'pass' else self.STYLE['btn_fail'],
            resp_ret=case_result['resp_ret'],
            resp_content=cgi.escape(case_result['resp_content'], quote=True),
            detail_content=cgi.escape(case_result['detail_content'], quote=True),
        )
        rows.append(row)

    def _generate_ending(self):
        return self.ENDING_TMPL


if __name__ == "__main__":
    fp = open('../../test/test-report.html', 'wb')
    runner = ParrotReport(stream=fp,
        title='Parrot流量回放测试报告',
        description='')
    result_dict = {'total_count': 0, 'succ_count': 0, 'fail_count': 0, 'result': []}
    i_file = '../../data/demo-report.ini'
    my_dict = MyIniHelper.ini2dict(filename=i_file)
    # print json.dumps(my_dict)
    s_time = e_time = 0
    for my_id in my_dict['IDS']:
        case_dict = my_dict[my_id]
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
        resp_content += "\nDiff: %s\nselect conf: %s\nignore conf:%s\nrule conf:%s" % (resp_diff, conf_select, conf_ignore, conf_rule)
        detail_content = "id: %s\nprotocol: %s\nmethod: %s\nhost: %s\nurl: %s\nparameter: %s\nheader:%s" % (case_id, case_protocol, case_method, case_host, case_url, case_parameter, case_header)

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

    print json.dumps(result_dict)
    runner.run(result=result_dict, start_time=s_time, end_time=e_time)
