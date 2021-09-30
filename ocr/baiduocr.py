#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/9/29 14:52
# @Author  : sgwang
# @File    : baiduocr.py
# @Software: PyCharm
import base64
import os
import time
import traceback

from PIL import Image
from aip import AipOcr
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as Exc
# 获取当前文件的绝对路径
from selenium.webdriver.support.wait import WebDriverWait

from utils import Final
from utils.config import get_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 临时图片保存，绝对路径
IMG_DIR = BASE_DIR + os.sep + 'img' + os.sep
if not os.path.exists(IMG_DIR):
    os.mkdir(IMG_DIR)

# 大小图片固定命令
SMALL_IMG = "small.jpg"
BIG_IMG = "big.jpg"


def get_img_file(filename):
    """读取图片文件"""
    with open(IMG_DIR + filename, 'rb') as fp:
        return fp.read()


class ocrapi(object):

    def __init__(self, _driver: WebDriver, _config):
        # selenium驱动
        self.driver = _driver
        self.APP_ID = _config['APP_ID']
        self.API_KEY = _config['API_KEY']
        self.SECRET_KEY = _config['SECRET_KEY']

        # 百度文字识别sdk客户端
        self.orcClient = AipOcr(self.APP_ID, self.API_KEY, self.SECRET_KEY)

    @staticmethod
    def flush_img(_driver):
        WebDriverWait(_driver, Final.timeout.s10).until(
            Exc.visibility_of_element_located((By.CLASS_NAME, "cpt-choose-refresh"))
        ).click()

    def download_img(self):
        """将图片保存到本地"""
        small_src = WebDriverWait(self.driver, Final.timeout.s10).until(
            Exc.visibility_of_element_located((By.CLASS_NAME, "cpt-small-img"))
        ).get_attribute("src")
        with open(IMG_DIR + SMALL_IMG, "wb") as f:
            f.write(base64.b64decode(small_src.split(',')[1]))
            f.close()

        big_src = WebDriverWait(self.driver, Final.timeout.s10).until(
            Exc.visibility_of_element_located((By.CLASS_NAME, "cpt-big-img"))
        ).get_attribute("src")
        with open(IMG_DIR + BIG_IMG, "wb") as f:
            f.write(base64.b64decode(big_src.split(',')[1]))
            f.close()

    def get_small_words(self):
        """识别上面小图中的文字"""
        ret_words = ''

        try:
            op = {'language_type': 'CHN_ENG', 'detect_direction': 'true'}
            res = self.orcClient.basicAccurate(get_img_file(SMALL_IMG), options=op)
            for item in res['words_result']:
                if item['words'].endswith('。'):
                    ret_words = ret_words + item['words'] + '\r\n'
                else:
                    ret_words = ret_words + item['words']
            return ret_words
        except:
            print(traceback.format_exc())
            return ret_words

    def get_big_pos(self, words: list):
        """识别下面大图中文字的坐标"""
        # 所有文字的位置信息，需要的文字的位置信息
        all_pos_info, ret_pos_info = list(), list()

        try:
            op = {'language_type': 'CHN_ENG', 'recognize_granularity': 'small', 'detect_direction': 'true'}
            res = self.orcClient.accurate(get_img_file(BIG_IMG), options=op)

            # 收集字符信息
            for item in res['words_result']:
                all_pos_info.extend(item['chars'])

            # 筛选出需要的文字的位置信息
            for word in words:
                for item in all_pos_info:
                    if word == item['char']:
                        ret_pos_info.append(item)

            return ret_pos_info
        except:
            print(traceback.format_exc())
            return ret_pos_info

    def click_words(self, big_pos_info):
        """按顺序点击图片中的文字"""
        ele_big_img = WebDriverWait(self.driver, Final.timeout.s5).until(
            Exc.visibility_of_element_located((By.CLASS_NAME, "cpt-big-img")))

        # 根据上图文字在下图中的顺序依次点击下图中的文字，注意需要加上字体的长度
        for info in big_pos_info:
            ActionChains(self.driver).move_to_element_with_offset(
                to_element=ele_big_img, xoffset=info['location']['left'] + 20, yoffset=info['location']['top'] + 20
            ).click().perform()

        # 点击提交
        self.driver.find_element(By.CLASS_NAME, 'cpt-choose-submit').click()

    def work(self):
        # 下载验证图片
        self.download_img()

        # 增加对比度，提高识别
        Image.open(IMG_DIR + SMALL_IMG).point(lambda p: p * 4).save(IMG_DIR + SMALL_IMG)
        Image.open(IMG_DIR + BIG_IMG).point(lambda p: p * 4).save(IMG_DIR + BIG_IMG)

        # 识别小图文字
        small_text = self.get_small_words()
        small_text = list(small_text)

        # 获取大图的文字位置信息
        big_pos_info = self.get_big_pos(small_text)

        if len(big_pos_info) < len(small_text):
            print("大图识别到的字符，比小图识别到的字符，还要少，可以刷新重试了！")
            time.sleep(3)
            return self.driver.current_url

        print('根据ocr识别结果，点击提交')
        self.click_words(big_pos_info)

        time.sleep(3)
        return self.driver.current_url


if __name__ == '__main__':
    from selenium import webdriver

    # 打开Chrome浏览器，需要将Chrome的驱动放在当前文件夹
    driver = webdriver.Chrome(executable_path="../drivers/chromedriver")
    driver.get('https://hotels.ctrip.com/hotel/6278770.html')

    # 获取配置
    config = get_config(file_name="test_config.yaml")

    # 开始破解
    unlock = ocrapi(driver, config)

    # 滑块element
    scrollElement = driver.find_elements_by_class_name('cpt-img-double-right-outer')[0]
    ActionChains(driver).click_and_hold(on_element=scrollElement).perform()
    ActionChains(driver).move_to_element_with_offset(to_element=scrollElement, xoffset=30, yoffset=10).perform()
    ActionChains(driver).move_to_element_with_offset(to_element=scrollElement, xoffset=100, yoffset=20).perform()
    ActionChains(driver).move_to_element_with_offset(to_element=scrollElement, xoffset=200, yoffset=50).perform()

    unlock.work()
