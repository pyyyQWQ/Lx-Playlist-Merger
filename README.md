# LXMC 歌单合并工具

QQ音乐 .lxmc 歌单文件的合并工具，支持拖拽上传、对比去重、一键合并下载。

## 功能特性

- 拖拽上传两个 .lxmc 歌单文件
- 自动解析并显示歌单统计信息（歌曲数、歌手数）
- 智能对比：识别共有歌曲、各自独有歌曲
- 一键合并去重，保持原始顺序
- 直接下载合并后的 .lxmc 文件

## 使用方式

### 桌面版（推荐）

下载 `LXMC-Playlist-Merger.exe`，双击运行即可。

### 网页版

打开 `lxmc-merge-tool.html`，用浏览器使用。

## 技术栈

- 桌面版：Python 3 + tkinter（内置 gzip 解压，无需外部依赖）
- 网页版：HTML + CSS + JavaScript（pako.js 用于 gzip）

## 项目地址

https://github.com/pyyyQWQ/lxmc-playlist-merger