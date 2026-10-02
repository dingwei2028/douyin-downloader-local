# -*- coding: utf-8 -*-
"""抖音: 视频链接 -> 反推 up 主主页 -> 写回 config.yml 的 link:（供 run_dy.bat 使用）。

用法：
  1. 推荐流程：把任意一个该 up 主的视频链接粘进 C:\\Github\\douyin-downloader\\dy_urls.txt
     （或 finddyUP.bat 提示时直接粘贴），双击 finddyUP.bat ——
     脚本反推作者主页后【只替换 config.yml 里 link: 的第一条】，其余配置原样保留。
  2. 命令行：python dy_find_up.py <视频链接>

依赖 douyin-downloader 自身的签名/风控机制（a_bogus + browser_fallback），
不需要 yt-dlp 的 cookies.txt。
"""
import asyncio
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

CONFIG_FILE = os.path.join(BASE, "config.yml")
URLS_FILE = os.path.join(BASE, "dy_urls.txt")

from config.config_loader import ConfigLoader  # noqa: E402
from core.api_client import DouyinAPIClient  # noqa: E402
from core.url_parser import URLParser  # noqa: E402
from utils.validators import is_short_url, normalize_short_url  # noqa: E402


def read_url_from_args_or_urls(argv):
    # 1) 命令行参数优先
    if len(argv) > 1 and argv[1].strip():
        return argv[1].strip().strip('"').strip("'")
    # 2) 读 urls.txt 第一条抖音链接（与 findyt.py 读 YouTube 链接对齐）
    if os.path.exists(URLS_FILE):
        for line in open(URLS_FILE, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line and not line.startswith("#") and "douyin.com" in line:
                print(f"[dy_urls.txt] 读到: {line}")
                return line.strip('"').strip("'")
    return None


def extract_aweme_id(url):
    parsed = URLParser.parse(url)
    if parsed and parsed.get("aweme_id"):
        return parsed["aweme_id"]
    # jingxuan?modal_id= 等形态 URLParser 不认，兜底正则
    m = re.search(r"(?:modal_id|video_id)=(\d+)", url) or re.search(
        r"douyin\.com/(?:video|note)/(\d+)", url
    )
    return m.group(1) if m else None


async def resolve_author(url):
    cfg = ConfigLoader(CONFIG_FILE)
    cookies = cfg.get_cookies()
    proxy = cfg.get("proxy") or None
    browser_cfg = cfg.get("browser_fallback") or {}
    # 与 cli/main.py 一致：aweme/detail 自 2026-09 起被 Argus 门禁，详情只能
    # 让真浏览器页内发起；这里把浏览器兜底选项（headless / 登录 Cookie）带上。
    async with DouyinAPIClient(
        cookies,
        proxy=proxy,
        browser_include_login_cookies=bool(browser_cfg.get("inject_login_cookies", False)),
        browser_fallback_options=browser_cfg,
    ) as api:
        if is_short_url(url):
            resolved = await api.resolve_short_url(normalize_short_url(url))
            if resolved:
                url = resolved
                print(f"[expand] 短链 -> {url.split('?')[0]}")
        aweme_id = extract_aweme_id(url)
        if not aweme_id:
            return None, "无法从链接里提取视频 id"
        detail = await api.get_video_detail(aweme_id)
        if not detail:
            return None, "拿不到视频详情（cookie 过期？或浏览器兜底不可用，检查 playwright）"
        author = detail.get("author") or {}
        sec_uid = author.get("sec_uid")
        nickname = author.get("nickname") or author.get("unique_id") or sec_uid
        if not sec_uid:
            return None, f"详情里没有 sec_uid（title={detail.get('desc', '')[:30]}）"
        return {"sec_uid": sec_uid, "nickname": nickname,
                "user_url": f"https://www.douyin.com/user/{sec_uid}"}, None


def rewrite_config_link(user_url):
    """只替换 config.yml 里 link: 下第一条 - 链接，其余内容原样保留。"""
    text = open(CONFIG_FILE, encoding="utf-8").read()
    # 匹配 link: 之后的第一条非注释列表项
    new_text, n = re.subn(
        r"(?m)^(link:\s*\n(?:\s*#[^\n]*\n)*)\s*-[ \t]+\S.*$",
        lambda m: m.group(1) + "  - " + user_url,
        text,
        count=1,
    )
    if n == 0:
        return False
    open(CONFIG_FILE, "w", encoding="utf-8").write(new_text)
    return True


def main():
    url = read_url_from_args_or_urls(sys.argv)
    if not url:
        print("[ERROR] 没找到抖音链接：请粘贴到 dy_urls.txt，或作为命令行参数传入")
        sys.exit(1)

    info, err = asyncio.run(resolve_author(url))
    if err:
        print(f"[ERROR] {err}")
        sys.exit(2)

    print(f"[OK] 作者: {info['nickname']}")
    print(f"[OK] 主页: {info['user_url']}")
    if rewrite_config_link(info["user_url"]):
        print(f"[OK] 已写回 {CONFIG_FILE} 的 link:")
        print("     现在双击 run_dy.bat 即可下载该 up 主全部作品")
    else:
        print("[WARN] 没找到 config.yml 的 link: 条目，请手动把上面主页链接填进去")


if __name__ == "__main__":
    main()
