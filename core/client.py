"""
HTTP 客户端模块

基于 requests.Session，支持 Cookie 注入和 HTTP 代理。
"""

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

    def __init__(self, account: AccountConfig, proxy: Optional[ProxyConfig] = None):
        self.account = account
        self.proxy = proxy
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

        self._setup_cookies()
        if proxy and proxy.enabled and proxy.http:
            self._setup_proxy()

    def _setup_cookies(self) -> None:
        """解析 cookie 字符串并注入到 session"""
        cookie_str = self.account.cookie.strip().rstrip(";")
        jar = RequestsCookieJar()
        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" not in item:
                continue
            key, _, value = item.partition("=")
            jar.set(key.strip(), value.strip(), domain="e-hentai.org")
            jar.set(key.strip(), value.strip(), domain="forums.e-hentai.org")
            jar.set(key.strip(), value.strip(), domain="exhentai.org")
        self.session.cookies = jar

    def _setup_proxy(self) -> None:
        """配置 HTTP 代理"""
        proxy_url = self.proxy.http.strip()
        if proxy_url:
            self.session.proxies = {
                "http": proxy_url,
                "https": proxy_url,
            }

    @property
    def proxy_str(self) -> str:
        if self.proxy and self.proxy.enabled and self.proxy.http:
            return self.proxy.http.strip()
        return ""

    def get(self, url: str, **kwargs) -> requests.Response:
        """发送 GET 请求"""
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """发送 POST 请求"""
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        return self.session.post(url, **kwargs)
