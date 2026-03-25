"""编码处理工具模块"""

import os
import sys


def setup_utf8_encoding():
    """设置 UTF-8 编码"""
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')


# 模块加载时自动设置编码
setup_utf8_encoding()
