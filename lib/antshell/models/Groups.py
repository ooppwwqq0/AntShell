#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/10/22 9:18 下午
# @Author  : Parsifal
# @File    : Hosts.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()


# 定义映射类User，其继承上一步创建的Base
class Groups(Base):
    # 指定本类映射到users表
    __tablename__ = 'groups'
    # 如果有多个类指向同一张表，那么在后边的类需要把extend_existing设为True，表示在已有列基础上进行扩展
    # 或者换句话说，sqlalchemy允许类是表的字集
    # __table_args__ = {'extend_existing': True}
    # 如果表在同一个数据库服务（datebase）的不同数据库中（schema），可使用schema参数进一步指定数据库
    # __table_args__ = {'schema': 'test_database'}

    # 各变量名一定要与表的各字段名一样，因为相同的名字是他们之间的唯一关联关系
    # 从语法上说，各变量类型和表的类型可以不完全一致，如表字段是String(64)，但我就定义成String(32)
    # 但为了避免造成不必要的错误，变量的类型和其对应的表的字段的类型还是要相一致
    # sqlalchemy强制要求必须要有主键字段不然会报错，如果要映射一张已存在且没有主键的表，那么可行的做法是将所有字段都设为primary_key=True
    # 不要看随便将一个非主键字段设为primary_key，然后似乎就没报错就能使用了，sqlalchemy在接收到查询结果后还会自己根据主键进行一次去重
    # 指定id映射到id字段; id字段为整型，为主键，自动增长（其实整型主键默认就自动增长）
    id = Column(Integer, primary_key=True, autoincrement=True)
    sort = Column(Integer, default=0)
    name = Column(String(50))
    user = Column(String(50))
    passwd = Column(String(100))
    port = Column(Integer, default=22)
    sudo = Column(String(50), default="")
    bastion = Column(Integer, default=0)
    create_at = Column(DateTime)
    update_at = Column(DateTime)

    # __repr__方法用于输出该类的对象被print()时输出的字符串，如果不想写可以不写
    def __repr__(self):
        return "<Groups(name='%s', %s(%s)@%s:%s)>" % (
            self.name, self.user, self.sudo, self.port)

