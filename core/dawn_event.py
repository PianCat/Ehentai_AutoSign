"""
黎明之时事件签到模块

从 e-hentai.org/news.php 获取事件信息并完成签到。
"""

from typing import Optional

from bs4 import BeautifulSoup

from .client import EhentaiClient

ENEWS_URL = "https://e-hentai.org/news.php"


def check_dawn_event(client: EhentaiClient) -> Optional[str]:
    """
    检查黎明之时事件，返回奖励文本；无事件时返回 None。

    对应 JHenTai 中 EHSpiderParser.newsPage2Event 的逻辑：
    - 查找 HTML 中 id="eventpane" 的元素
    - 提取 div > p:nth-child(2) 的文本作为奖励信息
    """
    try:
        resp = client.get(ENEWS_URL)
        resp.raise_for_status()
    except Exception as e:
        print(f"[错误] 访问 news.php 失败: {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    event_pane = soup.select_one("#eventpane")
    if event_pane is None:
        print("[信息] 当前无黎明之时事件")
        return None

    dawn_text = None
    p_elements = event_pane.select("div > p")
    if len(p_elements) >= 2:
        dawn_text = p_elements[1].get_text(strip=True)

    return dawn_text


def format_dawn_result(dawn_info: str) -> str:
    """格式化签到结果为日志字符串"""
    lines = [
        "=" * 50,
        "  黎明之时签到成功！",
        f"  奖励详情: {dawn_info}",
        "=" * 50,
    ]
    return "\n".join(lines)
