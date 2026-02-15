"""
NovaIC Backend - 兼容入口
Tauri 使用 python -m novaic_main 调用，本文件转发到 main_novaic
"""

from main_novaic import main

if __name__ == "__main__":
    main()
