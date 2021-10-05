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
    global XC_cookie, XC_account, XC_password
    global BD_APP_ID, BD_API_KEY, BD_SECRET_KEY

    browser = None

    try:
        # 加载配置文件
        config = get_config()

        # 根据配置文件，初始化浏览器
        browser = get_browser(config)

        # 配置orc识别验证码
        _ocr_api = None
        if (BD_APP_ID is not None) and (BD_API_KEY is not None) and (BD_SECRET_KEY is not None):
            config['APP_ID'] = BD_APP_ID
            config['API_KEY'] = BD_API_KEY
            config['SECRET_KEY'] = BD_SECRET_KEY
            _ocr_api = ocrapi(browser, config)

        crtip.main(browser, XC_cookie, XC_account, XC_password, _ocr_api)


    except:
        print(traceback.format_exc())

    finally:
        # 关闭浏览器
        print("程序运行结束！！！")
        if browser:
            browser.close()
            browser.quit()

        # todo 这里堵塞是为了调试
        # time.sleep(1000)


if __name__ == '__main__':
    print_hi('PyCharm')

    # baidu-aip参数
    BD_APP_ID = os.environ['BD_APP_ID'] \
        if "BD_APP_ID" in os.environ and os.environ['BD_APP_ID'] != "" else None
    BD_API_KEY = os.environ['BD_API_KEY'] \
        if "BD_API_KEY" in os.environ and os.environ['BD_API_KEY'] != "" else None
    BD_SECRET_KEY = os.environ['BD_SECRET_KEY'] \
        if "BD_SECRET_KEY" in os.environ and os.environ['BD_SECRET_KEY'] != "" else None

    XC_account = os.environ['XC_account'] if "XC_account" in os.environ and os.environ['XC_account'] != "" else None
    XC_password = os.environ['XC_password'] if "XC_password" in os.environ and os.environ['XC_password'] != "" else None
    XC_cookie = os.environ['XC_cookie'] if "XC_cookie" in os.environ and os.environ['XC_cookie'] != "" else None

    if XC_cookie is None:
        print("携程Cookie不能为空！请配置：XC_cookie")
        sys.exit(-1)

    main()
    sys.exit(0)
