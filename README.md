# Ehentai 黎明之时自动签到

从 [JHenTai](https://github.com/jiangtian616/JHenTai) 移植的 E-Hentai 黎明之时事件自动签到脚本，支持普通 Python 环境和青龙面板。

## 功能

- Cookie 登录（跳过服务器验证，仅本地校验格式）
- 自动检测并完成黎明之时事件签到
- **支持多账户**，通过 `usertag` 标识每个账户
- 支持 HTTP 代理
- 青龙版集成 notify.py 多平台通知推送
- 首次运行自动生成配置文件模板
- 提供普通版和青龙面板版两个入口

## 获取 Cookie

1. 登录 [E-Hentai](https://e-hentai.org) 或 [EXHentai](https://exhentai.org)
2. 按 `F12` 打开开发者工具 → Application → Cookies
3. 找到 `ipb_member_id` 和 `ipb_pass_hash` 的值
4. 组合为：`ipb_member_id=你的值; ipb_pass_hash=你的值`

## 配置文件

配置文件格式（普通版在脚本同目录，青龙版在 `/ql/data/config/`）：

```yaml
ehentai:
  # HTTP 代理配置（可选，国内用户需开启）
  proxy:
    enabled: true
    http: "http://172.17.0.1:7890"
  accounts:
    - cookie: "ipb_member_id=xxxxx; ipb_pass_hash=xxxxx"
      usertag: "主号"
    - cookie: "ipb_member_id=yyyyy; ipb_pass_hash=yyyyy"
      usertag: "小号"
```

- `cookie`: E-Hentai 的 Cookie 字符串
- `usertag`: 自定义标识名，用于日志和通知中区分账户

## 普通用户

### 环境要求

- Python 3.9+

### 安装

```bash
cd Ehentai_AutoSign
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### 运行

```bash
python ehentai_autosign.py
```

## 青龙面板

### 脚本依赖

青龙面板已预装 `requests` 和 `pyyaml`，本脚本额外的依赖需要在青龙面板中安装：

```bash
# 青龙面板 → 依赖管理 → Python3 → 新建依赖
beautifulsoup4
lxml
```

### 订阅

在青龙面板中通过 Repo 订阅添加本仓库，脚本会自动拉取到 `/ql/data/repo/` 下。

### 配置文件

配置文件需放置在 `/ql/data/config/Ehentai_UserConfig.yml`。

创建方式：
1. 青龙面板 → 配置文件 → 新建 `Ehentai_UserConfig.yml`
2. 或通过 SSH 上传到 `/ql/data/config/`

### 新建任务

拉取脚本后，青龙面板通过脚本头部注释自动识别：

- 脚本名称：`Ehentai黎明之时签到`
- cron 默认：`0 8 * * *`（每天早上 8 点）

### 通知推送

青龙版已集成 `notify.py`，签到结果自动推送到已配置的通知渠道。

通知内容精简为关键信息：
```
[代理] 已启用 HTTP 代理: http://172.17.0.1:7890
[信息] 主号 [结果] 今日无黎明之时事件
[信息] 小号 [结果] 签到成功! You gain 30 EXP, 2,100 Credits...
```

## 输出示例

多账户运行（普通版控制台）：

```
[Ehentai] 黎明之时签到脚本启动

[代理] 已启用 HTTP 代理: http://172.17.0.1:7890

[信息] 账户: 主号
[信息] Cookie 已验证（跳过服务器验证模式）
==================================================
  黎明之时签到成功！
  奖励详情: You gain 30 EXP, 2,100 Credits, 2,000 GP and 76 Hath!
==================================================

[信息] 账户: 小号
[信息] Cookie 已验证（跳过服务器验证模式）
[结果] 小号: 今日无黎明之时事件
```

## 文件结构

```
Ehentai_AutoSign/
├── core/
│   ├── config.py          # 配置加载、多账户解析
│   ├── client.py          # HTTP 客户端（Cookie + 代理）
│   └── dawn_event.py      # 签到核心逻辑
├── notify.py              # 青龙通知模块（多平台推送）
├── ehentai_autosign.py    # 普通版入口
├── ehentai_autosign_ql.py # 青龙面板版入口（集成通知）
├── requirements.txt
└── README.md
```

## 参考

本项目核心签到逻辑移植自 [JHenTai](https://github.com/jiangtian616/JHenTai) 的 `schedule_service.dart`、`eh_spider_parser.dart` 和 `login_page_logic.dart`。
