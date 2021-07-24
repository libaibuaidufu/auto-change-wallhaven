# -*- coding: utf-8 -*-
"""
@Date    : 2021/7/19
@Author  : libaibuaidufu
@Email   : libaibuaidufu@gmail.com
"""

import configparser
import copy
import ctypes
import json
import os
import pickle
import queue
import random
import tempfile
import threading
import time
import tkinter as tk
import traceback
from tkinter import messagebox, ttk
from urllib.parse import urlparse, parse_qs

import requests
import win32api
import win32con
import win32gui
import win32gui_struct
from PIL import Image, ImageTk
from bs4 import BeautifulSoup

config_path = 'config.ini'
gui_title = '壁纸'
gui_logo = 'icon.ico'


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(tk.sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.config_path = config_path
        self.master = master
        self.width = 1280
        self.height = 800
        sw = self.winfo_screenwidth()
        # 得到屏幕宽度
        sh = self.winfo_screenheight()
        # 得到屏幕高度
        ww = 1280
        wh = 800
        # 窗口宽高为100
        x = (sw - ww) / 2
        y = (sh - wh) / 2
        self.master.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
        # self.master.geometry("1280x800")
        self.master.resizable(0, 0)
        self.master.title(gui_title)
        self.master.iconbitmap(resource_path(gui_logo))  # 设置图标，仅支持.ico文件
        self.pack(fill=tk.BOTH)
        self.PATH, self.src_name = None, None

        self.t_id = 0  # 线程控制
        self.no_proxies = {
            'https': "",
            'http': ""
        }
        self.resolution = "1920x1080"
        self.url_dict = {"last_url": ""}
        self.page = 1
        self.auto_change_bz, self.auto_change_time, self.auto_change_url, self.auto_change_img, self.auto_change_page, self.auto_change_proxy, self.username, self.password, self.is_proxy = self.get_config()
        if self.auto_change_img:
            img = Image.open(self.auto_change_img)
            pil_image_resized = self.resize(self.width, self.height, img)  # 缩放图像让它保持比例，同时限制在一个矩形框范围内  【调用函数，返回整改后的图片】
            self.img = ImageTk.PhotoImage(pil_image_resized)  # 把PIL图像对象转变为Tkinter的PhotoImage对象  【转换格式，方便在窗口展示】
        else:
            self.img = None
        self.create_widgets()

        self.th_listen_listen_bz_change: threading.Thread = threading.Thread(target=self.listen_bz_change, args=(),
                                                                             daemon=True)
        self.th_listen_listen_bz_change.start()

        self.create_session(self.auto_change_proxy, self.is_proxy)

        if self.username and self.password:
            print('login')
            try:
                self.is_login(self.username, self.password)
            except requests.exceptions.SSLError and requests.exceptions.ConnectionError:
                self.set_proxy(self.auto_change_proxy, is_proxy="关闭")
                try:
                    self.is_login(self.username, self.password)
                except Exception:
                    print('login_fail')
            except Exception:
                print('login_fail')

        if self.auto_change_bz == "是":
            self.B5['text'] = "开启自动"
            self.button_auto_change()

    def create_widgets(self):
        # https://wallhaven.cc/latest
        # https://wallhaven.cc/hot
        # https://wallhaven.cc/toplist
        # https://wallhaven.cc/random
        # https://wallhaven.cc/untagged
        # https://wallhaven.cc/favorites
        self.L1 = tk.Label(self, text="自定义壁纸地址：")
        self.L1.pack(padx=5, pady=10, side=tk.LEFT)
        url_list = ["https://wallhaven.cc/latest", 'https://wallhaven.cc/hot', 'https://wallhaven.cc/toplist',
                    'https://wallhaven.cc/random', 'https://wallhaven.cc/untagged', "https://wallhaven.cc/favorites"]
        self.E1 = ttk.Combobox(self, width=65)
        self.E1["value"] = url_list
        self.E1.set(self.auto_change_url)
        self.E1.pack(padx=5, pady=10, side=tk.LEFT)
        self.B4 = tk.Button(self, text="确定", command=self.button_set_url_config)
        self.B4.pack(padx=5, pady=10, side=tk.LEFT)

        self.L3 = tk.Label(self, text="分辨率：")
        self.L3.pack(padx=5, pady=10, side=tk.LEFT)
        respicker_list = ['', '1600x900', '1920x1080', "2560x1440", '3840x2160']
        self.E3 = ttk.Combobox(self, width=10)
        self.E3["value"] = respicker_list
        self.E3.set(self.resolution)
        self.E3.pack(padx=5, pady=10, side=tk.LEFT)

        self.L2 = tk.Label(self, text="搜索词：")
        self.L2.pack(padx=5, pady=10, side=tk.LEFT)
        self.E2 = tk.Entry(self, bd=5, width=15)
        contents = tk.StringVar()
        self.E2["textvariable"] = contents
        self.E2.pack(padx=5, pady=10, side=tk.LEFT)
        self.B2 = tk.Button(self, text="搜索", command=self.button_search)
        self.B2.pack(padx=5, pady=10, side=tk.LEFT)

        self.B3 = tk.Button(self, text="保存壁纸", command=self.show_msg)
        self.B3.pack(padx=5, pady=10, side=tk.RIGHT)
        self.B1 = tk.Button(self, text="下一张", command=self.button_next_bz)
        self.B1.pack(padx=10, pady=10, side=tk.RIGHT)
        self.B5 = tk.Button(self, text="关闭自动" if self.auto_change_bz == '是' else "开启自动",
                            command=self.button_auto_change)
        self.B5.pack(padx=10, pady=10, side=tk.RIGHT)

        self.l = tk.Label(self.master, image=self.img, height=self.height, width=self.width)
        self.l.pack(padx=5, pady=10)

    def resize(self, w_box, h_box, pil_image):  # 参数是：要适应的窗口宽、高、Image.open后的图片
        w, h = pil_image.size  # 获取图像的原始大小
        f1 = 1.0 * w_box / w
        f2 = 1.0 * h_box / h
        factor = min([f1, f2])
        width = int(w * factor)
        height = int(h * factor)
        return pil_image.resize((width, height), Image.ANTIALIAS)

    def listen_bz_change(self):
        while True:
            item = q.get()
            if item is None:
                break
            path_dict = json.loads(item)
            self.auto_change_img = path_dict['path']
            print(self.auto_change_img)
            self.src_name = path_dict['src_name']
            img = Image.open(self.auto_change_img)
            pil_image_resized = self.resize(self.width, self.height, img)  # 缩放图像让它保持比例，同时限制在一个矩形框范围内  【调用函数，返回整改后的图片】
            tk_image = ImageTk.PhotoImage(pil_image_resized)  # 把PIL图像对象转变为Tkinter的PhotoImage对象  【转换格式，方便在窗口展示】
            self.l.configure(image=tk_image)

    def get_config(self):
        random_url = 'https://wallhaven.cc/toplist?page='
        if os.path.isfile(self.config_path):
            config_dict = configparser.ConfigParser()
            config_dict.read(self.config_path, encoding="utf8")
            auto_change_bz = config_dict.get("壁纸设置", '自动换壁纸')
            auto_change_time = config_dict.get("壁纸设置", '换壁纸时间')
            auto_change_url = config_dict.get('壁纸设置', '壁纸地址')
            auto_change_img = config_dict.get('壁纸设置', '缓存地址')
            auto_change_page = config_dict.get('壁纸设置', '壁纸页数')
            auto_change_proxy = config_dict.get('壁纸设置', '代理地址')
            username = config_dict.get('壁纸设置', '用户名')
            password = config_dict.get('壁纸设置', '密码')
            is_proxy = config_dict.get('壁纸设置', '是否启用代理')
        else:
            auto_change_bz = '否'
            auto_change_time = '600'
            auto_change_url = random_url
            auto_change_img = None
            auto_change_page = '15'
            auto_change_proxy = ''
            username = ''
            password = ''
            is_proxy = "关闭"
            with open(self.config_path, 'w', encoding='utf8') as f:
                f.write('[壁纸设置]\n')
                f.write(f'自动换壁纸 = {auto_change_bz}\n')
                f.write(f'换壁纸时间 = {auto_change_time}\n')
                f.write(f'壁纸地址 = {auto_change_url}\n')
                f.write(f'壁纸页数 = {auto_change_page}\n')
                f.write('代理地址 =\n')
                f.write('缓存地址 =\n')
                f.write('用户名 =\n')
                f.write('密码 =\n')
                f.write(f'是否启用代理 = {is_proxy}')

        return auto_change_bz, auto_change_time, auto_change_url, auto_change_img, auto_change_page, auto_change_proxy, username, password, is_proxy

    def button_auto_change(self):
        if self.B5['text'] == "开启自动":
            print('开启自动')
            self.B5['text'] = "关闭自动"
            self.t_id += 1
            self.auto_change_bz = "是"

            self.th_auto_change_bz = threading.Thread(target=self.change_bz,
                                                      args=(
                                                          self.t_id, self.auto_change_time,
                                                          self.auto_change_url, self.auto_change_page),
                                                      daemon=True)
            self.th_auto_change_bz.start()
        else:
            print('关闭自动')
            self.B5['text'] = "开启自动"
            self.t_id += 1
            self.auto_change_bz = "否"

            self.B5.text = "开启自动"

    def button_next_bz(self):
        self.th_next_bz = threading.Thread(target=self.next_bz,
                                           args=(self.auto_change_url, self.auto_change_page),
                                           daemon=True)
        self.th_next_bz.start()

    def button_search(self):
        self.search_key = self.E2.get()
        self.resolution = self.E3.get()
        print(self.search_key)
        print(self.resolution)
        if self.search_key or self.resolution:

            url = urlparse(self.auto_change_url)
            if url.path:
                url_type = url.path.split("/")[-1]
                if url_type == "search":
                    url_query_dict = parse_qs(url.query)
                    if 'sorting' in url_query_dict:
                        url_type = url_query_dict["sorting"][0]
                    else:
                        url_type = "random"
            else:
                url_type = "random"
            if self.search_key:
                self.auto_change_url = f"https://wallhaven.cc/search?q={self.search_key}&purity=100&sorting={url_type}&order=desc"
            else:
                self.auto_change_url = f"https://wallhaven.cc/search?purity=100&sorting={url_type}&order=desc"
            print(self.auto_change_url)
            self.E1.set(self.auto_change_url)
            self.button_next_bz()
            if self.auto_change_bz == "是":
                self.B5['text'] = '开启自动'
                self.button_auto_change()

    def button_set_url_config(self):
        self.auto_change_url = self.E1.get()
        url = urlparse(self.auto_change_url)
        if "wallhaven.cc" != url.netloc:
            messagebox.showerror('错误', "请勿放无关网址")
            return

        self.button_next_bz()
        if self.auto_change_bz == "是":
            self.B5['text'] = '开启自动'
            self.button_auto_change()

    def show_msg(self):
        if not self.PATH or not self.src_name:
            messagebox.showinfo('信息', '无法保存，谁让你上一次不保存呢！')
            return
        if not os.path.exists('save'):
            os.mkdir('save')
        with open(self.PATH, 'rb') as f:
            with open('save/' + self.src_name, 'wb') as fd:
                fd.write(f.read())
        messagebox.showinfo('信息', '保存成功！')

    def destroy(self):
        super(Application, self).destroy()

    def create_session(self, auto_change_proxy, is_proxy="关闭"):
        headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        }
        self.session = requests.Session()
        self.session.headers = headers
        self.session.trust_env = False
        self.set_proxy(auto_change_proxy, is_proxy)
        return self.session

    # 登录
    def is_login(self, username, password, is_use_cookie=True):
        index_url = 'https://wallhaven.cc/'
        login_url = 'https://wallhaven.cc/login'
        auth_login_url = 'https://wallhaven.cc/auth/login'
        payload = {
            '_token': (None, ''),
            'username': (None, username),
            'password': (None, password)
        }
        if is_use_cookie:
            if os.path.exists('cookies.txt'):
                with open('cookies.txt', 'rb') as f:
                    self.session.cookies.update(pickle.load(f))
                check_response = self.session.get(index_url)
                if username in check_response.text:
                    self.master.title(gui_title + f"-{username}")
                    print('use cookies')
                    return
        login_response = self.session.get(login_url)
        bf = BeautifulSoup(login_response.text, 'html.parser')
        hidden = bf.find_all('input', {'type': 'hidden'})
        for i in hidden:
            _token = i['value']
            payload['_token'] = _token

        check_response = self.session.post(auth_login_url, data=payload)
        print(check_response.url)
        if check_response.url in (f"https://wallhaven.cc/user/{username}", 'https://wallhaven.cc'):
            with open('cookies.txt', 'wb') as f:
                pickle.dump(self.session.cookies, f)
            self.master.title(gui_title + f"-{username}")
        else:
            self.clear_username_password()
            messagebox.showinfo('登录错误', '用户名或者密码错误，请重新设置！')
        return

    def clear_username_password(self):
        self.username = ""
        self.password = ""

    def set_proxy(self, auto_change_proxy, is_proxy):
        if is_proxy == "开启":
            print('开启代理')
            proxies = {
                'https': auto_change_proxy,
                'http': auto_change_proxy
            }
        else:
            print('关闭代理')
            proxies = self.no_proxies
        print(proxies)
        self.session.proxies.update(proxies)

    def change_bz(self, t_id, auto_change_time, auto_change_url, auto_change_page):
        while True:
            try:
                time.sleep(int(auto_change_time))
                if t_id != self.t_id:
                    break
                self.next_bz(auto_change_url, auto_change_page)
            except Exception as e:
                print('1', e)
                messagebox.showerror('错误', '请重新启动！')
                break

    # 手动切换壁纸
    def next_bz(self, auto_change_url, auto_change_page=15):
        print('切换图片')
        base_download_url = 'https://w.wallhaven.cc/full/{src_type}/wallhaven-{src_name}'
        try:
            url_data = urlparse(auto_change_url)
            base_url = f"{url_data.scheme}://{url_data.netloc}{url_data.path}?"

            url_query_dict = parse_qs(url_data.query)
            url_query = f""
            for key, value in url_query_dict.items():
                if key == "page":
                    continue
                url_query += f"{key}={value[0]}&"
            if self.resolution:
                url_query += f'atleast={self.resolution}&'

            set_url_in_dict = base_url + url_query
            print(self.url_dict.keys())
            print(set_url_in_dict)
            if set_url_in_dict not in self.url_dict.keys():
                self.url_dict[set_url_in_dict] = {"max_page": 0}
            if set_url_in_dict == self.url_dict['last_url']:
                if self.page < int(auto_change_page):
                    self.page += 1
                else:
                    self.page = 1
            else:
                self.page = 1
            print(self.page)
            max_page = self.url_dict[set_url_in_dict]['max_page']
            if max_page and max_page < self.page:
                self.page = 1
            print(self.page)
            url_query += f"page={self.page}"
            random_page_url = base_url + url_query
            print(random_page_url)
            li_url_list = []
            if set_url_in_dict in self.url_dict.keys() and self.page in self.url_dict[set_url_in_dict].keys():
                li_url_list = self.url_dict[set_url_in_dict][self.page]
            if not li_url_list:
                print('re_url')
                self.url_dict['last_url'] = set_url_in_dict
                response = self.session.get(random_page_url)
                soup: BeautifulSoup = BeautifulSoup(response.text, 'html.parser')
                if "Forgot password" in soup.text:
                    messagebox.showerror('错误', "请登录后在访问需要登录的页面")
                    return
                div_tag = soup.find('section', class_='thumb-listing-page')
                if div_tag:
                    li_list = div_tag.find_all('li')
                    if not li_list:
                        if self.page == 1:
                            messagebox.showinfo("提示", "没有相关内容")
                        else:
                            self.url_dict[set_url_in_dict]["max_page"] = self.page - 1
                            self.url_dict['last_url'] = ""
                            self.next_bz(auto_change_url, auto_change_page)
                        return
                    for li_tag in li_list:
                        image_tag = li_tag.find('img', class_='lazyload')
                        image_type_check = li_tag.find("span", class_='png')
                        src_url = image_tag['data-src']
                        src_list = src_url.rsplit("/", 2)
                        src_name = src_list[-1]
                        src_type = src_list[-2]
                        if image_type_check:
                            src_name = src_name.rsplit(".", 1)[0] + '.png'
                        src_num_url = base_download_url.format(src_type=src_type, src_name=src_name)
                        li_url_list.append(src_num_url)
                        print(li_url_list)
                    self.url_dict[set_url_in_dict][self.page] = li_url_list
                else:
                    messagebox.showerror('错误', "请勿放无关网址")
                    return
            bz_num = random.randrange(0, len(li_url_list) - 1)
            print(len(li_url_list),bz_num)
            src_num_url = li_url_list[bz_num]
            src_name = src_num_url.rsplit('-')[-1]
            print(src_num_url)
        except Exception:
            traceback.print_exc()
            messagebox.showerror('错误', "请查看是否壁纸地址有问题！")
            return
        print('更换壁纸中')
        try:
            img_type = src_num_url.rsplit('.')[-1]
            resp = self.session.get(src_num_url)
            tfp = tempfile.NamedTemporaryFile(suffix='.' + img_type, delete=False)
            with tfp:
                tfp.write(resp.content)
            PATH = tfp.name
            print(PATH)
            ctypes.windll.user32.SystemParametersInfoW(20, 0, PATH, 3)  # 设置桌面
            print('壁纸更换完毕')
            q.put(json.dumps({'path': PATH, 'src_name': src_name}))
        except Exception:
            traceback.print_exc()
            messagebox.showerror('错误', "设置壁纸失败，那里出问题了我也不知道！可能是切换太频繁被限制了，等一会就好了。也可能是代理问题。")


class PanConfigWindow(tk.Toplevel):
    def __init__(self, app, config_dict):
        super().__init__()
        self.iconbitmap(resource_path(gui_logo))  # 设置图标，仅支持.ico文件
        self.title("设置")
        sw = self.winfo_screenwidth()
        # 得到屏幕宽度
        sh = self.winfo_screenheight()
        # 得到屏幕高度
        ww = 400
        wh = 200
        # 窗口宽高为100
        x = (sw - ww) / 2
        y = (sh - wh) / 2
        self.geometry("%dx%d+%d+%d" % (ww, wh, x, y))
        # self.geometry("500x400")
        self.row_num = 1
        self.base_config_dict = config_dict
        self.config_dict = copy.deepcopy(config_dict)
        self._app = app
        self.last_m = None
        self.set_ui_o()

    def set_ui_o(self):
        row_b = tk.Frame(self, width=200, height=35)
        row_b.grid(row=0, column=0, padx=10, pady=10)

        b_c = [("设置", self.b1_cmd), ("用户", self.b2_cmd), ("代理", self.b3_cmd)]
        for index, bc in enumerate(b_c):
            b, c = bc
            bv = tk.Button(row_b, text=b, command=c)
            bv.grid(row=index, column=0, pady=3)

        self.b1_cmd()

        row_q = tk.Frame(self, bg='green', width=200, height=35)
        row_q.grid(row=1, column=1)
        tk.Button(row_q, text="取消", command=self.cancel).pack(side=tk.RIGHT)
        tk.Button(row_q, text="确定", command=self.ok).pack(side=tk.RIGHT)

    def grid_ui_config(self, row_c):
        padx, pady = 5, 5

        # l1 = tk.Label(row_c, text='自动切换壁纸：', width=15)
        # l1.grid(row=0, column=0, pady=pady, padx=padx)
        # self.auto_change_config = ttk.Combobox(row_c, width=2)  # 初始化
        # is_auto_change = ("是", "否")
        # self.auto_change_config["value"] = is_auto_change
        # self.auto_change_config.current(is_auto_change.index(self._app.auto_change_bz))
        # self.auto_change_config.grid(row=0, column=1, pady=pady, padx=padx)

        l2 = tk.Label(row_c, text='壁纸切换间隔 ：', width=15)
        l2.grid(row=1, column=0, pady=pady, padx=padx)
        self.auto_change_time_config = tk.IntVar()
        self.auto_change_time_config.set(self._app.auto_change_time)
        e2 = tk.Entry(row_c, textvariable=self.auto_change_time_config, width=20)
        e2.grid(row=1, column=1, pady=pady, padx=padx)

        l3 = tk.Label(row_c, text='壁纸页数 ：', width=15)
        l3.grid(row=2, column=0, pady=pady, padx=padx)
        self.auto_change_page_config = tk.IntVar()
        self.auto_change_page_config.set(self._app.auto_change_page)
        e3 = tk.Entry(row_c, textvariable=self.auto_change_page_config, width=8)
        e3.grid(row=2, column=1, pady=pady, padx=padx)

    def grid_user_config(self, row_c):
        padx, pady = 5, 5

        l1 = tk.Label(row_c, text='用户名：', width=15)
        l1.grid(row=0, column=0, pady=pady, padx=padx)
        self.username = tk.StringVar()
        self.username.set(self._app.username)
        e1 = tk.Entry(row_c, textvariable=self.username, width=20)
        e1.grid(row=0, column=1, pady=pady, padx=padx)

        # 第二行
        l2 = tk.Label(row_c, text='密码：', width=15)
        l2.grid(row=1, column=0, pady=pady, padx=padx)
        self.password = tk.StringVar()
        self.password.set(self._app.password)
        e2 = tk.Entry(row_c, textvariable=self.password, width=20)
        e2.grid(row=1, column=1, pady=pady, padx=padx)

    def grid_proxy_config(self, row_c):
        padx, pady = 5, 5
        l1 = tk.Label(row_c, text='协议 ：', width=15)
        l1.grid(row=0, column=0, pady=pady, padx=padx)
        self.is_http_config = ttk.Combobox(row_c, width=20)  # 初始化
        is_http = ("", "https", "http")
        self.is_http_config["value"] = is_http
        self.is_http_config.current(is_http.index(self.config_dict['is_http']))
        self.is_http_config.grid(row=0, column=1, pady=pady, padx=padx)

        l2 = tk.Label(row_c, text='host ：', width=15)
        l2.grid(row=1, column=0, pady=pady, padx=padx)
        self.host = tk.StringVar()
        self.host.set(self.config_dict['host'])
        e2 = tk.Entry(row_c, textvariable=self.host, width=20)
        e2.grid(row=1, column=1, pady=pady, padx=padx)

        l3 = tk.Label(row_c, text='端口 ：', width=15)
        l3.grid(row=2, column=0, pady=pady, padx=padx)
        self.port = tk.StringVar()
        self.port.set(self.config_dict['port'])
        e3 = tk.Entry(row_c, textvariable=self.port, width=20)
        e3.grid(row=2, column=1, pady=pady, padx=padx)

        l3 = tk.Label(row_c, text='启用代理 ：', width=15)
        l3.grid(row=3, column=0, pady=pady, padx=padx)
        self.is_proxy_config = ttk.Combobox(row_c, width=20)  # 初始化
        is_proxy = ("开启", "关闭")
        self.is_proxy_config["value"] = is_proxy
        self.is_proxy_config.current(is_proxy.index(self.config_dict['is_proxy']))
        self.is_proxy_config.grid(row=3, column=1, pady=pady, padx=padx)

    def b1_cmd(self):
        if self.last_m:
            self.change_value()
            self.last_m.destroy()
        row_c = tk.Frame(self, width=200, height=35)
        row_c.grid(row=0, column=1, pady=10)
        self.grid_ui_config(row_c)
        self.last_m = row_c
        self.row_num = 1

    def b2_cmd(self):
        if self.last_m:
            self.change_value()
            self.last_m.destroy()
        row_c = tk.Frame(self, width=200, height=35)
        row_c.grid(row=0, column=1)
        self.grid_user_config(row_c)
        self.last_m = row_c
        self.row_num = 2

    def b3_cmd(self):
        if self.last_m:
            self.change_value()
            self.last_m.destroy()
        row_c = tk.Frame(self, width=200, height=35)
        row_c.grid(row=0, column=1)
        self.grid_proxy_config(row_c)
        self.last_m = row_c
        self.row_num = 3

    def change_value(self):
        if self.row_num == 1:
            # self.config_dict['bz'] = self.auto_change_config.get()
            self.config_dict['time'] = str(self.auto_change_time_config.get())
            self.config_dict['page'] = str(self.auto_change_page_config.get())
        elif self.row_num == 2:
            self.config_dict['username'] = self.username.get()
            self.config_dict['password'] = self.password.get()
        elif self.row_num == 3:
            self.config_dict['is_http'] = self.is_http_config.get()
            self.config_dict['host'] = self.host.get()
            self.config_dict['port'] = self.port.get()
            self.config_dict['is_proxy'] = self.is_proxy_config.get()

    def ok(self):
        self.change_value()
        self.destroy()  # 销毁窗口

    def cancel(self):
        self.config_dict = self.base_config_dict  # 空！
        self.destroy()


# 最小化
class SysTrayIcon(object):
    '''SysTrayIcon类用于显示任务栏图标'''
    QUIT = 'QUIT'
    SPECIAL_ACTIONS = [QUIT]
    FIRST_ID = 5320

    def __init__(s, icon, hover_text, menu_options, on_quit, tk_window=None, default_menu_index=None,
                 window_class_name=None, app=None):
        '''
        icon         需要显示的图标文件路径
        hover_text   鼠标停留在图标上方时显示的文字
        menu_options 右键菜单，格式: (('a', None, callback), ('b', None, (('b1', None, callback),)))
        on_quit      传递退出函数，在执行退出时一并运行
        tk_window    传递Tk窗口，s.root，用于单击图标显示窗口
        default_menu_index 不显示的右键菜单序号
        window_class_name  窗口类名
        '''
        s.icon = icon
        s.hover_text = hover_text
        s.on_quit = on_quit
        s.root = tk_window
        s.app = app
        s.show_config = False

        menu_options = menu_options + (('退出', None, s.QUIT),)
        s._next_action_id = s.FIRST_ID
        s.menu_actions_by_id = set()
        s.menu_options = s._add_ids_to_menu_options(list(menu_options))
        s.menu_actions_by_id = dict(s.menu_actions_by_id)
        del s._next_action_id

        s.default_menu_index = (default_menu_index or 0)
        s.window_class_name = window_class_name or "SysTrayIconPy"

        message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): s.restart,
                       win32con.WM_DESTROY: s.destroy,
                       win32con.WM_COMMAND: s.command,
                       win32con.WM_USER + 20: s.notify, }
        # 注册窗口类。
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32gui.GetModuleHandle(None)
        wc.lpszClassName = s.window_class_name
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map  # 也可以指定wndproc.
        s.classAtom = win32gui.RegisterClass(wc)

    def activation(s):
        '''激活任务栏图标，不用每次都重新创建新的托盘图标'''
        hinst = win32gui.GetModuleHandle(None)  # 创建窗口。
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        s.hwnd = win32gui.CreateWindow(s.classAtom,
                                       s.window_class_name,
                                       style,
                                       0, 0,
                                       win32con.CW_USEDEFAULT,
                                       win32con.CW_USEDEFAULT,
                                       0, 0, hinst, None)
        win32gui.UpdateWindow(s.hwnd)
        s.notify_id = None
        # 提示没有什么用 烦人
        # s.refresh(title='壁纸软件已后台！', msg='点击重新打开', time=500)
        s.refresh()

        win32gui.PumpMessages()

    def refresh(s, title='', msg='', time=500):
        '''刷新托盘图标
           title 标题
           msg   内容，为空的话就不显示提示
           time  提示显示时间'''
        hinst = win32gui.GetModuleHandle(None)
        if os.path.isfile(s.icon):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst, s.icon, win32con.IMAGE_ICON,
                                       0, 0, icon_flags)
        else:  # 找不到图标文件 - 使用默认值
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        if s.notify_id:
            message = win32gui.NIM_MODIFY
        else:
            message = win32gui.NIM_ADD

        s.notify_id = (s.hwnd, 0,  # 句柄、托盘图标ID
                       win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP | win32gui.NIF_INFO,
                       # 托盘图标可以使用的功能的标识
                       win32con.WM_USER + 20, hicon, s.hover_text,  # 回调消息ID、托盘图标句柄、图标字符串
                       msg, time, title,  # 提示内容、提示显示时间、提示标题
                       win32gui.NIIF_INFO  # 提示用到的图标
                       )
        win32gui.Shell_NotifyIcon(message, s.notify_id)

    def show_menu(s):
        '''显示右键菜单'''
        menu = win32gui.CreatePopupMenu()
        s.create_menu(menu, s.menu_options)

        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(s.hwnd)
        win32gui.TrackPopupMenu(menu,
                                win32con.TPM_LEFTALIGN,
                                pos[0],
                                pos[1],
                                0,
                                s.hwnd,
                                None)
        win32gui.PostMessage(s.hwnd, win32con.WM_NULL, 0, 0)

    def _add_ids_to_menu_options(s, menu_options):
        result = []
        for menu_option in menu_options:
            option_text, option_icon, option_action = menu_option
            if callable(option_action) or option_action in s.SPECIAL_ACTIONS:
                s.menu_actions_by_id.add((s._next_action_id, option_action))
                result.append(menu_option + (s._next_action_id,))
            else:
                result.append((option_text,
                               option_icon,
                               s._add_ids_to_menu_options(option_action),
                               s._next_action_id))
            s._next_action_id += 1
        return result

    def restart(s, hwnd, msg, wparam, lparam):
        s.refresh()

    def destroy(s, hwnd=None, msg=None, wparam=None, lparam=None, exit=1):
        print('退出了')
        if os.path.isfile(s.app.config_path):
            print(s.app.auto_change_url)
            print(s.app.auto_change_bz)
            print(s.app.auto_change_time)
            print(s.app.auto_change_page)
            print(s.app.auto_change_img)
            print(s.app.auto_change_proxy)
            print(s.app.username)
            print(s.app.password)
            print(s.app.is_proxy)
            config_dict = configparser.ConfigParser()
            config_dict.read(s.app.config_path, encoding="utf8")
            config_dict.set("壁纸设置", '自动换壁纸', s.app.auto_change_bz)
            config_dict.set("壁纸设置", '换壁纸时间', str(s.app.auto_change_time))
            config_dict.set("壁纸设置", '壁纸地址', s.app.auto_change_url)
            config_dict.set('壁纸设置', '壁纸页数', str(s.app.auto_change_page))
            config_dict.set('壁纸设置', '缓存地址', s.app.auto_change_img)
            config_dict.set('壁纸设置', '代理地址', s.app.auto_change_proxy)
            config_dict.set('壁纸设置', '用户名', s.app.username)
            config_dict.set('壁纸设置', '密码', s.app.password)
            config_dict.set('壁纸设置', '是否启用代理', s.app.is_proxy)
            with open(s.app.config_path, "w+", encoding="utf8") as f:
                config_dict.write(f)
        nid = (s.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)  # 终止应用程序。
        if exit and s.on_quit:
            s.on_quit()  # 需要传递自身过去时用 s.on_quit(s)
        else:
            s.root.deiconify()  # 显示tk窗口

    def notify(s, hwnd, msg, wparam, lparam):
        '''鼠标事件'''
        # if lparam == win32con.WM_LBUTTONDBLCLK:  # 双击左键
        #     pass
        if lparam == win32con.WM_RBUTTONUP:  # 右键弹起
            s.show_menu()
        elif lparam == win32con.WM_LBUTTONUP:  # 左键弹起
            if not s.show_config:
                s.destroy(exit=0)
            else:
                return False
        return True
        """
        可能的鼠标事件：
          WM_MOUSEMOVE      #光标经过图标
          WM_LBUTTONDOWN    #左键按下
          WM_LBUTTONUP      #左键弹起
          WM_LBUTTONDBLCLK  #双击左键
          WM_RBUTTONDOWN    #右键按下
          WM_RBUTTONUP      #右键弹起
          WM_RBUTTONDBLCLK  #双击右键
          WM_MBUTTONDOWN    #滚轮按下
          WM_MBUTTONUP      #滚轮弹起
          WM_MBUTTONDBLCLK  #双击滚轮
        """

    def create_menu(s, menu, menu_options):
        for option_text, option_icon, option_action, option_id in menu_options[::-1]:
            if option_icon:
                option_icon = s.prep_menu_icon(option_icon)

            if option_id in s.menu_actions_by_id:
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                wID=option_id)
                win32gui.InsertMenuItem(menu, 0, 1, item)
            else:
                submenu = win32gui.CreatePopupMenu()
                s.create_menu(submenu, option_action)
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                hSubMenu=submenu)
                win32gui.InsertMenuItem(menu, 0, 1, item)

    def prep_menu_icon(s, icon):
        # 加载图标。
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
        hicon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

        hdcBitmap = win32gui.CreateCompatibleDC(0)
        hdcScreen = win32gui.GetDC(0)
        hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
        hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
        brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
        win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
        win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
        win32gui.SelectObject(hdcBitmap, hbmOld)
        win32gui.DeleteDC(hdcBitmap)

        return hbm

    def command(s, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        s.execute_menu_option(id)

    def execute_menu_option(s, id):
        menu_action = s.menu_actions_by_id[id]
        if menu_action == s.QUIT:
            win32gui.DestroyWindow(s.hwnd)
        else:
            menu_action(s)


# 主程序
class _Main:  # 调用SysTrayIcon的Demo窗口
    def __init__(s):
        s.SysTrayIcon = None  # 判断是否打开系统托盘图标

    def main(s):
        # tk窗口
        s.root = tk.Tk()
        s.app = Application(master=s.root)
        # iconify 最小化 normal 正常 zoom 最大化
        # s.root.bind("<Unmap>",lambda event: s.Hidden_window() if s.root.state() == 'iconic' else False)  # 窗口最小化判断，可以说是调用最重要的一步
        # s.root.protocol('WM_DELETE_WINDOW', s.exit)  # 点击Tk窗口关闭时直接调用s.exit，不使用默认关闭
        s.root.protocol('WM_DELETE_WINDOW', s.Hidden_window)  # 点击Tk窗口关闭时,设置最小化

        s.root.mainloop()

    def Hidden_window(s, icon=resource_path(gui_logo), hover_text="壁纸"):
        '''隐藏窗口至托盘区，调用SysTrayIcon的重要函数'''

        # 托盘图标右键菜单, 格式: ('name', None, callback),下面也是二级菜单的例子
        # 24行有自动添加‘退出’，不需要的可删除
        if s.app.is_proxy == "关闭":
            close_text = "关闭√"
            open_text = "开启"
        else:
            close_text = "关闭"
            open_text = "开启√"

        menu_options = (
            ('切换壁纸', None, s.handle_change_bz),
            ('设置', None, s.handle_set_config),
            ('代理', None, ((open_text, None, s.handle_proxy_open), (close_text, None, s.handle_proxy_close)))
        )
        # ('二级 菜单', None, (('更改 图标', None, s.switch_icon),)))
        # menu_options = ()
        s.root.withdraw()  # 隐藏tk窗口
        if not s.SysTrayIcon: s.SysTrayIcon = SysTrayIcon(
            icon,  # 图标
            hover_text,  # 光标停留显示文字
            menu_options,  # 右键菜单
            on_quit=s.exit,  # 退出调用
            tk_window=s.root,  # Tk窗口
            app=s.app
        )
        s.SysTrayIcon.activation()

    def exit(s, _sysTrayIcon=None):
        s.root.destroy()

    def show_msg(s, title='壁纸', msg='喔喔喔喔', time=500):
        s.SysTrayIcon.refresh(title=title, msg=msg, time=time)

    def switch_icon(s, _sysTrayIcon, icon=resource_path(gui_logo)):
        # 点击右键菜单项目会传递SysTrayIcon自身给引用的函数，所以这里的_sysTrayIcon = s.sysTrayIcon
        # 只是一个改图标的例子，不需要的可以删除此函数
        _sysTrayIcon.icon = icon
        _sysTrayIcon.refresh()

        # 气泡提示的例子
        s.show_msg(title='图标更换', msg='图标更换成功！', time=500)

    def change_menu(s, _sysTrayIcon):
        if s.app.is_proxy == "关闭":
            close_text = "关闭√"
            open_text = "开启"
        else:
            close_text = "关闭"
            open_text = "开启√"

        menu_options = (
            ('切换壁纸', None, s.handle_change_bz),
            ('设置', None, s.handle_set_config),
            ('代理', None, ((open_text, None, s.handle_proxy_open), (close_text, None, s.handle_proxy_close)))
        )

        menu_options = menu_options + (('退出', None, _sysTrayIcon.QUIT),)
        _sysTrayIcon._next_action_id = _sysTrayIcon.FIRST_ID
        _sysTrayIcon.menu_actions_by_id = set()
        _sysTrayIcon.menu_options = _sysTrayIcon._add_ids_to_menu_options(menu_options)
        _sysTrayIcon.menu_actions_by_id = dict(_sysTrayIcon.menu_actions_by_id)
        s.app.set_proxy(s.app.auto_change_proxy, s.app.is_proxy)

    def handle_proxy_open(s, _sysTrayIcon):
        s.app.is_proxy = "开启"
        s.change_menu(_sysTrayIcon)

    def handle_proxy_close(s, _sysTrayIcon):
        s.app.is_proxy = "关闭"
        s.change_menu(_sysTrayIcon)

    def handle_change_bz(s, _sysTrayIcon):
        s.app.button_next_bz()

    def handle_set_config(s, _sysTrayIcon):
        base_config_dict = {
            "bz": s.app.auto_change_bz,
            "time": s.app.auto_change_time,
            "page": s.app.auto_change_page,
            "username": s.app.username,
            "password": s.app.password,
            "is_http": s.app.auto_change_proxy.split("://")[0],
            "host": s.app.auto_change_proxy.split("://")[-1].split(":")[0],
            "port": s.app.auto_change_proxy.rsplit(":", 1)[-1].split(":")[0],
            "is_proxy": s.app.is_proxy
        }
        copy_config_dict = copy.deepcopy(base_config_dict)
        _sysTrayIcon.show_config = True
        inputDialog = PanConfigWindow(s.app, copy_config_dict)
        s.root.wait_window(inputDialog)  # 这一句很重要！！！
        if inputDialog.config_dict != None and inputDialog.config_dict != base_config_dict:
            print("in")
            print(inputDialog.config_dict)
            print(base_config_dict)
            s.app.auto_change_bz, s.app.auto_change_time, s.app.auto_change_page, s.app.username, s.app.password, is_http, host, port, s.app.is_proxy = inputDialog.config_dict.values()
            if is_http and host and port:
                s.app.auto_change_proxy = f"{is_http}://{host}:{port}"
            else:
                s.app.auto_change_proxy = ""
            if inputDialog.config_dict['time'] != base_config_dict['time'] or inputDialog.config_dict['page'] != \
                    base_config_dict['page']:
                s.app.B5['text'] = "开启自动"
                s.app.button_auto_change()

            if inputDialog.config_dict['is_proxy'] != base_config_dict['is_proxy'] or inputDialog.config_dict[
                'is_http'] != \
                    base_config_dict['is_http'] or inputDialog.config_dict['host'] != base_config_dict['host'] or \
                    inputDialog.config_dict['port'] != base_config_dict['port']:
                s.app.is_proxy = inputDialog.config_dict['is_proxy']
                s.change_menu(_sysTrayIcon)

            if inputDialog.config_dict['username'] != base_config_dict['username'] or inputDialog.config_dict[
                'password'] != \
                    base_config_dict['password']:
                s.app.is_login(s.app.username, s.app.password)
        _sysTrayIcon.show_config = False


if __name__ == '__main__':
    q = queue.Queue()
    Main = _Main()
    Main.main()
