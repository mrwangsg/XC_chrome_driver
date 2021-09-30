#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/9/28 20:19
# @Author  : sgwang
# @File    : crtip.py
# @Software: PyCharm
import time
import traceback

from selenium.common.exceptions import MoveTargetOutOfBoundsException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as Exc
from selenium.webdriver.support.wait import WebDriverWait

from ocr.baiduocr import ocrapi
from utils import Final


def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]

    return inner


@singleton
class page(object):

    def __init__(self):
        pass

    @staticmethod
    def scroll(browser: WebDriver, account: str, password: str):
        ele_account = browser.find_element(By.NAME, "ctripAccount")
        ele_password = browser.find_element(By.NAME, "ctripPassword")
        ele_login_btn = browser.find_element(By.TAG_NAME, "button")

        ele_account.send_keys(account)
        ele_password.send_keys(password)
        ele_login_btn.click()

        try:
            # 等待活动校验窗口出现
            ele_drop_btn = WebDriverWait(browser, Final.timeout.s30).until(
                Exc.visibility_of_element_located((By.CLASS_NAME, "cpt-drop-btn")), "滑动校验窗口，没有弹出")

            # 滑动滑块
            cycle_drop, times, width = True, int(10), browser.get_window_size().get('width')
            while cycle_drop and times > 0 and width > 0:
                try:
                    ActionChains(browser).click_and_hold(ele_drop_btn) \
                        .drag_and_drop_by_offset(ele_drop_btn, width, 0).perform()
                except MoveTargetOutOfBoundsException:
                    width = width - 30
                    times = times - 1
                    continue
                cycle_drop = False

            # 循环结束后，立即刷新验证图片。因为第一轮的，基本难以识别
            ocrapi.flush_img(browser)
            return True

        except TimeoutException as ex:
            print(ex.msg)
            return False

    @staticmethod
    def login(browser: WebDriver, account: str, password: str, _ocr_api: ocrapi = None):
        # 携程有个奇怪现象，多点几次登录按钮，可能会跳过验证码步骤
        flush_times, scroll_status = int(3), False
        for _ in range(flush_times):
            # 打开页面
            browser.get(url.login_account)

            # 滑动滑块
            scroll_status = page.scroll(browser, account, password)

            # 如果直接跳转到了，登录成功界面，跳出登录，返回成功
            if str(browser.current_url).startswith(url.login_success):
                print(f"刷新{_}次后，直接登录成功！")
                return True

            # 每次刷新都等待一段时间
            time.sleep(3)
        print(f"已经刷新{flush_times}次，依旧不能直接登录成功！")

        # 最后一次刷新后，判断是否还停留在登录页面。如果是，只能说明超时
        if scroll_status is False and str(browser.current_url).startswith(url.login_account):
            print(f"登录失败！在登录界面超时！url:{browser.current_url}")
            return False

        # 操作登录，可以尝试三次
        if _ocr_api:
            print("开始使用ocr机器识别验证码...")
            for _ in range(3):
                ret_url = _ocr_api.work()

                # 如果登录成功，跳出
                if url.login_success == ret_url:
                    return True

        return False

    @staticmethod
    def activity(browser: WebDriver, cookie=None):
        # 打开页面
        browser.get(url.activity_index)

        if cookie:
            browser.delete_all_cookies()
            page.re_add_cookie(browser, cookie)

        try:
            # 真实原因，即使下面wait可以找到“立即签到”，但由于是span标签，点击事件还没注册上去。固点击也没有用
            for _ in range(Final.timeout.s10):
                WebDriverWait(browser, Final.timeout.s10).until(
                    Exc.visibility_of_element_located((By.XPATH, "//li[@data-type='point']")),
                    message="寻找立即签到按钮，等待超时").click()
                print(f"\t第{_}次，尝试点击‘立即签到’按钮！")
                time.sleep(1)
                if str(browser.current_url).startswith(url.activity_jump_prefix):
                    break

            # 有可能在点击后，页面又跳到登录界面了。所以判断是否去到了“会员签到页面”
            WebDriverWait(browser, Final.timeout.s10).until(Exc.title_is('携程会员签到'), message="跳转会员签到页面失败！")
            return True

        except Exception as ex:
            print(traceback.format_exc())
            return False

    @staticmethod
    def re_add_cookie(browser: WebDriver, cookie):
        # 网页打开后，才能添加cookie
        for item in cookie.split(";"):
            name = item.split("=")[0].strip(" ")
            value = item.split("=")[1].strip(";")
            browser.add_cookie({"name": name, "value": value, "domain": ".ctrip.com"})


@singleton
class url(object):

    def __init__(self):
        pass

    @property
    def login_index(self):
        return str("https://accounts.ctrip.com/H5Login")

    @property
    def login_account(self):
        return str("https://accounts.ctrip.com/H5Login/login_ctrip")

    @property
    def login_success(self):
        return str('https://m.ctrip.com/webapp/myctrip/index')

    @property
    def activity_index(self):
        return str("https://m.ctrip.com/webapp/rewards/activity")

    @property
    def activity_jump_prefix(self):
        return str("https://m.ctrip.com/activitysetupapp/mkt/index")


url = url()
page = page()

if __name__ == "__main__":
    from info import crtip

    print(crtip.url.login_account)
