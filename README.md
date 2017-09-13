# ADAM登录程序说明


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
* 添加ansible模块替代部分功能
* 重构代码结构

## 0.4-beta
* 重构部分代码逻辑以及结构(基类以及配置获取)
* 合并部分类
* 使用paramiko获取ssh终端
* 彻底去除pexpect模块
* 重构全部代码结构
* 重构部分代码逻辑
* 主机信息存储改为sqlite3

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

### 老版本help

``` bash
Usage: a [OPTIONS]

Options:
  -v, --version         打印版本信息并退出
  -h, --help            打印帮助信息并退出
  -a ip, --add=ip       添加主机信息并登陆
  -c 'cmd1,cmd2,...', --commod='cmd1,cmd2,...'
                        主机远程执行命令
  -e, --edit            编辑主机信息
  -d ip, --delete=ip    删除主机信息并退出
  -f file_name, --file=file_name
                        文件名
  -F ',', --fs=','      指定分隔符，默认<,>
  -g file_path, --get=file_path
                        获取文件路径
  -G g1>g2, --group=g1>g2
                        过滤群组主机
  -l, --lists           输出主机列表并退出
  -m 2, --mode=2        列表显示列数1-5
  -n 0, --num=0         选择连接的主机编号
  -p dir_path, --put=dir_path
                        指定文件路径
  -P, --para            paramiko模式
  -s ip|name, --search=ip|name
                        模糊匹配主机信息
  -o, --old             old-sh-file模式登陆主机
```

### 新版本help

``` bash
usage: a [-h] [--version] [-a ip] [-c 'cmd1,cmd2,...'] [-e] [-d ip]
         [-f file_name] [-F ','] [-g file_path] [-G g1>g2] [-l] [-m 2] [-n 0]
         [-p dir_path] [-P] [-s ip|name] [-o]

usage: %prog [options] poetry-file

optional arguments:
  -h, --help            打印帮助信息并退出
  --version             打印版本信息并退出
  -a ip, --add ip       添加主机信息并登陆
  -c 'cmd1,cmd2,...', --commod 'cmd1,cmd2,...'
                        主机远程执行命令
  -e, --edit            编辑主机信息
  -d ip, --delete ip    删除主机信息并退出
  -f file_name, --file file_name
                        文件名
  -F ',', --fs ','      指定分隔符，默认<,>
  -g file_path, --get file_path
                        获取文件路径
  -G g1>g2, --group g1>g2
                        过滤群组主机
  -l, --lists           输出主机列表并退出
  -m 2, --mode 2        列表显示列数1-5
  -n 0, --num 0         选择连接的主机编号
  -p dir_path, --put dir_path
                        指定文件路径
  -P, --para            paramiko模式
  -s ip|name, --search ip|name
                        模糊匹配主机信息
  -o, --old             old-sh-file模式登陆主机
```


