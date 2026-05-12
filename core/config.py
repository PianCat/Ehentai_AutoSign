"""
配置文件加载模块

校验 cookie 格式，首次运行时创建配置模板。
支持多账户列表，每个账户用 usertag 标识。
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import yaml

CONFIG_FILENAME = "Ehentai_UserConfig.yml"

CONFIG_TEMPLATE = """\
# Ehentai 自动签到配置
# 支持多账户，每个账户需填写 cookie 和标识名 usertag
# Cookie 格式: ipb_member_id=xxxxx; ipb_pass_hash=xxxxx
# 可选字段: igneous=xxxxx
ehentai:
  # HTTP 代理配置（可选，国内用户需开启）
  proxy:
    enabled: false
    http: "http://127.0.0.1:7890"
  accounts:
    - cookie: ""
      usertag: ""
"""

COOKIE_PATTERN = re.compile(r"ipb_member_id=(\w+).*ipb_pass_hash=(\w+)", re.DOTALL)


@dataclass
class ProxyConfig:
    enabled: bool = False
    http: str = ""


@dataclass
class AccountConfig:
    cookie: str = ""
    usertag: str = ""

    @property
    def ipb_member_id(self) -> str:
        m = COOKIE_PATTERN.search(self.cookie)
        return m.group(1) if m else ""


@dataclass
class AppConfig:
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    accounts: list[AccountConfig] = field(default_factory=list)


def _create_default_config(path: Path) -> None:
    """创建默认配置模板"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(CONFIG_TEMPLATE, encoding="utf-8")


def load_config(config_dir: Path) -> AppConfig:
    """
    加载配置文件，不存在则自动创建模板。

    config_dir: 配置文件所在目录
    返回 AppConfig；若无有效账户则退出。
    """
    path = config_dir / CONFIG_FILENAME

    if not path.exists():
        print(f"[配置] 配置文件不存在，已自动创建模板: {path}")
        _create_default_config(path)
        print("[配置] 请编辑配置文件填入 Cookie 后重新运行")
        sys.exit(0)

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    ehentai = data.get("ehentai", {})

    proxy_raw = ehentai.get("proxy", {}) or {}
    proxy = ProxyConfig(
        enabled=bool(proxy_raw.get("enabled", False)),
        http=proxy_raw.get("http", ""),
    )

    accounts_raw = ehentai.get("accounts", []) or []
    accounts = [
        AccountConfig(
            cookie=acct.get("cookie", "").strip(),
            usertag=acct.get("usertag", "").strip(),
        )
        for acct in accounts_raw
    ]

    config = AppConfig(proxy=proxy, accounts=accounts)

    valid_accounts = [a for a in config.accounts if a.cookie and a.usertag]
    if not valid_accounts:
        print("[错误] 未找到有效账户（cookie 和 usertag 均不能为空），请检查配置文件")
        sys.exit(1)

    config.accounts = valid_accounts
    return config


def validate_cookie(cookie: str) -> bool:
    """
    跳过验证模式：仅校验 cookie 中是否包含有效的 ipb_member_id 和
    ipb_pass_hash（非空且值不为 '0'）。
    """
    if not cookie:
        return False
    m = COOKIE_PATTERN.search(cookie)
    if not m:
        return False
    member_id = m.group(1)
    pass_hash = m.group(2)
    return member_id != "0" and pass_hash != "0"
