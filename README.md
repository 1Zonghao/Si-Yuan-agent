# 🧠 Si-Yuan-Agent | 
# 🧠 思源--苏格拉底式提问与批判性思维引导智能体

> **一位专业的"苏格拉底式导师"和"思维助产士"**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)]()

---

## 📖 项目简介

**思源 (Si-Yuan)** 是一个基于 AI 的智能思维训练助手，旨在引导用户进行深度思考和自我探究，培养批判性思维能力。

与传统 AI 助手不同，思源**不会直接提供答案**，而是通过精心设计的开放式问题，扮演"思维助产士"的角色，帮助用户自己发现答案、梳理思路、提升逻辑能力。

### ✨ 核心理念

> *"教育不是灌输，而是点燃火焰。" —— 苏格拉底*

思源遵循苏格拉底式教学法，通过多轮、有逻辑层次的提问，引导用户：
- 🔍 深入探索问题的本质
- 🧩 识别自己思维中的盲点
- 📈 逐步构建完整的论证链条
- 🎯 培养独立思考和批判性思维能力

---

## 🚀 核心功能

### 🎯 苏格拉底式对话
- 多轮深度追问，引导用户自我探究
- 基于用户回答动态调整提问策略
- 保持中立、耐心、鼓励的对话风格

### 🛠️ 智能工具系统

| 工具 | 功能 | 触发时机 |
|------|------|----------|
| **🧠 generate_mindmap** | 生成思维导图 | 对话达到一定深度，帮助用户梳理思路 |
| **📊 analyze_conversation** | 生成思维简报 | 指出用户的逻辑优势和待改进点 |
| **🔎 search_knowledge** | 知识检索 | 需要事实性信息或案例支持时 |
| **✅ logic_checker** | 逻辑检查器 | 分析论述中的逻辑结构和潜在谬误 |

### 📈 长期思维成长档案
- 追踪用户跨对话的思维能力演进
- 识别核心认知能力的发展轨迹
- 提供个性化的下一阶段训练建议

### ⚡ 流式对话体验
- 实时流式响应，无需等待
- 智能工具调用状态可视化
- 优雅的错误恢复机制

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ index.html  │  │dashboard.html│ │chat_interface│     │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                      应用层 (Flask)                      │
│  ┌─────────────────────────────────────────────────┐    │
│  │  app.py - 核心路由 & 流式对话 & 工具编排          │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                      服务层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  OpenAI API │  │  SQLAlchemy │  │  Tool System│      │
│  │  (Qwen-Max) │  │  (SQLite)   │  │  (4 Tools)  │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
```

### 技术栈

- **后端框架**: Flask 3.1.1
- **数据库**: SQLite + SQLAlchemy 2.0
- **AI 模型**: 阿里云 DashScope (Qwen-Max)
- **前端**: HTML5 + CSS3 + JavaScript (原生)
- **API 规范**: OpenAI Compatible API

---

## 📦 项目结构

```
agent/
├── app.py                 # 主应用文件 (核心逻辑)
├── create_db.py           # 数据库初始化脚本
├── manage_users.py        # 用户管理工具
├── requirements.txt       # Python 依赖
├── README.md              # 项目说明文档
├── .gitignore             # Git 忽略配置
├── static/                # 静态资源
│   ├── chat_interface.js  # 聊天界面交互逻辑
│   └── tool_status.css    # 工具状态样式
├── templates/             # HTML 模板
│   ├── index.html         # 首页
│   ├── dashboard.html     # 用户仪表盘
│   └── index.txt          # 模板说明
└── local_deploy/          # 本地部署版本
```

---

## 🔧 安装与部署

### 方式一：在线体验 (服务器到期了，用不了/(ㄒoㄒ)/~~)

项目已部署在公网，可直接访问：

```
http://47.243.124.31/
```

### 方式二：本地部署(推荐)

#### 1. 环境要求
- Python 3.8+
- pip 包管理器

#### 2. 克隆项目
```bash
git clone https://github.com/1Zonghao/Si-Yuan-agent.git
cd Si-Yuan-agent
```

#### 3. 创建虚拟环境 (可选但推荐)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

#### 4. 安装依赖
```bash
pip install -r requirements.txt
```

#### 5. 配置环境变量
创建 `.env` 文件，添加以下内容：
```env
BINGLIAN_API_KEY=your_api_key_here
```

> 💡 **获取 API Key**: 访问 [阿里云 DashScope](https://dashscope.aliyun.com/) 注册并获取 API 密钥

#### 6. 初始化数据库
```bash
python create_db.py
```

#### 7. 启动服务
```bash
python app.py
```

#### 8. 访问应用
打开浏览器访问：`http://localhost:5001`

---

## 📖 使用指南

### 1️⃣ 创建/选择用户
- 首次使用需创建用户账号
- 可在用户管理页面查看现有用户

### 2️⃣ 开始对话
- 进入用户仪表盘
- 点击"新建对话"
- 输入对话主题 (可选)

### 3️⃣ 与思源互动
- 提出你的问题或观点
- 思源会以提问的方式引导你深入思考
- 多轮对话后，可请求生成思维导图或思维简报

### 4️⃣ 查看成长档案
- 在仪表盘查看历史对话记录
- 生成"思维成长档案"，追踪长期进步

---

## 🎨 功能演示

### 对话界面
```
用户：我认为应该禁止使用一次性塑料袋

思源：这是一个很有意义的观点。你能具体说说，
     禁止使用一次性塑料袋会带来哪些好处吗？
     
用户：可以减少白色污染，保护海洋生物

思源：很好，你关注到了环境影响。那么，
     你认为"白色污染"具体指的是哪些方面呢？
     这对海洋生物又是如何产生影响的？

[🧠 正在生成思维导图...]
```

### 工具调用示例
```json
{
  "tool": "generate_mindmap",
  "status": "success",
  "output": {
    "data": {
      "name": "是否应禁止使用一次性塑料袋？",
      "children": [
        {
          "name": "支持方：减少环境污染",
          "children": [...]
        },
        {
          "name": "反对方：生活便利性降低",
          "children": [...]
        }
      ]
    }
  }
}
```

---

## 🔐 安全与隐私

### 已忽略的文件 (`.gitignore`)
以下文件不会被上传到 GitHub，保护您的敏感信息：

| 文件/文件夹 | 原因 |
|------------|------|
| `.env` | 包含 API 密钥等敏感环境变量 |
| `*.db` | 数据库文件，包含用户数据 |
| `venv/` | Python 虚拟环境 |
| `__pycache__/` | Python 编译缓存 |

### 最佳实践
- ⚠️ **不要**将 `.env` 文件提交到版本控制
- ⚠️ **不要**在公开场合分享你的 API Key
- ✅ 定期备份重要数据
- ✅ 使用强密码保护生产环境

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 贡献流程
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发规范
- 遵循 PEP 8 代码风格
- 为新增功能编写测试
- 更新文档说明

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 📬 联系方式

- **GitHub**: [@1Zonghao](https://github.com/1Zonghao/Si-Yuan-agent)
- **Issue 反馈**: [GitHub Issues](https://github.com/1Zonghao/Si-Yuan-agent/issues)

---

## 🙏 致谢

感谢以下开源项目和技术：

- [Flask](https://flask.palletsprojects.com/) - 轻量级 Web 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL 工具包
- [阿里云 DashScope](https://dashscope.aliyun.com/) - 通义千问大模型 API
- [OpenAI API](https://platform.openai.com/) - API 兼容规范

---

<div align="center">

**🌟 如果这个项目对你有帮助，请给一个 Star!**

Made with ❤️ by Zonghao Ye,Xinyang Li,Jiankai He

</div>
