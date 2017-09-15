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

> 2017年9月14日正式更名AntShell（原名Adam）

## 功能参数解析
### 功能模式

### 常用参数组合

``` bash
# 筛选主机
a -s name | a -s ip
a -n num
a -s name -n num
a num | a name | a ip
```

### 参数优先级

## HELP

``` bash
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

## 未实现功能及特性

* 数据文件新增sqlite3格式，暂时保留两种数据格式，最终去除file模式
* 支持file格式升级到sqlite3格式（需要完成sqlite3）
* 新增sqlite模式自动备份机制（需要完成sqlite3）
* 删除old模式（已完成）
* 删除fast-file模式登录，并根据sqlite格式新增fast模式（需要完成sqlite3）
* 选项模块修改为argparse（已完成）
* 完成主机信息编辑，包括信息修改，显示顺序修改等（需要完成sqlite3）
* 新增主机多级分组机制（需要完成sqlite3）
* 未来版本讲抛弃pexpect，使用paramiko获取终端（已完成）
* 添加ansible模块替代部分功能，待定
* 重构代码结构
* 添加自动加载默认配置文件位置（已完成）
* 需要添加ini配置文件支持
* 需要拆分系统配置和用户自定义配置文件（已完成）

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

