# -*- coding: utf-8 -*-
"""
LXMC 歌单合并工具  - Python + tkinter 版本
单文件，可打包为 exe（pyinstaller --onefile lxmc_merger.py）
"""
import gzip
import json
import os
import sys
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

__version__ = "1.0.1"

# ─── Color Palette ───────────────────────────────────────────────────
BG       = "#0f1117"
CARD     = "#161b22"
CARD2    = "#1c2128"
BORDER   = "#30363d"
TEXT     = "#e6edf3"
TEXT2    = "#8b949e"
ACCENT   = "#6366f1"
ACCENT2  = "#818cf8"
GREEN    = "#22c55e"
RED      = "#f87171"
ORANGE   = "#fb923c"
BLUE     = "#38bdf8"
DISABLED_BG = "#2d333b"


# ─── LXMC File Parser ──────────────────────────────────────────────
def load_lxmc(path: str):
    """Load and decompress an .lxmc file. Returns parsed dict or None."""
    try:
        with open(path, "rb") as f:
            raw = f.read()
        # Try gzip first
        try:
            text = gzip.decompress(raw).decode("utf-8")
        except Exception:
            # Try raw JSON
            try:
                text = raw.decode("utf-8")
            except Exception:
                return None
        data = json.loads(text)
        if not (data.get("data") and data["data"].get("list")):
            return None
        return data
    except Exception:
        return None


def save_lxmc(data: dict, path: str):
    """Compress and save an .lxmc file."""
    text = json.dumps(data, ensure_ascii=False)
    compressed = gzip.compress(text.encode("utf-8"))
    with open(path, "wb") as f:
        f.write(compressed)


# ─── Helpers ────────────────────────────────────────────────────────
def song_key(song: dict) -> str:
    return f"{song.get('source', '')}_{song.get('id', '')}"


# ─── App ───────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"LXMC 歌单合并工具  v{__version__}")
        self.geometry("900x700")
        self.minsize(800, 580)
        self.configure(bg=BG)
        self._center_window()

        # State
        self.file1_path = None
        self.file2_path = None
        self.file1_data = None
        self.file2_data = None
        self.file1_list = []
        self.file2_list = []
        self.merged_data = None
        self.all_rows = []   # (idx, name, singer, status)

        self._build_ui()
        self._apply_dark_theme()

    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - max(w, 800)) // 2
        y = (sh - max(h, 580)) // 2
        self.geometry(f"+{x}+{y}")

    # ─── Build UI ───────────────────────────────────────────────────
    def _build_ui(self):
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=20, pady=16)

        # ── Header ──
        hdr = tk.Frame(main, bg=BG)
        hdr.pack(fill="x", pady=(0, 16))
        title = tk.Label(hdr,
            text="🎵  LXMC 歌单合并工具",
            font=("Segoe UI", 18, "bold"),
            fg=ACCENT2, bg=BG, anchor="w")
        title.pack(side="left")
        tk.Label(hdr, text="拖入两个歌单 → 对比 → 合并下载",
            font=("Segoe UI", 10), fg=TEXT2, bg=BG, anchor="e").pack(side="right")

        # ── Error label ──
        self.err_lbl = tk.Label(main, text="", font=("Segoe UI", 10),
            fg=RED, bg=BG, anchor="w", wraplen=860, justify="left")
        self.err_lbl.pack(fill="x", pady=(0, 8))
        self.err_lbl.pack_forget()

        # ── Drop zones ──
        zone_row = tk.Frame(main, bg=BG)
        zone_row.pack(fill="x", pady=(0, 12))

        self.zone1 = self._make_zone(zone_row, "📁  文件 1",
            "点击选择 .lxmc 文件", 0)
        self.zone1.pack(side="left", fill="both", expand=True, padx=(0, 6))

        swap_btn = tk.Button(zone_row, text="⇄", font=("Segoe UI", 16),
            bg=CARD2, fg=TEXT2, bd=0, padx=8, pady=4,
            cursor="hand2", command=self._swap)
        swap_btn.pack(side="left", padx=4)

        self.zone2 = self._make_zone(zone_row, "📁  文件 2",
            "点击选择 .lxmc 文件", 1)
        self.zone2.pack(side="left", fill="both", expand=True, padx=(6, 0))

        # ── Stats ──
        self.stats_frame = tk.Frame(main, bg=BG)
        self.stats_frame.pack(fill="x", pady=(0, 12))
        self._make_stats(self.stats_frame)

        # ── Action buttons ──
        btn_row = tk.Frame(main, bg=BG)
        btn_row.pack(fill="x", pady=(0, 12))

        self.btn_merge = tk.Button(btn_row, text="🔍  对比并合并",
            font=("Segoe UI", 11, "bold"), bg=DISABLED_BG, fg="#555",
            bd=0, padx=20, pady=9, cursor="hand2", state="disabled")
        self.btn_merge.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.btn_merge.bind("<Button-1>", lambda e: self._on_merge_click())

        self.btn_download = tk.Button(btn_row, text="⬇  下载合并歌单",
            font=("Segoe UI", 11, "bold"), bg=DISABLED_BG, fg="#555",
            bd=0, padx=20, pady=9, cursor="hand2",
            state="disabled", command=self._download)
        self.btn_download.pack(side="left", fill="x", expand=True, padx=(6, 0))

        self.btn_clear = tk.Button(btn_row, text="🗑 清空",
            font=("Segoe UI", 10), bg=CARD2, fg=TEXT2,
            bd=0, padx=14, pady=9, cursor="hand2",
            command=self._clear, state="disabled")
        self.btn_clear.pack(side="right")

        # ── Table ──
        table_frame = tk.Frame(main, bg=BORDER, bd=0)
        table_frame.pack(fill="both", expand=True)

        # Column headers
        hdr_row = tk.Frame(table_frame, bg=CARD2)
        hdr_row.pack(fill="x")
        headers = [("#", 50), ("歌曲名", 380), ("歌手", 250), ("状态", 90)]
        for h, w in headers:
            tk.Label(hdr_row, text=h, font=("Segoe UI", 10, "bold"),
                fg=TEXT2, bg=CARD2, width=w, anchor="w",
                padx=12, pady=7).pack(side="left")

        # Scrollable treeview
        tree_scroll = tk.Scrollbar(table_frame, bg=BORDER)
        tree_scroll.pack(side="right", fill="y")

        self.tree = ttk.Treeview(table_frame, show="", yscrollcommand=tree_scroll.set,
            height=20)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)

        self.tree.tag_configure("common", background="#0f1f10")
        self.tree.tag_configure("only1",  background="#1f1005")
        self.tree.tag_configure("only2",  background="#051020")
        self.tree.tag_configure("hover",   background=CARD2)

        # Hint (shown when no data)
        self.hint_lbl = tk.Label(table_frame,
            text="加载两个歌单文件后，点击「对比并合并」即可开始",
            font=("Segoe UI", 12), fg=TEXT2, bg=CARD, pady=40)
        self.hint_lbl.pack(fill="both", expand=True)

        self.tree.bind("<Motion>", self._on_row_hover)
        self.tree.bind("<Leave>",  self._on_row_leave)

    def _make_zone(self, parent, title, hint, idx):
        """Create a clickable file-zone card."""
        f = tk.Frame(parent, bg=CARD, bd=1, relief="solid",
            highlightbackground=BORDER, highlightthickness=1,
            cursor="hand2")
        f.idx = idx

        # Title
        lbl = tk.Label(f, text=title, font=("Segoe UI", 11, "bold"),
            fg=TEXT2, bg=CARD, anchor="w")
        lbl.pack(anchor="w", padx=16, pady=(14, 2))

        # Hint
        hint_lbl = tk.Label(f, text=hint, font=("Segoe UI", 10),
            fg=TEXT2, bg=CARD, anchor="w")
        hint_lbl.pack(anchor="w", padx=16)

        # File name (shown after load)
        self._zone_name_lbl(f, idx, "name")
        self._zone_name_lbl(f, idx, "count")

        # Bind events
        f.bind("<Button-1>", lambda e, i=idx: self._open_file(i))
        for child in f.winfo_children():
            child.bind("<Button-1>", lambda e, i=idx: self._open_file(i))

        return f

    def _zone_name_lbl(self, zone, idx, which):
        setattr(self, f"zone{idx+1}_{which}_lbl",
            tk.Label(zone, text="", font=("Segoe UI", 10, "bold"),
                fg=ACCENT2, bg=CARD, anchor="w"))
        lbl = getattr(self, f"zone{idx+1}_{which}_lbl")
        lbl.pack(anchor="w", padx=16, pady=(1, 0))
        return lbl

    def _make_stats(self, parent):
        cards = [
            ("common", "共有歌曲",   "0", GREEN),
            ("only1",  "仅文件1新增", "0", ORANGE),
            ("only2",  "仅文件2保留", "0", BLUE),
            ("total",  "合并后总计",  "0", ACCENT2),
        ]
        self.stat_widgets = {}
        for key, label, default, color in cards:
            card = tk.Frame(parent, bg=CARD, bd=1, relief="solid",
                highlightbackground=BORDER, highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=(0, 6))
            if key == "total":
                card.pack_configure(padx=(0, 0))
            num = tk.Label(card, text=default,
                font=("Segoe UI", 20, "bold"), fg=color, bg=CARD, pady=10)
            num.pack()
            tk.Label(card, text=label,
                font=("Segoe UI", 10), fg=TEXT2, bg=CARD).pack()
            self.stat_widgets[key] = num

    def _apply_dark_theme(self):
        """Apply dark theme via ttk styles."""
        try:
            style = ttk.Style(self)
            style.theme_use("clam")

            style.configure(".", background=BG, foreground=TEXT, fieldbackground=CARD)
            style.configure("Treeview", background=CARD, fieldbackground=CARD,
                foreground=TEXT, borderwidth=0, rowheight=28)
            style.configure("Treeview.Heading", background=CARD2, foreground=TEXT2,
                borderwidth=0, rowheight=32)
            style.map("Treeview",
                background=[("hover", CARD2)],
                foreground=[("hover", TEXT)])

            # Scrollbar
            sb = ttk.Style()
            sb.configure("Vertical.TScrollbar", background=BORDER,
                troughcolor=CARD, arrowcolor=TEXT2)
        except Exception:
            pass

    # ── File Loading ───────────────────────────────────────────────
    def _open_file(self, idx):
        path = filedialog.askopenfilename(
            title=f"选择文件 {'1' if idx == 0 else '2'} (.lxmc)",
            filetypes=[("LXMC 文件", "*.lxmc"), ("所有文件", "*.*")])
        if path:
            self._load_file(idx, path)

    def _load_file(self, idx, path):
        data = load_lxmc(path)
        if not data:
            self._show_err(f"无法解析文件：{Path(path).name}\n请确认是有效的 .lxmc 歌单文件")
            return
        songs = data["data"]["list"]
        name  = data["data"].get("name", Path(path).name)

        if idx == 0:
            self.file1_path = path
            self.file1_data = data
            self.file1_list = songs
            lbl = self.zone1_name_lbl
            clbl = self.zone1_count_lbl
            ztitle = self.zone1.winfo_children()[0]
        else:
            self.file2_path = path
            self.file2_data = data
            self.file2_list = songs
            lbl = self.zone2_name_lbl
            clbl = self.zone2_count_lbl
            ztitle = self.zone2.winfo_children()[0]

        lbl.config(text=Path(path).name)
        clbl.config(text=f"  🎵  {len(songs)} 首歌曲")
        ztitle.config(fg=GREEN, text=f"✅  文件 {'1' if idx == 0 else '2'} 已加载")
        self._hide_err()
        self._update_buttons()

    def _swap(self):
        """Swap file1 and file2."""
        for attr in ("path", "data", "list"):
            k1, k2 = f"file1_{attr}", f"file2_{attr}"
            setattr(self, k1, getattr(self, k2))
            setattr(self, k2, getattr(self, k1))

        # Rebuild UI for both zones
        for idx in (0, 1):
            zone = self.zone1 if idx == 0 else self.zone2
            data = self.file1_data if idx == 0 else self.file2_data
            path = self.file1_path  if idx == 0 else self.file2_path
            if data:
                lbl = self.zone1_name_lbl  if idx == 0 else self.zone2_name_lbl
                clbl = self.zone1_count_lbl if idx == 0 else self.zone2_count_lbl
                ztitle = zone.winfo_children()[0]
                lbl.config(text=Path(path).name)
                clbl.config(text=f"  🎵  {len(data['data']['list'])} 首歌曲")
                ztitle.config(fg=GREEN, text=f"✅  文件 {'1' if idx == 0 else '2'} 已加载")
            else:
                ztitle = zone.winfo_children()[0]
                lbl = self.zone1_name_lbl  if idx == 0 else self.zone2_name_lbl
                clbl = self.zone1_count_lbl if idx == 0 else self.zone2_count_lbl
                ztitle.config(fg=TEXT2, text=f"📁  文件 {'1' if idx == 0 else '2'}")
                lbl.config(text="")
                clbl.config(text="")
        self._update_buttons()

    def _update_buttons(self):
        has_both = bool(self.file1_data and self.file2_data)
        if has_both:
            self.btn_merge.config(state="normal", bg=ACCENT, fg="white")
        else:
            self.btn_merge.config(state="disabled", bg=DISABLED_BG, fg="#555")

        has_any = bool(self.file1_data or self.file2_data)
        self.btn_clear.config(state="normal" if has_any else "disabled")
        self.btn_download.config(state="disabled", bg=DISABLED_BG, fg="#555")

    # ── Merge ───────────────────────────────────────────────────────
    def _on_merge_click(self):
        if self.btn_merge.cget("state") == "disabled":
            self._show_err("请先加载两个歌单文件")
            return
        self._do_merge()

    def _do_merge(self):
        try:
            self._hide_err()
            f1_list = self.file1_list
            f2_list = self.file2_list

            if not f1_list or not f2_list:
                self._show_err("请先选择两个歌单文件")
                return

            # Build sets
            k1 = {song_key(s) for s in f1_list}
            k2 = {song_key(s) for s in f2_list}

            common = [s for s in f2_list if song_key(s) in k1]
            only1  = [s for s in f1_list if song_key(s) not in k2]
            only2  = [s for s in f2_list if song_key(s) not in k1]

            merged_list = common + only1 + only2

            # Build merged data object (copy file2 as base)
            merged = json.loads(json.dumps(self.file2_data))
            merged["data"]["list"] = merged_list
            merged["data"]["locationUpdateTime"] = int(time.time() * 1000)
            self.merged_data = merged

            # Update stats
            self.stat_widgets["common"].config(text=str(len(common)))
            self.stat_widgets["only1"].config(text=str(len(only1)))
            self.stat_widgets["only2"].config(text=str(len(only2)))
            self.stat_widgets["total"].config(text=str(len(merged_list)))

            # Build row list
            self.all_rows = []
            for i, s in enumerate(common, 1):
                self.all_rows.append((i,      s["name"], s.get("singer",""), "common"))
            for i, s in enumerate(only1, len(common)+1):
                self.all_rows.append((i,       s["name"], s.get("singer",""), "only1"))
            for i, s in enumerate(only2, len(common)+len(only1)+1):
                self.all_rows.append((i,       s["name"], s.get("singer",""), "only2"))

            # Render table (first 100 rows)
            self._render_table(100)
            self.hint_lbl.pack_forget()
            self.btn_download.config(state="normal", bg=GREEN, fg="white")

        except Exception as ex:
            self._show_err(f"合并出错: {ex}")

    def _render_table(self, limit=None):
        """Render up to `limit` rows in the treeview."""
        rows = self.all_rows[:limit] if limit else self.all_rows
        # Clear
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Insert
        for idx, name, singer, status in rows:
            tag = status
            if status == "common":
                tag_str = "共有"
                fg = GREEN
            elif status == "only1":
                tag_str = "+文件1"
                fg = ORANGE
            else:
                tag_str = "+文件2"
                fg = BLUE
            self.tree.insert("", "end", values=(idx, name, singer, tag_str), tags=(tag,))

        # Footer
        total = len(self.all_rows)
        shown = limit if limit and limit < total else total
        if limit and total > limit:
            self.hint_lbl.config(
                text=f"  仅显示前 {limit} 首（共 {total} 首）— 滚动查看更多，或点击下方按钮展开全部")
            self.hint_lbl.pack(fill="x", padx=2, pady=2)
        else:
            self.hint_lbl.pack_forget()

    def _on_row_hover(self, event):
        try:
            row = self.tree.identify_row(event.y)
            if row:
                self.tree.tk.call(self.tree, "tag", "add", row, "hover")
        except Exception:
            pass

    def _on_row_leave(self, event):
        pass

    # ── Download ────────────────────────────────────────────────────
    def _download(self):
        if not self.merged_data:
            return
        default = "merged_playlist.lxmc"
        if self.file1_data:
            name = self.file1_data.get("data", {}).get("name", "merged")
            default = f"{name}_合并版.lxmc"
        path = filedialog.asksaveasfilename(
            title="保存合并歌单",
            defaultextension=".lxmc",
            filetypes=[("LXMC 文件", "*.lxmc")],
            initialfile=default)
        if not path:
            return
        try:
            save_lxmc(self.merged_data, path)
            messagebox.showinfo("✅ 完成", f"已保存到：\n{path}\n\n共 {len(self.merged_data['data']['list'])} 首歌曲")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    # ── Clear ───────────────────────────────────────────────────────
    def _clear(self):
        self.file1_path = self.file2_path = None
        self.file1_data = self.file2_data = None
        self.file1_list = self.file2_list = []
        self.merged_data = None
        self.all_rows = []

        # Reset zones
        for idx, zone in ((0, self.zone1), (1, self.zone2)):
            lbl  = self.zone1_name_lbl  if idx == 0 else self.zone2_name_lbl
            clbl = self.zone1_count_lbl if idx == 0 else self.zone2_count_lbl
            ztitle = zone.winfo_children()[0]
            ztitle.config(fg=TEXT2, text=f"📁  文件 {'1' if idx == 0 else '2'}")
            lbl.config(text="")
            clbl.config(text="")

        # Reset stats
        for key, w in self.stat_widgets.items():
            w.config(text="0")

        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.hint_lbl.config(text="加载两个歌单文件后，点击「对比并合并」即可开始")
        self.hint_lbl.pack(fill="both", expand=True)
        self._update_buttons()

    # ── Error ───────────────────────────────────────────────────────
    def _show_err(self, msg):
        self.err_lbl.config(text=msg)
        self.err_lbl.pack(fill="x", pady=(0, 8))

    def _hide_err(self):
        self.err_lbl.pack_forget()


# ─── Main ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
