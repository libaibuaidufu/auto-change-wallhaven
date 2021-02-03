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
pyinstaller -D -w 壁纸.py -i 钱袋.ico --add-data 钱袋.ico;. --add-data config.ini;.
# upx 压缩
pyinstaller -D -w 壁纸.py -i 钱袋.ico --add-data 钱袋.ico;. --add-data config.ini;. --upx-dir=upx/upx.exe
```

### 下载 release 包
直接运行

**修改配置后 点击确定 执行**

#### 自定义
可以自己写修改icon 和 标题 ，然后自己打包。

github: [upx](https://github.com/upx/upx)
### 预览
![image](https://github.com/libaibuaidufu/auto-change-wallhaven/blob/master/preview.png)