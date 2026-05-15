"""
HTTP 客户端模块

基于 requests.Session，支持 Cookie 注入、HTTP 代理、
以及运行间 Cookie 持久化（对标 JHenTai 的 EHCookieManager）。
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
COOKIE_STORE_FILENAME = "Ehentai_Cookies.json"


class EhentaiClient:
    """Ehentai HTTP 客户端"""

    def __init__(
        self,
        account: AccountConfig,
        proxy: Optional[ProxyConfig] = None,
        config_dir: Optional[Path] = None,
    ):
        self.account = account
        self.proxy = proxy
        self._config_dir = config_dir or Path.cwd()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

        self._setup_cookies()
        if proxy and proxy.enabled and proxy.proxyurl:
            self._setup_proxy()

    @property
    def _store_path(self) -> Path:
        return self._config_dir / COOKIE_STORE_FILENAME

    # ─── Cookie 持久化 ───────────────────────────────────────

    def _load_persisted_cookies(self) -> dict[str, str]:
        """加载持久化 Cookie（按 usertag 隔离）"""
        try:
            if self._store_path.exists():
                data = json.loads(self._store_path.read_text(encoding="utf-8"))
                return data.get(self.account.usertag, {})
        except Exception:
            pass
        return {}

    def _session_cookie_dict(self) -> dict[str, str]:
        """从 session 提取当前有效 Cookie（主域优先，过滤 nw/datatags 等）"""
        result: dict[str, str] = {}
        for cookie in self.session.cookies:
            if cookie.domain != "e-hentai.org":
                continue
            if cookie.name in ("nw", "datatags"):
                continue
            if cookie.name == "__utmp":
                continue
            if cookie.name == "igneous" and cookie.value == "mystery":
                continue
            result[cookie.name] = cookie.value
        return result

    def save_cookies(self) -> None:
        """
        将会话 Cookie 持久化到磁盘。
        自动比对变化并输出日志。
        """
        all_data: dict[str, dict[str, str]] = {}
        try:
            if self._store_path.exists():
                all_data = json.loads(self._store_path.read_text(encoding="utf-8"))
        except Exception:
            pass

        tag = self.account.usertag
        old_cookies = all_data.get(tag, {})
        new_cookies = self._session_cookie_dict()

        added = {k: v for k, v in new_cookies.items() if k not in old_cookies}
        updated = {k: v for k, v in new_cookies.items()
                   if k in old_cookies and old_cookies[k] != v}
        removed = {k: old_cookies[k] for k in old_cookies if k not in new_cookies}

        if added:
            print(f"[Cookie] 新增: {', '.join(f'{k}={v[:8]}...' if len(v) > 8 else f'{k}={v}' for k, v in added.items())}")
        if updated:
            print(f"[Cookie] 更新: {', '.join(updated.keys())}")
        if removed:
            print(f"[Cookie] 移除: {', '.join(removed.keys())}")
        if not added and not updated and not removed:
            print("[Cookie] 无变化")

        all_data[tag] = new_cookies
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        self._store_path.write_text(
            json.dumps(all_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

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

        # 加载持久化的服务器下发 Cookie（如 sk）
        for key, value in self._load_persisted_cookies().items():
            if key in ("ipb_member_id", "ipb_pass_hash"):
                continue  # 不覆盖用户手动提供的
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
