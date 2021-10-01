#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/10/1 21:17
# @Author  : sgwang
# @File    : cond.py
# @Software: PyCharm
import datetime
import re

import yaml


class cond(object):
    __should_do_list = ["浏览", "逛逛"]

    def __init__(self):
        pass

    @classmethod
    def add_config_task(cls, my_tasks: list):
        # [{'title_text' : '参加活动01', 'end_date':"2021-01-02"}, {'title_text' : '参加活动02', 'end_date':None}]
        for item in my_tasks:
            if 'end_date' not in item or item['end_date'] is None or str(item['end_date']).strip() == "":
                cls.__should_do_list.append(item['title_text'])
                continue

            elif datetime.datetime.now() <= datetime.datetime.strptime(item['end_date'], '%Y-%m-%d'):
                cls.__should_do_list.append(item['title_text'])
                continue

    @classmethod
    def task_should_do(cls, text: str) -> bool:

        for _ in cls.__should_do_list:
            if _ in text:
                return True
        return False

    @staticmethod
    def btn_status(text: str) -> int:
        _status_dict = {
            "已完成": 0,
            "领奖励": 1,
            "其它": -1
        }

        return _status_dict.get(text, -1)

    @staticmethod
    def task_wait_seconds(text: str) -> int:
        _cn_second = re.compile("\\d+秒").search(text)
        _en_big_second = re.compile('\\d+S').search(text)
        _en_small_second = re.compile('\\d+s').search(text)

        if _cn_second:
            return int(_cn_second.group().replace("秒", ""))
        elif _en_big_second:
            return int(_en_big_second.group().replace("S", ""))
        elif _en_small_second:
            return int(_en_small_second.group().replace("s", ""))

        return int(0)


if __name__ == "__main__":
    wri_task = [
        {'title_text': '参加活动01', 'end_date': "2021-11-02"},
        {'title_text': '参加活动02', 'end_date': None},
        {'title_text': '参加活动03'}
    ]

    red_task = yaml.safe_load(open("../add_tasks.yaml", 'r', encoding='utf-8'))

    cond.add_config_task(wri_task)
    print(cond.task_should_do("参加活动01"))
    print(cond.task_should_do("参加活动02"))
    print(cond.task_should_do("参加活动03"))

    print(cond.task_should_do("参加活动04"))
    print(cond.task_should_do("参加活动"))
