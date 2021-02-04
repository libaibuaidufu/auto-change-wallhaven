#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2021/2/4 13:54
@File    : bz_not_gui.py
@author  : dfkai
@Software: PyCharm
"""
import configparser
import ctypes
import os
import random
import time
import urllib

import requests
from bs4 import BeautifulSoup


class AutoChangeBZ():
    def __init__(self):
        # base_dir = os.getcwd()
        # self.config_path = os.path.join(base_dir, 'config.ini')
        self.config_path = 'config.ini'

    def change_bz(self, auto_change_bz, auto_change_time, auto_change_url):
        while True:
            try:
                if auto_change_bz == '是':
                    self.next_bz(auto_change_url)
                    time.sleep(int(auto_change_time))
                else:
                    break
            except Exception as e:
                print(e)
                print("更换失败，联系作者！")

    def next_bz(self, auto_change_url):
        base_url = 'https://w.wallhaven.cc/full/{src_type}/wallhaven-{src_name}'
        try:
            page = random.randrange(1, 15)
            random_page_url = auto_change_url + str(page)
            response = requests.get(random_page_url)
            soup: BeautifulSoup = BeautifulSoup(response.text, 'html.parser')
            div_tag = soup.find('section', class_='thumb-listing-page')
            li_list = div_tag.find_all('li')
            bz_num = random.randrange(0, len(li_list) - 1)
            li_tag = li_list[bz_num]
            image_tag = li_tag.find('img', class_='lazyload')
            image_type_check = li_tag.find("span", class_='png')
            src_url = image_tag['data-src']
            src_list = src_url.rsplit("/", 2)
            src_name = src_list[-1]
            src_type = src_list[-2]
            if image_type_check:
                src_name = src_name.rsplit(".", 1)[0] + '.png'
            src_num_url = base_url.format(src_type=src_type, src_name=src_name)
            print('更换壁纸中')
            try:
                opener = urllib.request.build_opener()  # 创建一个opener
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]  # 给这个opener设置header #'Mozilla/5.0'
                urllib.request.install_opener(opener)  # 安装这个opener的表头header,用于模拟浏览器.如果不模拟浏览器,下面的代码会404
                PATH = urllib.request.urlretrieve(src_num_url)[0]  # 获取处理图片地址
                ctypes.windll.user32.SystemParametersInfoW(20, 0, PATH, 3)  # 设置桌面
                print('壁纸更换完毕')
            except Exception as e:
                print(e)
                print(image_type_check)
                print(image_tag)
                print(src_url)
                print(random_page_url)
                print(src_num_url)
        except Exception as e:
            print(e)
            print("更换失败，联系作者！")

    def main(self):
        random_url = 'https://wallhaven.cc/search?sorting=random&ref=fp&seed=gLasU&page='
        if os.path.isfile(self.config_path):
            config_dict = configparser.ConfigParser()
            config_dict.read(self.config_path, encoding="utf8")
            auto_change_bz = config_dict.get("壁纸设置", '自动换壁纸')
            auto_change_time = config_dict.get("壁纸设置", '换壁纸时间')
            auto_change_url = config_dict.get('壁纸设置', '壁纸地址')
        else:
            auto_change_bz = '是'
            auto_change_time = 600
            auto_change_url = random_url
        self.change_bz(auto_change_bz, auto_change_time, auto_change_url)


if __name__ == '__main__':
    acbz = AutoChangeBZ()
    acbz.main()
