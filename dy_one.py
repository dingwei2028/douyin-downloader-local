# -*- coding: utf-8 -*-
r"""抖音单条视频下载：dy_one.py <URL> [video|original|720|audio]

与 dy_run.py 四件套同语义，但只处理**一条**链接：
  original = 原画（上传母带）MP4 + MP3   ← 默认，画质优先
  video    = 最高转码档 MP4 + MP3        720 = 720p MP4 + MP3
  audio    = 只留 MP3
不传 URL 时读 dy_urls.txt 里第一条抖音链接。

为什么默认 original：单条下载的语义就是"我要这一条"，而抖音 web detail 的
bit_rate 阶梯最高档常只有 720（960x720 / ~1.2 Mbps）。原画不在阶梯里，要走
/aweme/v1/play/?ratio=default 探测上传母带——同一条视频实测 1440x1080 HEVC
60fps 14.6 Mbps vs 阶梯最高档 960x720 h264 30fps 1.15 Mbps。体积约十余倍，
嫌大就用 720。

背景：抖音 2026-09 起对 aweme/detail 等接口启用 Argus 门禁，纯 HTTP 必 403；
单作品的详情由 DouyinAPIClient.get_video_detail 走浏览器兜底拿
（页内发起 → 200），拿到详情后走与批量模式完全相同的落盘路径。
"""
import os
import sys

import yaml

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

import dy_run  # noqa: E402  复用模式表 / 下载器入口 / MP3 转换

CONFIG_FILE = os.path.join(BASE, "config.yml")
URLS_FILE = os.path.join(BASE, "dy_urls.txt")
ONE_CONFIG = os.path.join(BASE, "_cfg_dy_one.yml")


def read_first_url():
    if not os.path.exists(URLS_FILE):
        return ""
    with open(URLS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "douyin.com" in line:
                return line
    return ""


def build_one_config(mode, url):
    spec = dy_run.MODES[mode]
    cfg = yaml.safe_load(open(CONFIG_FILE, encoding="utf-8"))
    cfg["video_quality"] = spec["video_quality"]
    cfg["redownload_missing_files"] = spec["redownload"]
    cfg["link"] = [url]
    with open(ONE_CONFIG, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, sort_keys=False)
    return ONE_CONFIG


def main():
    raw = [a.strip() for a in sys.argv[1:] if a.strip()]
    url = next((a for a in raw if "douyin.com" in a or a.startswith("http")), "")
    mode = next((a.lower() for a in raw if a.lower() in dy_run.MODES), "original")

    if not url:
        url = read_first_url()
        if url:
            print(f"[i] 未传 URL，用 dy_urls.txt 里第一条: {url}")
    if not url:
        print(f"用法: dy_one.py <抖音链接> [{'|'.join(dy_run.MODES)}]")
        print("     链接形态: douyin.com/video/xxx  |  ...?modal_id=xxx  |  v.douyin.com/xxx")
        sys.exit(1)

    spec = dy_run.MODES[mode]
    print(f"==== dy_one [{mode}] {spec['label']} ====")
    print(f"[i] 目标: {url}")

    variant = build_one_config(mode, url)
    rc = dy_run.run_downloader(variant)
    if rc != 0:
        print(f"[warn] 下载器退出码 {rc}")

    converted, deleted = dy_run.convert_tree(mode)
    print(
        f"==== 完成: 新转 MP3 {converted} 个"
        + (f"，删除 MP4 {deleted} 个" if deleted else "")
        + " ===="
    )


if __name__ == "__main__":
    main()
