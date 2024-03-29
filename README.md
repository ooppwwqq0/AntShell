# AntShell 说明

```
                         _______  __    _  _______  _______  __   __  _______  ___      ___
                        |   _   ||  |  | ||       ||       ||  | |  ||       ||   |    |   |
                        |  |_|  ||   |_| ||_     _||  _____||  |_|  ||    ___||   |    |   |
                        |       ||       |  |   |  | |_____ |       ||   |___ |   |    |   |
                        |       ||  _    |  |   |  |_____  ||       ||    ___||   |___ |   |___
                        |   _   || | |   |  |   |   _____| ||   _   ||   |___ |       ||       |
                        |__| |__||_|  |__|  |___|  |_______||__| |__||_______||_______||_______|


                                       ___           ___              _   _      _
                                      / __\_   _    / __\__ _ ___ ___| |_(_) ___| |
                                     /__\// | | |  / /  / _` / __/ __| __| |/ _ \ |
                                    / \/  \ |_| | / /__| (_| \__ \__ \ |_| |  __/ |
                                    \_____/\__, | \____/\__,_|___/___/\__|_|\___|_|
                                           |___/
```

AntShell项目已通过Go语言重构，新版本将在Go版本继续更新，python版本不再进行更新

[Go版本地址](https://github.com/ooppwwqq0/AntShell-Go)

> 2017年9月14日正式更名AntShell（原名Adam）

## 功能参数解析

### 功能模式

### 常用参数组合

```
# 筛选主机
a -s name | a -s ip
a -n num
a -s name -n num
a num | a name | a ip
```

### 参数优先级

## 未实现功能及特性

## 目前已知bug

* 文件传输模块tqdm无法在python3下正常运行

## 未完成

* 新增sqlite模式自动备份机制
* 新增主机多级分组机制
* 需要完善分组机制
* 主机信息显示顺序修改
* web管理功能
* 添加ansible模块替代部分功能（待定）
* session模式（待定）

## 0.6-beta

* 数据库操作封装sqlite操作，去除文件模式
* 重新处理初始化操作
* 选项模块修改为argparse
* 抛弃pexpect，使用paramiko获取终端
* 系统配置文件（语言相关）拆分  
* 添加自动加载默认配置文件位置
* 配置文件修改为ini格式，重构配置文件加载方式
* 新增堡垒机模式
  * 支持将堡垒机作为登录跳转
  * 支持堡垒机根据totp自动计算动态token验证码（齐治堡垒机，其他堡垒机未测试）(brew install oath-toolkit)
  * 新增命令行参数指定新增主机记录时是否开启堡垒机模式
* 将默认sudo用户root修改为可通过命令行参数配置
  * 新增命令行参数指定新增主机记录时默认sudo用户
  * 登录主机时使用命令韩sudo命令行参数覆盖数据库保存的默认sudo用户
* 新增error处理
* 新增debug参数，打印debug信息
* 主机信息打印微调
* 主机编辑模式
  * 新增主机记录调整
  * 删除记录调整
  * 新增编辑模式
* 去除批量执行命令、上传、下载模式


## 0.5-beta

> 由于0.4版本变更太多，并且本次版本较之前也会有很大变化，因此重新切出0.5版本

* 修改默认语言设置为中文
* 修改输出信息颜色列表颜色重复的问题
* 修改部分方法为静态方法；部分方法、属性为私有
* 重构加载配置文件代码，以及添加加载配置文件失败的判断
    * 先检测配置文件位置
    * 然后再加载配置文件
* 封装数据库操作
* 更新install.py
    * 新增初始化配置文件功能
    * 完善数据文件与数据库互转
* 重构代码
	* 搜索主机列表重构
	* 新增交互模式下的多重搜索（暂时未或条件，后续改成与条件）
	* 新的主机交互列表 
	* 新增单页模式，上下翻页，清楚搜索历史
	* 新增title模式的颜色输出
	* 去掉线程模式，改为协程模式
	* 重构tqdm进度条类
	* 拆分主机信息打印方法到base中(合并成一个方法)
	* 拆分ssh类，拆分paramiko方法到paramiko单独类
* 修复bug
	* 主机列表输出
	* 获取sshkey位置认证
    * 修复拆分后没导入signal模块导致的不能自动变更终端大小的bug-0.5.7
    * 修复python3 input兼容问题，修复python bytes 与 str兼容问题 0.5.8
    * 添加主机数据时第一次不能添加都是bug
    * 修复python3需要导入reduce的问题
* 第一次执行自动生成配置文件

## 0.4-beta
* 修复stty无法随终端大小变化的bug
* 重构全部代码结构，合并部分功能类
* 重构部分代码逻辑
* 使用paramiko获取ssh终端
* 彻底去除pexpect模块
* 主机信息存储改为sqlite3
* 去除file数据模式
* 新增name自定义参数
* 调整命令行参数
* 添加install.py
    * 生成sqlite3数据库文件，初始化表结构
    * file数据迁移至sqlite3
* 增加配置文件默认读取位置
    * env ANTSHELL_CONFIG
    * ~/.antshell/antshell.yml
    * /etc/antshell/antshell.yml
    * $CWD/antshell.yml
* 修改新增主机，删除主机逻辑代码
* 修改为pypi安装包
* 修改目录结构
* 新增bin下系统命令
* 配置文件拆分成系统配置和用户自定义配置
* 拆分部分脚本功能，优化部分结构
* 新增agent模式（-A|--agent）参数，默认开启agent模式，参数禁用sudo模式
    * agent模式似乎需要本机ssh -A开启过一次agent才能生效，待测试
* 新增登录时打印banner
* 修改banner颜色，增加自定义banner颜色（预设）功能
* 修复文件传输以及命令执行模式下fast参数无效的bug

## 0.3-beta

* 删除old模式
* 删除fast-file模式登录
* 新增帮助信息程序描述
* 添加参数项组以及子参数配置
* 优化部分代码流程
* 新增添加主机记录时可指定用户名、端口、密码
* bug修复，兼容性修复（-a添加主机的匹配结果问题，-c的python3兼容问题）
* bug修复，修复传输文件时-s后-n选项失效问题
* bug修复，修复传输文件时-a首次添加ip依然出现交互列表的bug
* 优化-s搜索模式，输入全ip自动精确匹配
* 修复文件传输时，-n指定机器编号无法执行问题

## 0.2-beta

* optparse修改为argparse
* 新增argparse参数v
* fast主机操作中sys.argv修改为argparse.v参数

## 0.1-beta

### 已实现功能及特性

* 兼容python2、pyhton3
* 配置文件使用yml格式
* 支持配置项自定义
* 支持帮助菜单中英文配置
* 数据文件使用file格式
* 支持新增记录，删除记录
* 支持主机打印列表自适应或指定列数
* 支持指定主机编号登录
* 支持快速主机编号登录(fast,sys.argv)
* 支持搜索主机信息登录
* 支持选定主机批量远程执行命令
* 支持指定命令分隔符
* 支持选定主机批量上传下载文件，有进度条
* 支持秘钥登录，密码登录
* 支持自定默认用户名，端口号
* 支持远程登录自动sudo
* 支持远程登录后执行指定命令
* 保留old模式登录, -o 开启
* 保留fast-file模式登录
* 菜单模块使用optparse

## HELP

```
usage: AntShell [ -h | --version ] [-l [-m 2] ]
            [ v | -n 1 | -s 'ip|name' ] [ -G g1>g2 ]
            [ -e | -a ip [--name tag | --user root | --passwd xx | --port 22 ] | -d ip ]
            [ -P -c 'cmd1,cmd2,...' ]
            [ -f file_name [-g file_path | -p dir_path [-F ','] ] ]

AntShell 远程登录管理工具

positional arguments:
  v                     fast模式位置变量

sys arguments:
  -h, --help            打印帮助信息并退出
  --version             打印版本信息并退出

edit arguments:
  -a ip, --add ip       添加主机信息并登陆
  -e, --edit            编辑主机信息
  -d ip, --delete ip    删除主机信息并退出
  --name tag            标记名
  --user root           用户名
  --passwd xxx          密码
  --port 22             端口

host arguments:
  -l                    输出主机列表并退出
  -m 2, --mode 2        列表显示列数1-5
  -n 0                  选择连接的主机编号
  -s 'ip|name', --search 'ip|name'
                        模糊匹配主机信息
  -G g1>g2              过滤群组主机

manager arguments:
  -P                    paramiko模式
  -c 'cmd1,cmd2,...'    主机远程执行命令
  -f file_name, --file file_name
                        文件名
  -g file_path, --get file_path
                        获取文件路径
  -p dir_path, --put dir_path
                        指定文件路径
  -F ',', --fs ','      指定分隔符，默认<,>
```
