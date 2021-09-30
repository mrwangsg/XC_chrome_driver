#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/9/28 18:36
# @Author  : sgwang
# @File    : Final.py
# @Software: PyCharm
# 单例


def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]

    return inner


@singleton
class timeout(object):

    def __init__(self):
        pass

    @property
    def s3(self) -> int:
        return int(3)

    @property
    def s5(self) -> int:
        return int(5)

    @property
    def s10(self) -> int:
        return int(10)

    @property
    def s15(self) -> int:
        return int(15)

    @property
    def s30(self) -> int:
        return int(30)

    @property
    def s60(self) -> int:
        return int(60)

    @property
    def m1(self) -> int:
        return int(1 * 60)

    @property
    def m3(self) -> int:
        return int(3 * 60)


timeout = timeout()

if __name__ == "__main__":
    print(timeout.s10)
    print(timeout.m3)
