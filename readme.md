# 一个自动更换壁纸的小软件

> python 3+

### python 安装运行

1. 运行

```bash
pip install requirements.txt
python 壁纸.py
```

2. 打包

```bash
# 单文件 单文件读取配置  (非必须-需要把配置文件config.ini 复制过去才能使用),如果添加 --add-data config.ini;. 就无法永久保存配置
pyinstaller -F -w 壁纸.py -i icon.ico --add-data icon.ico;.

# 单文件 单文件读取配置 需要把配置文件config.ini 复制过去才能使用
pyinstaller -F -w bz_not_gui.py -i icon.ico --add-data icon.ico;.

#######################
#其他打包方式 文件方式 不需要复制config.ini
pyinstaller -D -w 壁纸.py -i icon.ico --add-data icon.ico;. --add-data config.ini;.
# upx 压缩  同样需要复制config.ini 报错打不开 缺少dll
pyinstaller -F -w 壁纸.py -i icon.ico --add-data icon.ico;.  --upx-dir=upx/upx.exe
```

### 下载 release 包

直接运行

**修改配置后 点击确定 执行**

#### 配置

```
[壁纸设置]
自动换壁纸 = 否
换壁纸时间 = 600
壁纸地址 = https://wallhaven.cc/favorites?page=
壁纸页数 = 10
代理地址 = http://127.0.0.1:8889
缓存地址 = 
用户名 = username
密码 = password
是否启用代理 = 关闭
```

#### 自定义

可以自己写修改icon 和 标题 ，然后自己打包。
###### 2021-7-23 更新

1. 修改整体样式
2. 扩展最小化时设置功能
3. 整体重构修改代理问题
###### 2021-7-20 更新

1. 更新处理代理问题 保证更好的兼容性
2. 登录帐号 查看自己收藏 完善登录问题
###### 2021-5-20 更新

1. 增加登录功能，登录后可选择自己收藏图片展示
2. 增加代理功能，更快访问

github: [upx](https://github.com/upx/upx)

### 预览

![image](https://github.com/libaibuaidufu/auto-change-wallhaven/blob/master/preview.png)