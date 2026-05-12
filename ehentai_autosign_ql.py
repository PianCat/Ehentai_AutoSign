'''
cron: 0 8 * * *
new Env('Ehentai黎明之时签到')
'''

"""
Ehentai 黎明之时自动签到脚本（青龙面板版）

使用 Cookie 登录（跳过验证），自动检测并完成黎明之时事件签到。
支持多账户，配置文件位于 /ql/data/config/Ehentai_UserConfig.yml。
集成青龙 notify.py 通知模块。
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config import load_config, validate_cookie
from core.client import EhentaiClient
from core.dawn_event import check_dawn_event

CONFIG_DIR = Path("/ql/data/config")

logs: list[str] = []
_notify_lines: list[str] = []


def log(msg: str) -> None:
    """记录完整日志到控制台"""
    print(msg)
    logs.append(msg)


def notify_line(msg: str) -> None:
    """记录通知摘要"""
    _notify_lines.append(msg)


def send_notify(success: bool, summary: str) -> None:
    """通过青龙通知模块发送精简推送"""
    try:
        import notify

        title = "Ehentai黎明之时签到 - 成功" if success else "Ehentai黎明之时签到 - 失败"
        content = "\n".join(_notify_lines) + f"\n{summary}"
        notify.send(title, content)
    except Exception:
        log("[通知] 发送推送失败（notify 模块未配置或调用异常）")


def main():
    log("[Ehentai] 黎明之时签到脚本启动（青龙面板版）")

    try:
        config = load_config(CONFIG_DIR)
    except SystemExit:
        send_notify(False, "配置文件缺失或账户为空，请检查 /ql/data/config/Ehentai_UserConfig.yml")
        sys.exit(1)

    if config.proxy.enabled and config.proxy.http:
        notify_line(f"[代理] 已启用 HTTP 代理: {config.proxy.http}")

    overall_success = True
    result_summary: list[str] = []

    for account in config.accounts:
        tag = account.usertag

        if not validate_cookie(account.cookie):
            log(f"[错误] 账户 {tag} Cookie 格式无效")
            notify_line(f"[信息] {tag} [错误] Cookie 格式无效")
            overall_success = False
            continue

        log(f"[信息] 账户: {tag}")

        try:
            client = EhentaiClient(account, proxy=config.proxy)
        except Exception:
            log(f"[错误] 账户 {tag} 初始化客户端失败: {traceback.format_exc()}")
            notify_line(f"[信息] {tag} [错误] 初始化客户端失败")
            overall_success = False
            continue

        try:
            dawn_info = check_dawn_event(client)
        except Exception:
            log(f"[错误] 账户 {tag} 签到请求异常: {traceback.format_exc()}")
            notify_line(f"[信息] {tag} [错误] 签到请求异常")
            overall_success = False
            continue

        if dawn_info:
            result = f"[结果] {tag}: 签到成功! {dawn_info}"
            log(result)
            notify_line(f"[信息] {tag} [结果] 签到成功! {dawn_info}")
        else:
            result = f"[结果] {tag}: 今日无黎明之时事件"
            log(result)
            notify_line(f"[信息] {tag} [结果] 今日无黎明之时事件")

        result_summary.append(result)

    send_notify(overall_success, "\n".join(result_summary))


if __name__ == "__main__":
    main()
