# Parrot(鹦鹉)流量回放框架
## 使用说明
### Step 0：准备环境、源数据和项目配置
Python环境
* 项目目前基于Python2实现，需要准备Python环境，建议版本2.7.x
* 项目依赖的第三方module均配置在requirements.txt中，可采用`pip install -r requirements.txt`进行批量安装
* 脚本执行均采用命令行方式操作，先cd到Parrot项目目录下

目前流量回放工具支持标准的抓包导出文本
* Charles导出的trace文件
* Fiddler导出的txt文件

请参考config/template.yaml和demo.yaml的格式和内容，构建自己项目的yaml配置文件
* 根据自己的项目情况，复制并编辑自己的项目配置

### Step 1：流量录制
目前的流量录制，实际是将前面步骤准备的源文件解析为回放所需的标准格式化ini文件
* 根据yaml config内的说明，配置自己项目的record阶段配置，也可保持为空
* `python recorder.py -h`查看具体用法
* 本阶段执行会生成record.ini文件，用于后续的流量回放和结果验证

### Step 2：流量回放
目前仅支持HTTP(S)的流量回放，暂无法用于大数据量并发
* 根据yaml config内的说明，配置自己项目的replay阶段配置，也可保持为空
* 执行本步骤之前，记得先执行流量录制生成自己的record.ini
* `python replayer.py -h`查看具体用法
* 本阶段执行会生成replay.ini文件，用于后续的结果验证

### Step 3：结果验证
目前的验证主要通过对录制流量和回放流量的status和response进行对比来判定结果
* 根据yaml config内的说明，配置自己项目的check阶段配置，也可保持为空
* 执行本步骤之前，记得先执行流量录制和流量回放生成自己的record.ini、replay.ini
* `python checker.py -h`查看具体用法
* 本阶段执行会生成report.ini和report.html文件，供查看结果验证的详情


## Project Framework
* config/
    * config.py: 全局配置和项目默认配置，一般无需修改
    * template.yaml: 项目配置模板，可参照复制编辑自己的项目配置，具体参见文件自身内容及注释
* module/
    * common/
        * helper.py
            * MyTimeHelper: 常用的date和time方法集，如时间戳
            * MyFileHelper: 常用的目录和文件方法集，如删除文件
            * MyRandomHelper: 常用的随机方法集，如随机字符串、中文
            * MyDictHelper: 将字典/列表解析为深度为1的KV组合，便于diff
        * configer.py
            * MyConfigHelper: 对config的解析及select、ignore、store、replace、wait操作
            * MyIniHelper: 支持ini文件格式和dict之间的相互转换
        * logger.py
            * Logger: 不同级别日志打印，同时输出到屏幕和log文件
        * reportor.py
            * Reportor: 待开发-可视化报告输出，便于查阅
    * record/
        * parser.py
            * MyParser: 解析Charles.trace和Fiddler.txt，匹配规则，输出ini文件
    * replay/
        * request.py
            * MyHttpHelper: 支持http(s)的请求及结果获取
    * check/
        * differ.py
            * MyDiffer: 进行两个字符串、列表、字典对比，支持select、ignore、rule
* data/
    * record、replay、report ini/html文件的默认存储路径
* tmp/
    * replay执行过程中的临时文件存放路径
* recorder.py
    * 流量回放步骤一 - 录制 - 主入口，`python recorder.py -h`查看具体用法
* replayer.py
    * 流量回放步骤二 - 回放 - 主入口，`python replayer.py -h`查看具体用法
* checker.py
    * 流量回放步骤三 - 验证 - 主入口，`python checker.py -h`查看具体用法
* requirements.txt
    * 项目所需第三方module，可采用`pip install -r requirements.txt`进行批量安装
* CHANGELOG.md
    * 项目release日志

## ini文件结构说明
### 回放所需
* protocol
* method
* host
* url
* parameter
* header

### 验证所需
* status
* duration
* response

