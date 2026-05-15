"""
HTTP 客户端模块

基于 requests.Session，支持 Cookie 注入、HTTP 代理、
会话 Cookie 回写到 AccountConfig.session（对标 JHenTai 的 EHCookieManager）。
"""

import json
from pathlib import Path
from typing import Optional

import requests
from requests.cookies import RequestsCookieJar

from .config import AccountConfig, ProxyConfig

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

DEFAULT_TIMEOUT = 30


class EhentaiClient:
    """Ehentai HTTP 客户端"""

    def __init__(
        self,
        account: AccountConfig,
        proxy: Optional[ProxyConfig] = None,
    ):
        self.account = account
        self.proxy = proxy
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

        self._setup_cookies()
        if proxy and proxy.enabled and proxy.proxyurl:
            self._setup_proxy()

    # ─── Cookie 持久化 ───────────────────────────────────────

    def _session_cookie_dict(self) -> dict[str, str]:
        """从 session 提取当前有效 Cookie（按名称去重，过滤 nw/datatags 等）"""
        result: dict[str, str] = {}
        for cookie in self.session.cookies:
            if cookie.name in ("nw", "datatags"):
                continue
            if cookie.name == "__utmp":
                continue
            if cookie.name == "igneous" and cookie.value == "mystery":
                continue
            if cookie.name not in result:
                result[cookie.name] = cookie.value
        return result

    def save_cookies(self) -> None:
        """
        比对 session 与 account.session，输出变化并更新。
        由主脚本调用 save_config() 最终回写 YAML。
        """
        old = self.account.session
        new = self._session_cookie_dict()

        added = {k: v for k, v in new.items() if k not in old}
        updated = {k: v for k, v in new.items() if k in old and old[k] != v}
        removed = {k: old[k] for k in old if k not in new}

        if added:
            print(f"[Cookie] 新增: {', '.join(f'{k}={v[:8]}...' if len(v) > 8 else f'{k}={v}' for k, v in added.items())}")
        if updated:
            print(f"[Cookie] 更新: {', '.join(updated.keys())}")
        if removed:
            print(f"[Cookie] 移除: {', '.join(removed.keys())}")
        if not added and not updated and not removed:
            print("[Cookie] 无变化")

        self.account.session = new

    @property
    def has_sk(self) -> bool:
        """是否已持有 sk cookie"""
        return any(c.name == "sk" and c.value for c in self.session.cookies)

    # ─── 内部初始化 ──────────────────────────────────────────

    def _setup_cookies(self) -> None:
        jar = RequestsCookieJar()

        # JHenTai 硬编码默认 cookie
        for domain in ("e-hentai.org", "forums.e-hentai.org", "exhentai.org"):
            jar.set("nw", "1", domain=domain)
            jar.set("datatags", "1", domain=domain)

        # 用户提供的 Cookie
        cookie_str = self.account.cookie.strip().rstrip(";")
        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" not in item:
                continue
            key, _, value = item.partition("=")
            for domain in ("e-hentai.org", "forums.e-hentai.org", "exhentai.org"):
                jar.set(key.strip(), value.strip(), domain=domain)

        # 加载持久化的会话 Cookie（如 sk）
        for key, value in self.account.session.items():
            if key in ("ipb_member_id", "ipb_pass_hash"):
                continue
            for domain in ("e-hentai.org", "forums.e-hentai.org", "exhentai.org"):
                jar.set(key, value, domain=domain)

        self.session.cookies = jar

    def _setup_proxy(self) -> None:
        proxy_url = self.proxy.proxyurl.strip()
        if proxy_url:
            self.session.proxies = {
                "http": proxy_url,
                "https": proxy_url,
            }

    @property
    def proxy_str(self) -> str:
        if self.proxy and self.proxy.enabled and self.proxy.proxyurl:
            return self.proxy.proxyurl.strip()
        return ""

    def get(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        return self.session.post(url, **kwargs)
