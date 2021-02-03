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
```

### 下载 release 包
直接运行


#### 自定义
可以自己写修改icon 和 标题 ，然后自己打包。