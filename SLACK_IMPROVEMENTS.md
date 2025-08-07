# Slack 通知功能改进

## 问题描述
原来的 Slack 通知只发送本地文件路径，用户无法直接在 Slack 中查看报告内容，需要手动访问本地文件。

## 解决方案

### 1. 增强基础通知功能
**文件：** `utils/slack_notifier.py`

**改进内容：**
- ✅ 自动读取报告文件内容
- ✅ 将完整报告内容发送到 Slack
- ✅ 智能截取长内容（3000字符限制）
- ✅ 添加错误处理和备选方案
- ✅ 保持向后兼容性

### 2. 高级通知功能
**文件：** `utils/slack_advanced.py`

**新功能：**
- ✅ 支持富文本格式（Slack Blocks）
- ✅ 智能内容分割，避免长度限制
- ✅ 分段发送长内容
- ✅ 支持文件上传（需要 Bot Token）
- ✅ 更好的视觉体验

### 3. 配置选项

#### 基础配置
```bash
# 必需：Webhook URL
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
```

#### 高级配置
```bash
# 可选：Bot Token（用于文件上传等高级功能）
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
```

## 使用方法

### 方法1：使用增强的基础通知（推荐）
```python
from utils.slack_notifier import send_to_slack

# 自动发送完整报告内容
send_to_slack(summary, report_path)
```

### 方法2：使用高级通知
```python
from utils.slack_advanced import send_to_slack_with_file

# 发送富文本格式的通知
send_to_slack_with_file(summary, report_path)
```

### 方法3：使用简单通知（兼容旧版本）
```python
from utils.slack_advanced import send_simple_notification

# 只发送摘要和文件路径
send_simple_notification(summary, report_path)
```

## 测试方法

### 测试基础通知
```bash
python tests/test_slack_notifier.py
```

### 测试高级通知
```bash
python tests/test_slack_advanced.py
```

### 测试完整流程
```bash
python tests/test_run_report_simple.py
```

## 消息格式对比

### 原来的格式
```
*投资研究周报*
摘要：本周重点：请关注宏观变化与科技板块机会。
📄 本地报告: reports/report_2025-08-07_19-04.md
```

### 新的格式
```
*📊 投资研究周报*

# 📊 投资研究周报 (2025-08-07 19:04)

## 🔥 热点新闻与分析
### Car insurance options for low-mileage drivers
1) 涉及的行业主题：保险行业，尤其是与汽车保险相关的领域。
...

[完整报告内容]
```

## 优势

1. **即时查看** - 用户可以直接在 Slack 中查看完整报告
2. **无需下载** - 不需要访问本地文件
3. **格式美观** - 使用 Markdown 格式，阅读体验更好
4. **智能分割** - 自动处理长内容，避免消息截断
5. **向后兼容** - 保持原有功能不变
6. **错误处理** - 完善的错误处理和备选方案

## 注意事项

1. **消息长度限制** - Slack 单条消息有长度限制，长内容会自动分割
2. **文件权限** - 确保程序有读取报告文件的权限
3. **网络连接** - 需要稳定的网络连接发送消息
4. **Webhook 安全** - 保护好 Webhook URL，避免泄露

## 故障排除

### 问题：报告内容没有发送
**解决方案：**
1. 检查报告文件是否存在
2. 确认文件读取权限
3. 查看错误日志

### 问题：消息被截断
**解决方案：**
1. 使用高级通知功能
2. 内容会自动分割发送
3. 检查网络连接

### 问题：格式显示异常
**解决方案：**
1. 检查 Markdown 格式
2. 使用高级通知的富文本格式
3. 确认 Slack 应用权限 