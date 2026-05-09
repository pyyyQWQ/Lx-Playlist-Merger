# LXMC 歌单合并工具

一款用于合并 LXMC 歌单文件的桌面应用程序。

## 功能特点

- 同时加载两个 .lxmc 歌单文件
- 自动识别两首歌单中的共同曲目和各独有的曲目
- 一键合并歌单
- 深色主题界面

## 下载使用

下载最新版本：[LXMC-Playlist-Merger.exe](https://github.com/pyyyQWQ/lxmc-playlist-merger/releases)

## 使用方法

1. 点击「File 1」选择第一个 .lxmc 歌单文件
2. 点击「File 2」选择第二个 .lxmc 歌单文件
3. 点击「Compare & Merge」分析歌单
4. 点击「Download Merged Playlist」保存合并后的歌单

## 从源码构建

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name LXMC-Playlist-Merger --icon=lxmc_icon.ico lxmc_merger.py
```

## 开源协议

MIT