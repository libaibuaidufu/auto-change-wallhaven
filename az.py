#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2021/2/3 14:44
@File    : az.py
@author  : dfkai
@Software: PyCharm
"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2021/2/2 14:21
@File    : test.py
@author  : dfkai
@Software: PyCharm
"""
import asyncio
import configparser
import ctypes
import os
import random
import urllib
from tkinter import *

from PIL import Image, ImageTk
from aiohttp import ClientSession
from bs4 import BeautifulSoup


class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.geometry("1200x800")
        self.master.resizable(0, 0)
        self.master.title("壁纸")
        self.master.iconbitmap('钱袋.ico')  # 设置图标，仅支持.ico文件
        self.grid()
        self.place()
        base_dir = os.getcwd()
        self.config_path = os.path.join(base_dir, 'config.ini')

        self.auto_change_bz, self.auto_change_time, self.auto_change_url, self.auto_change_img = self.abc_main()
        if self.auto_change_img:
            img = Image.open(self.auto_change_img)
            self.img = ImageTk.PhotoImage(img)
        else:
            self.img = None

        self.loop = asyncio.get_event_loop()
        self.th_auto_change_bz = None
        self.th_next_bz = None
        self.th_listen_listen_bz_change = None
        self.is_run = False
        self.run()

    async def create_widgets(self):
        self.L1 = Label(self, text="壁纸地址：")
        self.L1.grid(row=0, column=0, sticky=W)

        self.E1 = Entry(self, bd=5, width=100)
        contents = StringVar()
        contents.set(self.auto_change_url)
        self.E1["textvariable"] = contents
        self.E1.grid(row=0, column=1, sticky=E)

        self.L2 = Label(self, text="是否自动更换：")
        self.L2.grid(row=0, column=2, sticky=W)
        self.E2 = Entry(self, bd=5, width=5)
        contents = StringVar()
        contents.set(self.auto_change_bz)
        self.E2["textvariable"] = contents
        self.E2.grid(row=0, column=3, sticky=E)

        self.L3 = Label(self, text="自动更换时间：")
        self.L3.grid(row=0, column=4, sticky=W)
        self.E3 = Entry(self, bd=5, width=5)
        contents = IntVar()
        contents.set(self.auto_change_time)
        self.E3["textvariable"] = contents
        self.E3.grid(row=0, column=5, sticky=E)

        self.B1 = Button(self, text="下一张壁纸", command=self.next_bz)
        self.B1.grid(row=0, column=6, sticky=W)
        self.B2 = Button(self, text="确定", command=self.get_config)
        self.B2.grid(row=0, column=7, sticky=W)

        self.l = Label(self.master, image=self.img, height=800, width=1200)
        self.l.place(x=1, y=30)

    def destroy(self):
        if self.th_auto_change_bz:
            self.th_auto_change_bz.cancel()
        if self.th_next_bz:
            self.th_next_bz.cancel()
        if self.th_listen_listen_bz_change:
            self.th_listen_listen_bz_change.cancel()
        super(Application, self).destroy()

    def run(self):
        return self.loop.run_until_complete(self.main())

    async def listen_bz_change(self):
        while True:
            try:
                item = await self.queue.get()
            except asyncio.queues.QueueEmpty:
                await asyncio.sleep(0.5)
                continue
            img = Image.open(item)
            image = ImageTk.PhotoImage(img)
            self.l.configure(image=image)
            self.queue.task_done()
        print("done done")

    def get_config(self):
        if self.is_run:
            self.th_auto_change_bz.cancel()
            self.is_run = False
        self.auto_change_bz = self.E2.get()
        self.auto_change_time = self.E3.get()
        self.auto_change_url = self.E1.get()
        if os.path.isfile(self.config_path):
            config_dict = configparser.ConfigParser()
            config_dict.read(self.config_path, encoding="utf8")
            config_dict.set("壁纸设置", '自动换壁纸', self.auto_change_bz)
            config_dict.set("壁纸设置", '换壁纸时间', self.auto_change_time)
            config_dict.set('壁纸设置', '壁纸地址', self.auto_change_url)
            with open(self.config_path, "w+", encoding="utf8") as f:
                config_dict.write(f)
        self.is_run = True
        print('get_config')
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run_abc_change_bz())

    async def run_abc_change_bz(self):
        try:
            if self.auto_change_bz == "是":
                while True:
                    try:
                        num = self.queue_run.get()
                    except asyncio.queues.QueueEmpty:
                        await asyncio.sleep(0.5)
                        continue
                    if num:
                        await self.abc_next_bz()
                        await asyncio.sleep(int(self.auto_change_time))
        except Exception as e:
            print(e)

    async def main(self):
        self.queue = asyncio.Queue()
        self.queue_run = asyncio.Queue()
        self.th_create_widgets = asyncio.ensure_future(self.create_widgets())
        self.th_listen_listen_bz_change = asyncio.ensure_future(self.listen_bz_change())

    def next_bz(self):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.abc_next_bz())

    async def abc_next_bz(self):
        random_header = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36",
        }
        base_url = 'https://w.wallhaven.cc/full/{src_type}/wallhaven-{src_name}'
        page = random.randrange(1, 15)
        random_page_url = self.auto_change_url + str(page)
        try:
            print('更换壁纸中')
            print(random_page_url)
            async with ClientSession() as session:
                print('1')
                async with session.get(random_page_url, headers=random_header) as response:
                    print('2')
                    response = await response.read()
                    print('3')
                    soup: BeautifulSoup = BeautifulSoup(response, 'html.parser')
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
                    try:
                        opener = urllib.request.build_opener()  # 创建一个opener
                        opener.addheaders = [('User-agent', 'Mozilla/5.0')]  # 给这个opener设置header
                        urllib.request.install_opener(opener)  # 安装这个opener的表头header,用于模拟浏览器.如果不模拟浏览器,下面的代码会404
                        PATH = urllib.request.urlretrieve(src_num_url)[0]  # 获取处理图片地址
                        ctypes.windll.user32.SystemParametersInfoW(20, 0, PATH, 3)  # 设置桌面
                        config_dict = configparser.ConfigParser()
                        config_dict.read(self.config_path, encoding="utf8")
                        config_dict.set("壁纸设置", '缓存地址', PATH)
                        with open(self.config_path, "w+", encoding="utf8") as f:
                            config_dict.write(f)
                        self.queue.put_nowait(PATH)
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
        finally:
            print("next_bz done")

    def abc_main(self):
        random_url = 'https://wallhaven.cc/search?q=id%3A65348&sorting=random&ref=fp&seed=gLasU&page='

        if os.path.isfile(self.config_path):
            config_dict = configparser.ConfigParser()
            config_dict.read(self.config_path, encoding="utf8")
            auto_change_bz = config_dict.get("壁纸设置", '自动换壁纸')
            auto_change_time = config_dict.get("壁纸设置", '换壁纸时间')
            auto_change_url = config_dict.get('壁纸设置', '壁纸地址')
            auto_change_img = config_dict.get('壁纸设置', '缓存地址')
        else:
            auto_change_bz = '是'
            auto_change_time = 600
            auto_change_url = random_url
            auto_change_img = None
        return auto_change_bz, auto_change_time, auto_change_url, auto_change_img


class Main:
    @classmethod
    def run(cls):
        root = Tk()
        app = Application(master=root)
        app.mainloop()


if __name__ == '__main__':
    Main.run()
