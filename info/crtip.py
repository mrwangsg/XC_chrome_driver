#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/9/28 20:19
# @Author  : sgwang
# @File    : crtip.py
# @Software: PyCharm
import re
import time
import traceback

from selenium.common.exceptions import MoveTargetOutOfBoundsException, TimeoutException, NoSuchElementException, \
    StaleElementReferenceException
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
    def re_add_cookie(browser: WebDriver, cookie):
        # 网页打开后，才能添加cookie
        for item in cookie.split(";"):
            name = item.split("=")[0].strip(" ")
            value = item.split("=")[1].strip(";")
            browser.add_cookie({"name": name, "value": value, "domain": ".ctrip.com"})

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
            ele_drop_btn = WebDriverWait(browser, Final.timeout.s10).until(
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
                print(f"\t第{_}次，尝试点击‘立即签到’按钮！")
                WebDriverWait(browser, Final.timeout.s10).until(
                    Exc.visibility_of_element_located((By.XPATH, "//li[@data-type='point']")),
                    message="寻找立即签到按钮，等待超时").click()
                time.sleep(1)

                if str(browser.current_url).startswith(url.activity_jump_prefix):
                    return True
                elif str(browser.current_url).startswith(url.login_index):
                    # 此时也有可能还没能正确登录，跳转到另外的页面，所以就会一直找不到按钮，超时
                    return False

            # 有可能在点击后，页面又跳到登录界面了。所以判断是否去到了“会员签到页面”
            print("跳转会员签到页面失败！")
            return False

        except Exception as ex:
            print(traceback.format_exc())
            return False

    @staticmethod
    def point_sign(browser: WebDriver) -> int:
        try:
            # 阻塞寻找元素。但找到了，点击事件还不一定加载完毕。所以用execute_script解决问题
            ele_mtsh_btn = WebDriverWait(browser, Final.timeout.s10).until(
                Exc.visibility_of_element_located((By.CLASS_NAME, "mtsh_btn")), message="寻找'签到'按钮，超时！")

            # 已经签过的，直接返回0积分
            ele_sub_span = ele_mtsh_btn.find_element(By.CSS_SELECTOR, "span")
            if ele_sub_span.text == "已签到":
                return int(0)

            ele_sub_btn = ele_mtsh_btn.find_element(By.CSS_SELECTOR, "div")
            browser.execute_script("arguments[0].click();", ele_sub_btn)

            # 点击之后，如果跳出弹窗。则说明成功
            ele_mtspi_num = WebDriverWait(browser, Final.timeout.s10).until(
                Exc.visibility_of_element_located((By.CLASS_NAME, "mtspi_num")), message="等待签到成功弹窗，超时！")

            print(f"签到成功！恭喜您获得{ele_mtspi_num.text}积分")
            return int(ele_mtspi_num.text)

        except NoSuchElementException:
            print("今天已经完成签到任务！")
            return int(0)

        except Exception:
            print(traceback.format_exc())
            return int(0)

    @staticmethod
    def point_scan(browser: WebDriver) -> int:
        try:
            # 总获得积分，任务初始页记录
            scan_point, scan_index_url = int(0), browser.current_url

            # 前期先收集任务
            scan_task_list = page.store_scan_tasks(browser)

            # 开始做子任务
            for _, task in enumerate(scan_task_list):
                print(f"\t浏览任务：{_}，{task['title']}")
                ret_point_num = page.do_scan_task(browser, scan_index_url, task)
                print(f"\t\t该任务获得积分：{ret_point_num}")
                scan_point += ret_point_num

            return scan_point
        except Exception:
            print(traceback.format_exc())
            return int(0)

    @staticmethod
    def store_scan_tasks(browser: WebDriver) -> list:
        scan_task_list = list()

        els_task_items = page.click_show_more(browser)
        for item in els_task_items:
            # 获取文本内容和按钮内容，匹配是否含有“浏览”和”逛逛“
            info_text = item['ele_title'].text
            desc_text = item['ele_desc'].get_attribute("textContent")
            btn_text = item['ele_button'].text
            point_num_str = item['ele_point'].text

            point_num = re.compile('\\d+').search(point_num_str).group()

            # 含有“浏览”和”逛逛“，并且不是已完成的。收集起来做任务
            total_text = str(info_text) + ", " + str(btn_text) + str(desc_text)
            if "浏览" in total_text or "逛逛" in total_text:
                if btn_text != "已完成":
                    scan_task_list.append({"title": info_text, "point": point_num})
        return scan_task_list

    @staticmethod
    def do_scan_task(browser: WebDriver, flush_index_url: str, task: dict) -> int:
        try:
            # 重新加载页面
            browser.get(flush_index_url)

            # 弹窗更多的任务列表，等待一下，让事件加载完毕
            els_task_items = page.click_show_more(browser)

            for item in els_task_items:
                info_text = item['ele_title'].text
                desc_text = item['ele_desc'].get_attribute("textContent")
                btn_text = item['ele_button'].text
                point_num_str = item['ele_point'].text

                point_num = re.compile('\\d+').search(point_num_str).group()
                if info_text == task['title'] or desc_text == task['title']:
                    # 点击按钮
                    item['ele_button'].click()

                    # 情况1，如果按钮是:”领奖励“，任务结束，返回积分数
                    if btn_text == "领奖励":
                        time.sleep(Final.timeout.s3)
                        return int(point_num)

                    else:
                        # 情况2，按要求浏览，分：2.1等待一定时间和2.2浏览即可
                        WebDriverWait(browser, Final.timeout.s10).until(
                            Exc.visibility_of_element_located((By.XPATH, "//body")))

                        # 再追加等待时间，防止因加载dom树，造成倒计时没有启动完全
                        time.sleep(Final.timeout.s3)

                        # 如果是要多等待一定使时间，再sleep一下
                        desc_seconds = re.compile('\\d+s').search(desc_text)
                        info_seconds = re.compile('\\d+s').search(info_text)
                        if desc_seconds:
                            wait_time = desc_seconds.group().replace("s", "")
                            time.sleep(int(wait_time))

                        elif info_seconds:
                            wait_time = info_seconds.group().replace("s", "")
                            time.sleep(int(wait_time))

                        # 浏览完毕，重新加载页面并点击
                        browser.get(flush_index_url)

                        # 弹窗更多的任务列表，等待一下，让事件加载完毕
                        inner_els_task_items = page.click_show_more(browser)
                        time.sleep(Final.timeout.s3)

                        for _inner_item in inner_els_task_items:
                            _info_text = _inner_item['ele_title'].text
                            _btn_text = _inner_item['ele_button'].text

                            if _info_text == task['title'] and _btn_text == "领奖励":
                                _inner_item['ele_button'].click()
                                time.sleep(Final.timeout.s3)
                                return int(point_num)
                        return int(0)

            return int(0)

        except:
            print(traceback.format_exc())
            return int(0)

    @staticmethod
    def click_show_more(browser: WebDriver) -> list:
        # 异步寻找元素。但找到了，点击事件还不一定加载完毕。所以用execute_script解决问题
        ele_show_more = WebDriverWait(browser, Final.timeout.s10).until(
            Exc.visibility_of_element_located((By.CLASS_NAME, "show_more")), message="寻找'查看更多'按钮，超时！")
        browser.execute_script("arguments[0].click();", ele_show_more)

        # 任务列表
        task_items_tag = "//div[@class='scroll-wrapper']/div/div/div[@class='task-wraper']/div[@class='task_item']"
        ele_task_items = WebDriverWait(browser, Final.timeout.s10).until(
            Exc.visibility_of_all_elements_located((By.XPATH, task_items_tag)), message="获取积分任务列表，超时！")

        ele_task_items_dict = list()
        for _ in ele_task_items:
            # todo 无法获取文本信息，可能是被隐藏的缘故
            try:
                ele_task_items_dict.append({
                    "ele_title": _.find_element(By.CSS_SELECTOR, "div.title"),
                    "ele_desc": _.find_element(By.CSS_SELECTOR, "div.desc-wrap > div"),
                    "ele_button": _.find_element(By.CSS_SELECTOR, "div.button"),
                    "ele_point": _.find_element(By.CSS_SELECTOR, "p.point"),
                })
            except StaleElementReferenceException as ex:
                ele_task_items_dict.append({
                    "ele_title": _.find_element(By.CSS_SELECTOR, "div.title"),
                    "ele_desc": _.find_element(By.CSS_SELECTOR, "div.desc-wrap > div"),
                    "ele_button": _.find_element(By.CSS_SELECTOR, "div.button"),
                    "ele_point": _.find_element(By.CSS_SELECTOR, "p.point"),
                })

        return ele_task_items_dict


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
