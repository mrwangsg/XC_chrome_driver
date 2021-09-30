#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import time
import traceback

from info import crtip
from ocr.baiduocr import ocrapi
from utils.config import get_config
from utils.selenium_browser import get_browser


def print_hi(name):
    print(f'Hi, {name}')


def main():
    global BD_APP_ID, BD_API_KEY, BD_SECRET_KEY
    global XC_account, XC_password, XC_cookie

    browser = None

    try:
        # 加载配置文件
        config = get_config()

        # 根据配置文件，初始化浏览器
        browser = get_browser(config)

        # 先来到活动页面，选择“立即签到”
        print("方法1，直接使用配置的Cookie登录...")
        sign_status = crtip.page.activity(browser, XC_cookie)

        if sign_status:
            print(f"立即签到点击，跳转成功！选择后，跳转页面链接：{browser.current_url}")

        elif (XC_account is not None) and (XC_password is not None):
            print("方法2，尝试使用账号和密码登录...")
            # 初始化orc工具
            _ocr_api = None
            if (BD_APP_ID is not None) and (BD_API_KEY is not None) and (BD_SECRET_KEY is not None):
                config['APP_ID'] = BD_APP_ID
                config['API_KEY'] = BD_API_KEY
                config['SECRET_KEY'] = BD_SECRET_KEY
                _ocr_api = ocrapi(browser, config)

            # 进入登录页面
            login_status = crtip.page.login(browser, XC_account, XC_password, _ocr_api)
            if login_status is False:
                print("使用账号和密码登录失败，退出程序！！！")
                return

            print(f"使用账号和密码登录成功！当前页面链接：{browser.current_url}")
            sign_status = crtip.page.activity(browser)
            if sign_status is False:
                print(f"立即签到点击，跳转失败！退出程序！！！")
                return

        # todo 点击“立即签到”，页面跳转后，第一件事就是签到

    except:
        print(traceback.format_exc())

    finally:
        print("程序运行结束！！！")

        # todo 这里堵塞是为了调试
        time.sleep(1000)

        # 关闭浏览器
        if browser:
            browser.close()
            browser.quit()


if __name__ == '__main__':
    print_hi('PyCharm')

    # baidu-aip参数
    BD_APP_ID = os.environ['BD_APP_ID'] if "BD_APP_ID" in os.environ else None
    BD_API_KEY = os.environ['BD_API_KEY'] if "BD_API_KEY" in os.environ else None
    BD_SECRET_KEY = os.environ['BD_SECRET_KEY'] if "BD_SECRET_KEY" in os.environ else None

    XC_account = os.environ['XC_account'] if "XC_account" in os.environ else None
    XC_password = os.environ['XC_password'] if "XC_password" in os.environ else None
    XC_cookie = os.environ['XC_cookie'] if "XC_cookie" in os.environ else None
    if XC_cookie is None:
        print("携程Cookie不能为空！请配置：XC_cookie")
        sys.exit(-1)

    main()
    sys.exit(0)