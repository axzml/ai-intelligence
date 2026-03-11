[English](README.md) | 中文

# AI 情报系统 (AIS)

> 在线演示：[contents.voxlinkai.com](https://contents.voxlinkai.com)

一个 OpenClaw 技能包，构建全自动 AI 新闻情报流水线 — 采集、分析、通知、日报、查询 — 全部由 LLM 驱动的 Agent 技能完成。

## 功能概览

```
17:00  ais-collect   → 从 RSS、Hacker News、X/Twitter、GitHub Trending 采集
17:30  ais-analyze   → LLM 聚类分析，生成评分事件
18:00  ais-notify    → Telegram 推送高分事件（≥ 7 分）
19:00  ais-report    → 生成并邮件发送 HTML 日报
随时    ais-query     → 自然语言查询情报知识库
```

## 技能列表

| 技能 | 触发方式 | 说明 |
|------|----------|------|
| `ais-collect` | 定时 17:00 | 多源数据采集（RSS、HN、X、GitHub） |
| `ais-analyze` | 定时 17:30 | LLM 事件聚类、评分（1-10）、分类 |
| `ais-notify` | 定时 18:00 | Telegram 即时推送高分事件 |
| `ais-report` | 定时 19:00 | 每日 HTML/文本邮件报告（Resend SMTP） |
| `ais-query` | 按需触发 | 自然语言知识库查询 |

## 快速开始

### 前置条件

- 已安装并配置 [OpenClaw](https://openclaw.com)
- Python 3.8+
- SQLite3
- （可选）Resend 账号，用于邮件日报
- （可选）通过 OpenClaw 绑定的 Telegram Bot，用于即时通知

### 1. 安装技能

克隆仓库：
```bash
git clone https://github.com/axzml/ai-intelligence.git ~/ai-intelligence
```

然后通过以下两种方式之一将技能安装到 OpenClaw。

**方式 A：复制到 OpenClaw 默认技能目录**

```bash
cp -r ~/ai-intelligence/skills/ais-* ~/.openclaw/workspace/skills/
```

验证技能是否被识别 — 向 OpenClaw 提问：

```
你有哪些技能？能看到 ais-collect、ais-analyze、ais-notify、ais-report、ais-query 吗？
```

OpenClaw 应列出全部 5 个 `ais-*` 技能。如果没有，检查目录结构是否正确：每个技能文件夹下应包含一个 `SKILL.md` 文件。

**方式 B：在 `openclaw.json` 中添加自定义技能路径**

编辑 OpenClaw 配置文件（通常位于 `~/.openclaw/openclaw.json`），添加 `skills` 字段指向本仓库的 skills 目录：

```json
{
  "skills": {
    "load": {
      "extraDirs": ["/home/<YOUR_USER_NAME>/ai-intelligence/skills"],
      "watch": true
    }
  }
}
```

将 `<YOUR_USER_NAME>` 替换为你的实际系统用户名。`watch: true` 选项使 OpenClaw 在技能文件变更时自动重新加载。

### 2. 初始化数据库

```bash
python scripts/init_db.py
```

### 3. 配置数据源

编辑 `config/rss_feeds.json`，自定义 RSS 订阅源、HN 关键词、X/Twitter 账号和 GitHub Trending 过滤器。

### 4. 配置系统参数

编辑 `config/settings.json`：
- `scoring.user_interests` — 你的兴趣标签，用于相关性评分
- `schedule` — 调整流水线时间
- `webapp.domain` — Web 仪表盘域名（如果部署 webapp）

### 5. 配置邮件（可选）

```sql
sqlite3 ~/ai-intelligence/data/intelligence.db
UPDATE config SET value = '你的-resend-api-key' WHERE key = 'resend_api_key';
UPDATE config SET value = 'noreply@yourdomain.com' WHERE key = 'email_sender';
UPDATE config SET value = 'you@example.com' WHERE key = 'email_recipient';
```

### 6. 设置定时任务

```bash
bash scripts/setup_cron.sh
```

或手动添加到 crontab（时间为服务器时区）：
```cron
0 17 * * * openclaw run ais-collect
30 17 * * * openclaw run ais-analyze
0 18 * * * openclaw run ais-notify
0 19 * * * openclaw run ais-report
```

### 7. 部署 Web 仪表盘（可选）

参见 `deploy/SERVER_DEPLOY_GUIDE.md` 了解 Nginx + systemd 部署。

```bash
cd webapp
pip install -r requirements.txt
python app.py
```

## 项目结构

```
├── skills/                  # OpenClaw Agent 技能（核心）
│   ├── ais-collect/         # 4 源数据采集
│   ├── ais-analyze/         # LLM 分析与事件生成
│   ├── ais-notify/          # Telegram 通知
│   ├── ais-report/          # 每日邮件报告
│   └── ais-query/           # 自然语言查询
├── config/
│   ├── settings.json        # 系统配置
│   └── rss_feeds.json       # 数据源定义
├── scripts/
│   ├── init_db.py           # 数据库初始化
│   └── setup_cron.sh        # 定时任务安装
├── heartbeat/
│   └── HEARTBEAT.md         # 系统健康检查清单
├── webapp/                  # Flask Web 仪表盘
└── deploy/                  # 服务器部署配置
```

## 心跳检测（健康监控）

`heartbeat/HEARTBEAT.md` 定义了一份检查清单，OpenClaw 可定期执行以监控系统健康状态：

- 检测未处理条目积压（raw_items 堆积）
- 发现有高分事件未推送通知
- 日报未按时生成时发出警告
- 报告数据源采集错误

启用方法 — 将心跳清单追加到 OpenClaw 工作区：

```bash
cat ~/ai-intelligence/heartbeat/HEARTBEAT.md >> ~/.openclaw/workspace/HEARTBEAT.md
```

OpenClaw 会自动读取 `HEARTBEAT.md` 并在心跳周期中执行检查。也可以手动触发，向 OpenClaw 提问："运行心跳检查。"

## 评分体系

事件按 1-10 分加权评分：

| 权重 | 维度 | 说明 |
|------|------|------|
| 25% | 来源权威性 | 官方博客 > 主流媒体 > 社区 > 个人 |
| 25% | 兴趣匹配度 | 与你配置的兴趣标签的相关性 |
| 20% | 新颖度 | 全新概念 > 重大更新 > 增量改进 |
| 15% | 社区热度 | 互动指标（点赞、评论、转发） |
| 15% | 时效性 | 突发新闻 > 当日 > 1-2 天前 |

## 许可证

MIT
