# -*- coding: utf-8 -*-
"""dy_setdate: 交互式设置/清除抖音下载的时间窗口（写 config.yml 的 start_time/end_time）。

- 只下载 create_time 落在窗口内的作品：start_time 当天含、end_time 当天含。
- 留空回车 = 清除该端。两端都清 = 不限量。
- 用正则改写原始文本，config.yml 里的注释原样保留。
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE, "config.yml")


def set_field(text, key, value):
    """替换 config.yml 里 `key: "xxx"` 行的值，保留缩进与注释。"""
    pat = re.compile(r'(^%s:\s*)"[^"]*"' % key, re.M)
    if pat.search(text):
        return pat.sub(lambda m: '%s"%s"' % (m.group(1), value), text, count=1)
    # 字段不存在则追加到文件头
    return '%s: "%s"\n' % (key, value) + text


def read_current():
    """读出 config.yml 里当前的时间窗设置。"""
    text = open(CONFIG_FILE, encoding="utf-8").read()
    cur = {}
    for key in ("start_time", "end_time"):
        m = re.search(r'^%s:\s*"([^"]*)"' % key, text, re.M)
        cur[key] = (m.group(1) if m else "") or ""
    return cur


CLEAR_WORDS = {"0", "none", "clear", "all", "不限", "清除", "-"}


def main():
    cur = read_current()
    print("=" * 56)
    print("  Douyin time window - GLOBAL switch (config.yml)")
    print("  当前设置: start_time=%s  end_time=%s"
          % (cur["start_time"] or "(无=不限)", cur["end_time"] or "(无=不限)"))
    print("  设一次即对所有 up 主生效，一直保留到下回修改")
    print("  格式 YYYY-MM-DD (含当天)；回车 = 保持不变；填 0 = 清除该端")
    print("=" * 56)
    s = input("start_time (从此日期起下载) [%s]: " % (cur["start_time"] or "不限")).strip()
    e = input("end_time   (到此日期止下载) [%s]: " % (cur["end_time"] or "不限")).strip()
    if not s:                      # 回车 = 保持原值
        s = cur["start_time"]
    elif s.lower() in CLEAR_WORDS:  # 0/clear/= 清除
        s = ""
    if not e:
        e = cur["end_time"]
    elif e.lower() in CLEAR_WORDS:
        e = ""
    for v, label in ((s, "start_time"), (e, "end_time")):
        if v and not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            print("[ERROR] %s 格式不对: %r (应为 YYYY-MM-DD)，未修改。" % (label, v))
            sys.exit(1)

    text = open(CONFIG_FILE, encoding="utf-8").read()
    text = set_field(text, "start_time", s)
    text = set_field(text, "end_time", e)
    open(CONFIG_FILE, "w", encoding="utf-8").write(text)

    if not s and not e:
        print("[OK] 时间窗已清除 = 不限量（下全部作品）")
    else:
        print("[OK] 已写入: start_time=%s  end_time=%s" % (s or "(无)", e or "(无)"))
    print("     这是全局开关：换 up 主照样生效，直到你下次修改")


if __name__ == "__main__":
    main()
