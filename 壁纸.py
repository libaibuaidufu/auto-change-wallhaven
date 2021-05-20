#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2021/2/2 14:21
@File    : bz.py
@author  : dfkai
@Software: PyCharm
"""
import configparser
import ctypes
import json
import os
import queue
import random
import threading
import time
import urllib
from tkinter import *
from tkinter import messagebox, ttk

import requests
import win32api
import win32con
import win32gui
import win32gui_struct
from PIL import Image, ImageTk
from bs4 import BeautifulSoup


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class AutoChangeBZ():
    def __init__(self):
        base_dir = os.getcwd()
        self.config_path = os.path.join(base_dir, 'config.ini')
        self.t_id = 0  # 线程控制

    def change_bz(self, t_id, auto_change_time, auto_change_url, auto_change_page,auto_change_proxy):
        while True:
            try:
                if t_id != self.t_id:
                    break
                self.next_bz(auto_change_url, auto_change_page,auto_change_proxy)
                time.sleep(int(auto_change_time))
            except Exception as e:
                print('1', e)
                messagebox.showerror('错误', '请重新启动！')
                break

    def main(self):
        random_url = 'https://wallhaven.cc/search?sorting=random&ref=fp&seed=gLasU&page='

        if os.path.isfile(self.config_path):
            config_dict = configparser.ConfigParser()
            config_dict.read(self.config_path, encoding="utf8")
            auto_change_bz = config_dict.get("壁纸设置", '自动换壁纸')
            auto_change_time = config_dict.get("壁纸设置", '换壁纸时间')
            auto_change_url = config_dict.get('壁纸设置', '壁纸地址')
            auto_change_img = config_dict.get('壁纸设置', '缓存地址')
            auto_change_page = config_dict.get('壁纸设置', '壁纸页数')
            auto_change_proxy = config_dict.get('壁纸设置', '代理地址')
        else:
            auto_change_bz = '是'
            auto_change_time = 600
            auto_change_url = random_url
            auto_change_img = None
            auto_change_page = 15
            auto_change_proxy = ''
        return auto_change_bz, auto_change_time, auto_change_url, auto_change_img, auto_change_page,auto_change_proxy

    def next_bz(self, auto_change_url, auto_change_page=15,auto_change_proxy=''):
        base_url = 'https://w.wallhaven.cc/full/{src_type}/wallhaven-{src_name}'
        try:
            if int(auto_change_page) <= 1:
                page = 1
            else:
                page = random.randrange(1, int(auto_change_page))
            random_page_url = auto_change_url + str(page)
            print(random_page_url)
            if auto_change_proxy:
                proxies = {
                    'https': auto_change_proxy,
                    'http':auto_change_proxy
                }
                response = requests.get(random_page_url, proxies=proxies)
            else:
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
            print(src_num_url)
        except Exception as e:
            print(e)
            messagebox.showerror('错误', "请查看是否壁纸地址有问题！")
            return
        print('更换壁纸中')
        try:
            opener = urllib.request.build_opener()  # 创建一个opener
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]  # 给这个opener设置header #'Mozilla/5.0'
            urllib.request.install_opener(opener)  # 安装这个opener的表头header,用于模拟浏览器.如果不模拟浏览器,下面的代码会404
            PATH = urllib.request.urlretrieve(src_num_url)[0]  # 获取处理图片地址
            ctypes.windll.user32.SystemParametersInfoW(20, 0, PATH, 3)  # 设置桌面
            print('壁纸更换完毕')
            config_dict = configparser.ConfigParser()
            config_dict.read(self.config_path, encoding="utf8")
            config_dict.set("壁纸设置", '缓存地址', PATH)
            with open(self.config_path, "w+", encoding="utf8") as f:
                config_dict.write(f)
            q.put(json.dumps({'path': PATH, 'src_name': src_name}))
        except Exception as e:
            print(e)
            print(image_type_check)
            print(image_tag)
            print(src_url)
            print(random_page_url)
            print(src_num_url)
            messagebox.showerror('错误', "设置壁纸失败，那里出问题了我也不知道！可能是切换太频繁被限制了，等一会就好了。")


class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.config_path = 'config.ini'
        self.master = master
        self.width = 1280
        self.height = 800
        self.master.geometry("1280x800")
        self.master.resizable(0, 0)
        self.master.title("壁纸")
        self.master.iconbitmap(resource_path('钱袋.ico'))  # 设置图标，仅支持.ico文件
        self.pack()
        self.PATH, self.src_name = None, None
        self.acbz = AutoChangeBZ()
        self.auto_change_bz, self.auto_change_time, self.auto_change_url, self.auto_change_img, self.auto_change_page,self.auto_change_proxy = self.acbz.main()
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

    def create_widgets(self):
        self.L1 = Label(self, text="壁纸地址：")
        self.L1.pack(padx=5, pady=10, side=LEFT)

        self.E1 = Entry(self, bd=5, width=65)
        contents = StringVar()
        contents.set(self.auto_change_url)
        self.E1["textvariable"] = contents
        self.E1.pack(padx=5, pady=10, side=LEFT)

        self.L5 = Label(self, text="代理：")
        self.L5.pack(padx=5, pady=10, side=LEFT)

        self.E5 = Entry(self, bd=5, width=20)
        contents = StringVar()
        contents.set(self.auto_change_proxy)
        self.E5["textvariable"] = contents
        self.E5.pack(padx=5, pady=10, side=LEFT)

        self.L2 = Label(self, text="自动更换：")
        self.L2.pack(padx=5, pady=10, side=LEFT)

        self.E2 = ttk.Combobox(self, width=2)  # 初始化
        is_auto_change = ("是", "否")
        self.E2["value"] = is_auto_change
        self.E2.current(is_auto_change.index(self.auto_change_bz))
        self.E2.pack(padx=5, pady=10, side=LEFT)

        self.L3 = Label(self, text="时间：")
        self.L3.pack(padx=5, pady=10, side=LEFT)

        self.E3 = Entry(self, bd=5, width=4)
        contents = IntVar()
        contents.set(self.auto_change_time)
        self.E3["textvariable"] = contents
        self.E3.pack(padx=5, pady=10, side=LEFT)

        self.L4 = Label(self, text="总页数：")
        self.L4.pack(padx=5, pady=10, side=LEFT)

        self.E4 = Entry(self, bd=5, width=4)
        contents = IntVar()
        contents.set(self.auto_change_page)
        self.E4["textvariable"] = contents
        self.E4.pack(padx=5, pady=10, side=LEFT)

        self.B2 = Button(self, text="确定", command=self.get_config)
        self.B2.pack(padx=5, pady=10, side=LEFT)

        self.B1 = Button(self, text="切换", command=self.next_bz)
        self.B1.pack(padx=20, pady=10, side=LEFT)
        self.B3 = Button(self, text="保存", command=self.show_msg)
        self.B3.pack(padx=5, pady=10, side=LEFT)

        self.l = Label(self.master, image=self.img, height=self.height, width=self.width)
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
            self.PATH = path_dict['path']
            self.src_name = path_dict['src_name']
            img = Image.open(self.PATH)
            pil_image_resized = self.resize(self.width, self.height, img)  # 缩放图像让它保持比例，同时限制在一个矩形框范围内  【调用函数，返回整改后的图片】
            tk_image = ImageTk.PhotoImage(pil_image_resized)  # 把PIL图像对象转变为Tkinter的PhotoImage对象  【转换格式，方便在窗口展示】
            self.l.configure(image=tk_image)

    def get_config(self):
        self.acbz.t_id += 1
        self.auto_change_bz = self.E2.get()
        self.auto_change_time = self.E3.get()
        self.auto_change_url = self.E1.get()
        self.auto_change_page = self.E4.get()
        self.auto_change_proxy = self.E5.get()
        if os.path.isfile(self.config_path):
            config_dict = configparser.ConfigParser()
            config_dict.read(self.config_path, encoding="utf8")
            config_dict.set("壁纸设置", '自动换壁纸', self.auto_change_bz)
            config_dict.set("壁纸设置", '换壁纸时间', self.auto_change_time)
            config_dict.set('壁纸设置', '壁纸地址', self.auto_change_url)
            config_dict.set('壁纸设置', '壁纸页数', self.auto_change_page)
            config_dict.set('壁纸设置', '代理地址', self.auto_change_proxy)
            with open(self.config_path, "w+", encoding="utf8") as f:
                config_dict.write(f)
        messagebox.showinfo('配置', '配置保存成功')
        if self.auto_change_bz == "是":
            self.th_auto_change_bz = threading.Thread(target=self.acbz.change_bz,
                                                      args=(
                                                          self.acbz.t_id, self.auto_change_time,
                                                          self.auto_change_url, self.auto_change_page,self.auto_change_proxy),
                                                      daemon=True)
            self.th_auto_change_bz.start()

    def next_bz(self):
        self.th_next_bz = threading.Thread(target=self.acbz.next_bz,
                                           args=(self.auto_change_url, self.auto_change_page,self.auto_change_proxy), daemon=True)
        self.th_next_bz.start()

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


class SysTrayIcon(object):
    '''SysTrayIcon类用于显示任务栏图标'''
    QUIT = 'QUIT'
    SPECIAL_ACTIONS = [QUIT]
    FIRST_ID = 5320

    def __init__(s, icon, hover_text, menu_options, on_quit, tk_window=None, default_menu_index=None,
                 window_class_name=None):
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
        s.refresh(title='壁纸软件已后台！', msg='点击重新打开', time=500)

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
        nid = (s.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)  # 终止应用程序。
        if exit and s.on_quit:
            s.on_quit()  # 需要传递自身过去时用 s.on_quit(s)
        else:
            s.root.deiconify()  # 显示tk窗口

    def notify(s, hwnd, msg, wparam, lparam):
        '''鼠标事件'''
        if lparam == win32con.WM_LBUTTONDBLCLK:  # 双击左键
            pass
        elif lparam == win32con.WM_RBUTTONUP:  # 右键弹起
            s.show_menu()
        elif lparam == win32con.WM_LBUTTONUP:  # 左键弹起
            s.destroy(exit=0)
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


class _Main:  # 调用SysTrayIcon的Demo窗口
    def __init__(s):
        s.SysTrayIcon = None  # 判断是否打开系统托盘图标

    def main(s):
        # tk窗口
        s.root = Tk()
        s.app = Application(master=s.root)
        s.root.bind("<Unmap>",
                    lambda event: s.Hidden_window() if s.root.state() == 'iconic' else False)  # 窗口最小化判断，可以说是调用最重要的一步
        s.root.protocol('WM_DELETE_WINDOW', s.exit)  # 点击Tk窗口关闭时直接调用s.exit，不使用默认关闭
        s.root.mainloop()

    def switch_icon(s, _sysTrayIcon, icon=resource_path('钱袋.ico')):
        # 点击右键菜单项目会传递SysTrayIcon自身给引用的函数，所以这里的_sysTrayIcon = s.sysTrayIcon
        # 只是一个改图标的例子，不需要的可以删除此函数
        _sysTrayIcon.icon = icon
        _sysTrayIcon.refresh()

        # 气泡提示的例子
        s.show_msg(title='图标更换', msg='图标更换成功！', time=500)

    def show_msg(s, title='壁纸', msg='喔喔喔喔', time=500):
        s.SysTrayIcon.refresh(title=title, msg=msg, time=time)

    def Hidden_window(s, icon=resource_path('钱袋.ico'), hover_text="壁纸"):
        '''隐藏窗口至托盘区，调用SysTrayIcon的重要函数'''

        # 托盘图标右键菜单, 格式: ('name', None, callback),下面也是二级菜单的例子
        # 24行有自动添加‘退出’，不需要的可删除
        # menu_options = (('一级 菜单', None, s.switch_icon),
        #                 ('二级 菜单', None, (('更改 图标', None, s.switch_icon),)))
        menu_options = ()
        s.root.withdraw()  # 隐藏tk窗口
        if not s.SysTrayIcon: s.SysTrayIcon = SysTrayIcon(
            icon,  # 图标
            hover_text,  # 光标停留显示文字
            menu_options,  # 右键菜单
            on_quit=s.exit,  # 退出调用
            tk_window=s.root,  # Tk窗口
        )
        s.SysTrayIcon.activation()

    def exit(s, _sysTrayIcon=None):
        s.root.destroy()


if __name__ == '__main__':
    q = queue.Queue()
    Main = _Main()
    Main.main()
