# LXMC Playlist Merger

A desktop application for merging LXMC playlist files.

## Features

- Load and compare two .lxmc playlist files
- Automatically identify common songs and unique songs in each file
- Merge playlists with one click
- Dark theme interface

## Download

Download the latest release: [LXMC-Playlist-Merger.exe](https://github.com/pyyyQWQ/lxmc-playlist-merger/releases)

## Usage

1. Click "File 1" to select your first .lxmc playlist file
2. Click "File 2" to select your second .lxmc playlist file
3. Click "Compare & Merge" to analyze the playlists
4. Click "Download Merged Playlist" to save the result

## Building from Source

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name LXMC-Playlist-Merger --icon=lxmc_icon.ico lxmc_merger.py
```

## License

MIT
