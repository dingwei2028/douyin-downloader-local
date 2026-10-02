# -*- coding: utf-8 -*-
r"""抖音四件套核心：dy_run.py <video|original|720|audio>

与 yt-dlp 三件套语义对齐，另加一档「原画」：
  video    = dy_download.bat          最高转码档 MP4 + 转 MP3（128k）
  original = dy_download_original.bat 原画（上传母带）MP4 + 转 MP3
  720      = dy_download720.bat       720p MP4 + 转 MP3
  audio    = dy_audio_only.bat        只留 MP3（下 MP4 -> 转 MP3 -> 删 MP4）

video 与 720 的区别只在「抖音自己给的 bit_rate 阶梯」里挑档；该阶梯最高档
常常只有 720（960x720 / ~1.2 Mbps）。**原画不在这个阶梯里**——它要靠
/aweme/v1/play/?ratio=default 302 到上传母带（实测同一条视频：原画
1440x1080 HEVC 60fps 14.6 Mbps / 21.6 MB，而阶梯最高档 960x720 h264 30fps
1.15 Mbps / 1.9 MB）。体积可达十余倍，所以 original 是显式选择，不是默认。

实现：
  1. 从 config.yml 派生临时配置（_cfg_dy_<mode>.yml），改 video_quality /
     redownload_missing_files，不动 config.yml 本体；
  2. 调 run.py 下载；
  3. 扫描 D:\download\dy 下所有缺 MP3 的 MP4，用 CapsWriter 的 ffmpeg 补转；
     audio 模式转完删 MP4（下次运行靠 redownload_missing_files=false 不重下）。

注意 audio 模式与 video 模式会互相"抢"磁盘状态：
  audio 删过 MP4 之后，再跑 video/720 会把全部作品的 MP4 重下回来（这是预期行为）。
"""
import glob
import os
import shutil
import subprocess
import sys

import yaml

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE, "config.yml")
# 本机已知的 ffmpeg 位置，按优先级探测；都不在时退回项目依赖 / 系统 PATH。
# 这里不写死单一绝对路径：本仓库要能直接分享出去，硬编码某台机器的路径
# 在别人机器上一律失效。
FFMPEG_CANDIDATES = (
    r"C:\Github\CapsWriter-Offline\ffmpeg\bin\ffmpeg.exe",
)
AUDIO_KBPS = "128"  # 与 yt-dlp config.yaml 的 audio_quality 对齐


def resolve_ffmpeg():
    """挑一个可用的 ffmpeg：本机已知路径 → imageio-ffmpeg 自带 → PATH。"""
    for candidate in FFMPEG_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    try:
        import imageio_ffmpeg

        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled and os.path.isfile(bundled):
            return bundled
    except Exception:
        pass
    return shutil.which("ffmpeg") or "ffmpeg"

MODES = {
    "video": {"video_quality": "highest", "redownload": True, "keep_mp4": True, "label": "最高画质 MP4 + MP3"},
    "original": {"video_quality": "original", "redownload": True, "keep_mp4": True, "label": "原画 MP4 + MP3"},
    "720":   {"video_quality": "720p",    "redownload": True, "keep_mp4": True, "label": "720p MP4 + MP3"},
    "audio": {"video_quality": "highest", "redownload": False, "keep_mp4": False, "label": "仅 MP3 (128k)"},
}


def build_variant_config(mode, links=None):
    """派生临时配置；links 非 None 时覆盖 link: 列表（关注列表批量用）。"""
    spec = MODES[mode]
    cfg = yaml.safe_load(open(CONFIG_FILE, encoding="utf-8"))
    cfg["video_quality"] = spec["video_quality"]
    cfg["redownload_missing_files"] = spec["redownload"]
    if links:
        cfg["link"] = list(links)
    out = os.path.join(BASE, f"_cfg_dy_{mode}.yml")
    with open(out, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, sort_keys=False)
    return out


def run_downloader(variant_cfg):
    py = os.path.join(BASE, ".venv", "Scripts", "python.exe")
    r = subprocess.call([py, os.path.join(BASE, "run.py"), "-c", variant_cfg], cwd=BASE)
    return r


def convert_tree(mode):
    """扫描下载根目录，补转缺 MP3 的 MP4；audio 模式转完删 MP4。"""
    spec = MODES[mode]
    cfg = yaml.safe_load(open(CONFIG_FILE, encoding="utf-8"))
    root = cfg.get("path") or os.path.join(BASE, "Downloaded")
    ffmpeg = resolve_ffmpeg()
    converted = deleted = 0
    for mp4 in glob.glob(os.path.join(root, "**", "*.mp4"), recursive=True):
        mp3 = mp4[:-4] + ".mp3"
        if os.path.exists(mp3):
            continue
        try:
            r = subprocess.call(
                [ffmpeg, "-y", "-loglevel", "error", "-i", mp4,
                 "-vn", "-acodec", "libmp3lame", "-b:a", f"{AUDIO_KBPS}k", mp3]
            )
        except OSError as exc:
            # 没装 ffmpeg 时别把整轮下载判成失败：MP3 只是收尾步骤，
            # MP4 已经在盘上了，提示清楚让用户自己补转即可。
            print(f"  [warn] 找不到可用的 ffmpeg({ffmpeg})，跳过 MP3 转换: {exc}")
            break
        if r != 0 or not os.path.exists(mp3):
            print(f"  [warn] MP3 转换失败: {os.path.basename(mp4)}")
            continue
        converted += 1
        print(f"  [mp3] {os.path.basename(mp3)}")
        if not spec["keep_mp4"]:
            os.remove(mp4)
            deleted += 1
            # 空了的一层目录顺手删掉（保持 audio 模式目录干净）
            folder = os.path.dirname(mp4)
            try:
                if not os.listdir(folder):
                    os.rmdir(folder)
            except OSError:
                pass
    return converted, deleted


def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    if mode not in MODES:
        print(f"用法: dy_run.py <{'|'.join(MODES)}>  (收到: {mode!r})")
        sys.exit(1)
    spec = MODES[mode]
    print(f"==== dy_run [{mode}] {spec['label']} ====")

    variant = build_variant_config(mode)
    rc = run_downloader(variant)
    if rc != 0:
        print(f"[warn] 下载器退出码 {rc}，继续尝试转换已下载的部分")

    converted, deleted = convert_tree(mode)
    print(f"==== 完成: 新转 MP3 {converted} 个" + (f"，删除 MP4 {deleted} 个" if deleted else "") + " ====")


if __name__ == "__main__":
    main()
