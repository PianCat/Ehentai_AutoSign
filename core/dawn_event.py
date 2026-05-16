"""
黎明之时事件签到模块

对标 JHenTai 的 checkEHEvent()：只访问 news.php 检测 #eventpane。
Cookie 持久化由 client 层管理，sk 缺失时自动从 home.php 引导获取。
"""

from typing import Optional

from bs4 import BeautifulSoup

from .client import EhentaiClient

EHOME_URL = "https://e-hentai.org/home.php"
ENEWS_URL = "https://e-hentai.org/news.php"


class DawnResult:
    def __init__(self, dawn_info: Optional[str] = None, error: Optional[str] = None):
        self.dawn_info = dawn_info
        self.error = error

    @property
    def success(self) -> bool:
        return self.dawn_info is not None and self.error is None

    @property
    def no_event(self) -> bool:
        return self.dawn_info is None and self.error is None

    @property
    def failed(self) -> bool:
        return self.error is not None


DAWN_THREE = {"Credits", "GP", "Hath"}
DAWN_FOUR = {"Credits", "GP", "Hath", "EXP"}


def _extract_dawn_info(html: str) -> Optional[str]:
    """
    从 #eventpane 中提取黎明之时奖励文本。

    不依赖固定位置选择器，改用关键词锚点匹配：
    1. 优先：同时包含 Credits、GP、Hath 三者
    2. 降级：包含 Credits、GP、Hath 中任意一个
    3. 最终降级：包含 Credits、GP、Hath、EXP 中任意一个
    """
    soup = BeautifulSoup(html, "lxml")
    event_pane = soup.select_one("#eventpane")
    if event_pane is None:
        return None

    candidates: list[tuple[int, str]] = []

    for p in event_pane.select("p"):
        text = p.get_text(strip=True)
        if not text:
            continue

        present_three = sum(1 for kw in DAWN_THREE if kw in text)
        present_four = sum(1 for kw in DAWN_FOUR if kw in text)

        if present_three == 3:
            # 三者全命中 → 最高优先级，直接返回
            return text

        if present_three >= 1:
            # 命中至少一个 Credits/GP/Hath → 优先级 2
            candidates.append((2, text))
        elif present_four >= 1:
            # 命中至少一个 Credits/GP/Hath/EXP → 优先级 3
            candidates.append((3, text))

    # 按优先级排序（数字越小越优先）
    candidates.sort(key=lambda x: x[0])
    if candidates:
        return candidates[0][1]

    return None


def _bootstrap_sk(client: EhentaiClient) -> bool:
    """首次运行：访问 home.php 获取 sk 等会话 Cookie"""
    try:
        resp = client.get(EHOME_URL)
        resp.raise_for_status()
        client.save_cookies()
        print("[会话] 已从 home.php 引导获取 sk Cookie")
        return True
    except Exception as e:
        print(f"[警告] 引导获取 sk 失败: {e}")
        return False


def check_dawn_event(client: EhentaiClient) -> DawnResult:
    """
    检测黎明之时事件（仅访问 news.php）。
    若缺失 sk cookie 则自动从 home.php 引导获取后重试。
    """
    # 首次运行无 sk → bootstrap
    if not client.has_sk:
        _bootstrap_sk(client)

    try:
        resp = client.get(ENEWS_URL)
        resp.raise_for_status()
    except Exception as e:
        return DawnResult(error=f"访问 news.php 失败: {e}")

    dawn_info = _extract_dawn_info(resp.text)
    if dawn_info is not None:
        return DawnResult(dawn_info=dawn_info)

    return DawnResult()


def format_dawn_result(dawn_info: str) -> str:
    return "\n".join([
        "=" * 50,
        "  黎明之时签到成功！",
        f"  奖励详情: {dawn_info}",
        "=" * 50,
    ])
