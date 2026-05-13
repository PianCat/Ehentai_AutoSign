"""
Ehentai 黎明之时自动签到脚本

使用 Cookie 登录（跳过验证），自动检测并完成黎明之时事件签到。
支持多账户，配置文件 Ehentai_UserConfig.yml 位于本脚本同目录下。
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config import load_config, validate_cookie
from core.client import EhentaiClient
from core.dawn_event import check_dawn_event, format_dawn_result

CONFIG_DIR = Path(__file__).resolve().parent


def main():
    print("[Ehentai] 黎明之时签到脚本启动\n")

    config = load_config(CONFIG_DIR)

    if config.proxy.enabled and config.proxy.proxyurl:
        print(f"[代理] 已启用 HTTP 代理: {config.proxy.proxyurl}\n")

    for account in config.accounts:
        tag = account.usertag
        print(f"[信息] 账户: {tag}")

        if not validate_cookie(account.cookie):
            print(f"[错误] 账户 {tag} Cookie 格式无效，跳过\n")
            continue

        print("[信息] Cookie 已验证（跳过服务器验证模式）")

        try:
            client = EhentaiClient(account, proxy=config.proxy)
        except Exception:
            print(f"[错误] 初始化客户端失败: {traceback.format_exc()}\n")
            continue

        try:
            dawn_info = check_dawn_event(client)
        except Exception:
            print(f"[错误] 签到请求异常: {traceback.format_exc()}\n")
            continue

        if dawn_info:
            print(format_dawn_result(dawn_info))
        else:
            print(f"[结果] {tag}: 今日无黎明之时事件")
        print()


if __name__ == "__main__":
    main()
