# utils/console.py
"""Console utilities for Unicode/CP932 compatibility"""

import os
import sys
import locale

def init_stdout_utf8():
    """Initialize UTF-8 output, return success status"""
    # 1) 環境でUTF-8を指示（副作用小）
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        # 2) 3.7+ は reconfigure がある
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        return True
    except Exception:
        return False

def supports_emoji() -> bool:
    """Check if current console supports emoji output"""
    # Windows の cp932 等では基本NG
    enc = (sys.stdout.encoding or "") or locale.getpreferredencoding(False)
    return "UTF-8" in enc.upper()

def safe_print(msg: str, fallback: str = None):
    """UTF-8で出せない場合は絵文字を落として出力"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(fallback or _strip_emoji(msg))

def _strip_emoji(s: str) -> str:
    """最低限：BMP以外と明らかな絵文字域を削る（厳密でなくてOK）"""
    return "".join(ch for ch in s if ord(ch) <= 0xFFFF and not (0x1F300 <= ord(ch) <= 0x1FAFF))