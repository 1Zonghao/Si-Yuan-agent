# 思源AI - 本地部署文件包

## 📦 文件清单

本文件夹包含本地部署所需的所有文件：

### Python 核心文件
- `app.py` - Flask主应用（包含所有路由和业务逻辑）
- `create_db.py` - 数据库初始化脚本
- `manage_users.py` - 用户管理脚本（可选）
- `requirements.txt` - Python依赖包列表

### 前端文件
- `static/chat_interface.js` - 前端聊天界面JavaScript
- `static/tool_status.css` - 工具状态显示样式
- `templates/index.html` - 主页面模板
- `templates/dashboard.html` - 思维成长档案页面模板

### 配置文件
- `.env` - 环境变量配置文件（**重要**：需要您自己在 `local_deploy` 目录下创建）

**创建 `.env` 文件的方法：**
在 `local_deploy` 目录下创建 `.env` 文件，内容如下：
```
BINGLIAN_API_KEY=你的API密钥
```

⚠️ **注意**: 如果您的 `.env` 文件已经在 `agent` 目录下，请将其复制到 `local_deploy` 目录下。

## 🚀 快速部署步骤

### 1. 创建虚拟环境（推荐）
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
在 `local_deploy` 目录下创建 `.env` 文件：
```
BINGLIAN_API_KEY=你的API密钥
```

### 4. 初始化数据库
```bash
python create_db.py
```

### 5. 启动应用
```bash
python app.py
```

应用将在 http://localhost:5001 启动

## 📝 注意事项

1. **API密钥**: 确保 `.env` 文件包含有效的 `BINGLIAN_API_KEY`
2. **数据库**: 首次运行 `create_db.py` 会创建 `siyuan.db` 数据库文件
3. **端口**: 默认端口为 5001，可在 `app.py` 最后一行修改

## 🔧 文件说明

所有文件都是从主项目复制而来，未做任何修改，可以直接使用。

