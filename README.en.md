# 🧠 Si-Yuan-Agent | Socratic Thinking Assistant

> **A Professional "Socratic Mentor" and "Mind Midwife"**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)]()

---

## 📖 Introduction

**Si-Yuan (思源)** is an AI-powered intelligent thinking training assistant designed to guide users through deep self-reflection and critical thinking development.

Unlike traditional AI assistants, Si-Yuan **does not provide direct answers**. Instead, through carefully crafted open-ended questions, it acts as a "mind midwife," helping users discover answers, organize thoughts, and enhance logical reasoning abilities on their own.

### ✨ Core Philosophy

> *"Education is not the filling of a pail, but the lighting of a fire." — Socrates*

Following the Socratic method, Si-Yuan guides users through multi-layered, logical questioning to:
- 🔍 Deeply explore the essence of problems
- 🧩 Identify blind spots in their thinking
- 📈 Gradually build complete argumentation chains
- 🎯 Cultivate independent and critical thinking skills

---

## 🚀 Core Features

### 🎯 Socratic Dialogue
- Multi-round deep questioning to guide self-exploration
- Dynamic question strategy adjustment based on user responses
- Neutral, patient, and encouraging conversation style

### 🛠️ Intelligent Tool System

| Tool | Function | Trigger Condition |
|------|------|----------|
| **🧠 generate_mindmap** | Generate mind maps | When conversation reaches sufficient depth |
| **📊 analyze_conversation** | Generate thinking brief | Highlight logical strengths and areas for improvement |
| **🔎 search_knowledge** | Knowledge retrieval | When factual information or case support is needed |
| **✅ logic_checker** | Logic checker | Analyze logical structure and potential fallacies |

### 📈 Long-term Thinking Growth Portfolio
- Track thinking skill evolution across conversations
- Identify core cognitive development trajectories
- Provide personalized next-stage training recommendations

### ⚡ Streaming Conversation Experience
- Real-time streaming responses, no waiting
- Visualized intelligent tool invocation status
- Elegant error recovery mechanisms

---

## 🏗️ Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  index.html │  │dashboard.html│ │  chat_interface│   │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                      Application Layer (Flask)          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  app.py - Core Routing & Streaming & Tools      │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                      Service Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  OpenAI API │  │  SQLAlchemy │  │  Tool System│      │
│  │  (Qwen-Max) │  │  (SQLite)   │  │  (4 Tools)  │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack

- **Backend Framework**: Flask 3.1.1
- **Database**: SQLite + SQLAlchemy 2.0
- **AI Model**: Alibaba Cloud DashScope (Qwen-Max)
- **Frontend**: HTML5 + CSS3 + JavaScript (Vanilla)
- **API Specification**: OpenAI Compatible API

---

## 📦 Project Structure

```
agent/
├── app.py                 # Main application file (Core logic)
├── create_db.py           # Database initialization script
├── manage_users.py        # User management tool
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation (Chinese)
├── README.en.md           # Project documentation (English)
├── .gitignore             # Git ignore configuration
├── static/                # Static resources
│   ├── chat_interface.js  # Chat interface interaction logic
│   └── tool_status.css    # Tool status styles
├── templates/             # HTML templates
│   ├── index.html         # Homepage
│   ├── dashboard.html     # User dashboard
│   └── index.txt          # Template description
└── local_deploy/          # Local deployment version
```

---

## 🔧 Installation & Deployment

### Option 1: Online Demo (The server is temporarily unavailable)

The project is deployed on a public server, accessible directly:

```
http://47.243.124.31/
```

### Option 2: Local Deployment（Recommended）

#### 1. Requirements
- Python 3.8+
- pip package manager

#### 2. Clone the Project
```bash
git clone https://github.com/1Zonghao/Si-Yuan-agent.git
cd Si-Yuan-agent
```

#### 3. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

#### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 5. Configure Environment Variables
Create a `.env` file with the following content:
```env
BINGLIAN_API_KEY=your_api_key_here
```

> 💡 **Get API Key**: Visit [Alibaba Cloud DashScope](https://dashscope.aliyun.com/) to register and obtain your API key

#### 6. Initialize Database
```bash
python create_db.py
```

#### 7. Start the Service
```bash
python app.py
```

#### 8. Access the Application
Open your browser and visit: `http://localhost:5001`

---

## 📖 User Guide

### 1️⃣ Create/Select User
- Create a user account on first use
- View existing users on the user management page

### 2️⃣ Start a Conversation
- Enter the user dashboard
- Click "New Conversation"
- Enter a conversation topic (optional)

### 3️⃣ Interact with Si-Yuan
- Pose your questions or viewpoints
- Si-Yuan will guide you with thought-provoking questions
- After multiple rounds, request mind maps or thinking briefs

### 4️⃣ View Growth Portfolio
- View historical conversation records on the dashboard
- Generate a "Thinking Growth Portfolio" to track long-term progress

---

## 🎨 Feature Demonstration

### Conversation Interface
```
User: I think disposable plastic bags should be banned

Si-Yuan: That's a meaningful viewpoint. Could you elaborate on
         what benefits banning disposable plastic bags would bring?
     
User: It can reduce white pollution and protect marine life

Si-Yuan: Excellent, you've considered the environmental impact. 
         So, what specific aspects does "white pollution" refer to?
         And how does it affect marine life?

[🧠 Generating mind map...]
```

### Tool Invocation Example
```json
{
  "tool": "generate_mindmap",
  "status": "success",
  "output": {
    "data": {
      "name": "Should disposable plastic bags be banned?",
      "children": [
        {
          "name": "Pro: Reduce environmental pollution",
          "children": [...]
        },
        {
          "name": "Con: Reduced convenience",
          "children": [...]
        }
      ]
    }
  }
}
```

---

## 🔐 Security & Privacy

### Ignored Files (`.gitignore`)
The following files are not uploaded to GitHub to protect your sensitive information:

| File/Folder | Reason |
|------------|------|
| `.env` | Contains API keys and sensitive environment variables |
| `*.db` | Database files containing user data |
| `venv/` | Python virtual environment |
| `__pycache__/` | Python compilation cache |

### Best Practices
- ⚠️ **Do NOT** commit `.env` files to version control
- ⚠️ **Do NOT** share your API Key publicly
- ✅ Regularly backup important data
- ✅ Use strong passwords for production environments

---

## 🤝 Contributing

Contributions, issue reports, and suggestions are welcome!

### Contribution Process
1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Standards
- Follow PEP 8 code style
- Write tests for new features
- Update documentation

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

---

## 📬 Contact

- **GitHub**: [@1Zonghao](https://github.com/1Zonghao/Si-Yuan-agent)
  
- **Issue Tracker**: [GitHub Issues](https://github.com/1Zonghao/Si-Yuan-agent/issues)

---

## 🙏 Acknowledgments

Thanks to the following open-source projects and technologies:

- [Flask](https://flask.palletsprojects.com/) - Lightweight web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit
- [Alibaba Cloud DashScope](https://dashscope.aliyun.com/) - Qwen large model API
- [OpenAI API](https://platform.openai.com/) - API compatibility specification

---

<div align="center">

**🌟 If this project helps you, please give it a Star!**

Made with ❤️ by Zonghao  Ye, Xinyang Li , Jiankai He

</div>
