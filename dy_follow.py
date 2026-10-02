# -*- coding: utf-8 -*-
"""抖音关注列表批量：dy_follow.py [video|720|audio] [名字过滤词] [--max-users N]

解决「douyin.com/follow 页面没有单独视频链接」的问题：
不走页面链接，直接用登录态（config.yml 的 cookies）调关注列表 API，
把所有关注（或名字含过滤词的）的 up 主主页拼成批量链接，交给 dy_run 下载。

用法示例：
  python dy_follow.py video              # 全部关注，最高画质 MP4+MP3
  python dy_follow.py audio 访谈          # 只下名字含"访谈"的 up 主，仅 MP3
  python dy_follow.py 720 --max-users 3  # 先试前 3 个关注，720p
"""
import asyncio
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import dy_run  # noqa: E402
from config.config_loader import ConfigLoader  # noqa: E402
from core.api_client import DouyinAPIClient  # noqa: E402

MAX_FOLLOWS = 500  # 安全上限


def parse_args(argv):
    mode = "video"
    filt = None
    max_users = None
    rest = list(argv[1:])
    if rest and rest[0].lower() in dy_run.MODES:
        mode = rest.pop(0).lower()
    while rest:
        a = rest.pop(0)
        if a == "--max-users":
            max_users = int(rest.pop(0))
        elif a.startswith("--max-users="):
            max_users = int(a.split("=", 1)[1])
        else:
            filt = a
    return mode, filt, max_users


def fetch_followings(cookies, proxy):
    """翻页拉全关注列表，返回 [(nickname, sec_uid), ...]"""
    async def _run():
        async with DouyinAPIClient(cookies, proxy=proxy) as api:
            me = await api.get_self_info()
            if not me:
                return None, "拿不到登录用户信息（sessionid 过期？重导 cookie）"
            my_uid = me.get("sec_uid")
            print(f"[self] {me.get('nickname')}")
            follows, max_time, has_more = [], 0, True
            while has_more and len(follows) < MAX_FOLLOWS:
                page = await api.get_following_page(my_uid, max_time=max_time, count=20)
                items = page.get("items") or []
                for it in items:
                    su = it.get("sec_uid")
                    if su:
                        follows.append((it.get("nickname") or su, su))
                has_more = bool(page.get("has_more"))
                max_time = int(page.get("min_time") or 0)
                print(f"  ... 已拉取 {len(follows)} 个关注 (has_more={has_more})")
            return follows, None
    return asyncio.run(_run())


def main():
    mode, filt, max_users = parse_args(sys.argv)
    cfg = ConfigLoader(dy_run.CONFIG_FILE)
    follows, err = fetch_followings(cfg.get_cookies(), cfg.get("proxy"))
    if err:
        print(f"[ERROR] {err}")
        sys.exit(2)
    if filt:
        follows = [(n, s) for n, s in follows if filt in n]
    if max_users:
        follows = follows[:max_users]
    if not follows:
        print("[ERROR] 过滤后没有匹配的关注")
        sys.exit(1)

    print(f"\n==== 共 {len(follows)} 个 up 主（模式: {dy_run.MODES[mode]['label']}）====")
    for i, (n, _) in enumerate(follows, 1):
        print(f"  {i:3d}. {n}")
    ans = input(f"\n开始下载这 {len(follows)} 个 up 主的作品? [Y/N]: ").strip().lower()
    if ans not in ("", "y", "yes"):
        print("已取消")
        return

    links = [f"https://www.douyin.com/user/{su}" for _, su in follows]
    variant = dy_run.build_variant_config(mode, links=links)
    rc = dy_run.run_downloader(variant)
    if rc != 0:
        print(f"[warn] 下载器退出码 {rc}，继续转换已下载的部分")
    converted, deleted = dy_run.convert_tree(mode)
    print(f"==== 完成: 新转 MP3 {converted} 个" + (f"，删除 MP4 {deleted} 个" if deleted else "") + " ====")


if __name__ == "__main__":
    main()
