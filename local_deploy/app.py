# app.py (已修正并补全的完整版本)

import os
import datetime
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
import time
from pydantic import BaseModel, Field  # 导入 Pydantic 用于工具定义 
from typing import List, Optional, Dict, Any

# --- 1. 初始化核心对象  ---
db = SQLAlchemy()
app = Flask(__name__)

# --- 2. 配置 App  ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'siyuan.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- 3. 关联数据库与 App  ---
db.init_app(app)

# --- 4. OpenAI & AI Prompts 配置  ---
load_dotenv()
API_KEY = os.getenv("BINGLIAN_API_KEY")
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
MODEL_NAME = "qwen-max"

# --- 5. 数据库模型 (补全) ---
class User(db.Model):
    """用户模型 (前端需要)"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # 建立 User 和 Conversation 之间的一对多关系
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username
        }

class Conversation(db.Model):
    """对话会话模型"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # <-- 必须有这一行
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade="all, delete-orphan")

class Message(db.Model):
    """消息模型 (支持工具调用)"""
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'tool'
    content = db.Column(db.Text, nullable=True)
    
    # 用于工具调用 
    tool_call_id = db.Column(db.String(100), nullable=True) # 记录AI发起的工具调用ID
    name = db.Column(db.String(100), nullable=True) # 记录工具名称 (当 role == 'tool')
    
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        """序列化为字典,用于发送给OpenAI API"""
        if self.role == "tool":
            return {
                "role": "tool",
                "tool_call_id": self.tool_call_id,
                "name": self.name,
                "content": self.content
            }
        
        # 构建基础消息
        message = {"role": self.role, "content": self.content}
        
        # 如果是助手发起的工具调用
        if self.role == "assistant" and self.tool_call_id:
            message["tool_calls"] = [{
                "id": self.tool_call_id,
                "type": "function",
                "function": {"name": self.name, "arguments": self.content}
            }]
            # (注意) 简化：这里我们假设一个消息只有一个工具调用
            # 并且我们将参数存在 content 字段
            
        return message

# --- 6. Pydantic 工具定义 (现代化修正) ---
# (我们为  中提到的工具定义 Pydantic 模型,用于生成 Schema [3, 4])

class GenerateMindmapArgs(BaseModel):
    """
    (保留) 触发思维导图生成的参数。
    (注意) 您的 _generate_mindmap_data 函数  接受的是
    完整的 'messages_for_ai'，而不是特定参数。
    因此，我们定义一个空模型，仅用于触发工具。
    """
    pass

class AnalyzeConversationArgs(BaseModel):
    """
    (保留) 触发对话分析的参数。
    (注意) 同样，此函数接受完整历史，因此模型为空。
    """
    pass

class SearchKnowledgeArgs(BaseModel):
    """
    (补全) 为 'search_knowledge'  定义参数。
    这是唯一需要 AI 提供特定参数的工具。
    """
    query: str = Field(..., description="需要搜索的关键词或问题")

class LogicCheckerArgs(BaseModel):
    """
    (保留) 触发逻辑检查的参数。
    (注意) 同样，此函数接受完整历史，模型为空。
    """
    pass

# --- 7. 工具 Schema 和注册表 (现代化修正) ---
# (将 Pydantic 模型转换为 OpenAI API 需要的 JSON Schema 格式 )

# 工具函数定义 (Function Calling Schema)
# app.py (复制并替换从 'TOOLS_SCHEMA = [' 开始的整个列表)

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "generate_mindmap",
            "description": "当用户请求梳理思路时调用此工具。此工具会分析对话历史并在界面上显示一个可视化的思维导图。",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "为什么在这个时候生成思维导图(向用户解释)"
                    }
                },
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_conversation",
            "description": "当用户请求分析时调用此工具。此工具会分析对话历史并在界面上显示一份思维简报。",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "为什么在这个时候进行分析(向用户解释)"
                    }
                },
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "搜索相关知识、事实或案例,用于支持讨论或验证观点",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要搜索的关键词或问题"
                    },
                    "purpose": {
                        "type": "string",
                        "description": "搜索的目的(如'验证数据'、'寻找案例'、'了解背景')"
                    }
                },
                "required": ["query", "purpose"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "logic_checker",
            "description": "当用户请求检查特定文本时调用此工具。此工具会分析该文本的逻辑结构。",
            "parameters": {
                "type": "object",
                "properties": {
                    "text_to_check": {
                        "type": "string",
                        "description": "需要检查逻辑的文本内容"
                    }
                },
                "required": ["text_to_check"]
            }
        }
    }
]


# --- 8. AI Prompts 和工具实现 (保留与补全) ---

# 
SYSTEM_PROMPT = """你是一个名叫“思源”的AI，一个专业的“苏格拉底式导师”和“思想的助产士”。
你的目标是**引导用户进行深度反思**。

# 核心方法论 (你的默认行为):
1.  **提问**：你的主要回应方式是提问。
2.  **挖掘**：使用苏格拉底式提问法挑战用户的思维。
3.  **禁止直接回答**：在正常的苏格拉底对话中，永远不要提供事实、答案或你自己的观点。

# 工具使用原则 (高优先级)
这是你的核心方法论的**例外**。你必须学会区分“执行命令”和“讨论话题”。

- `generate_mindmap`:
    - **(执行)** 当用户明确**请求梳理思路**或**命令**你生成时（例如：“我需要梳理思路”、“帮我做个思维导图”、“我有点乱，帮我总结一下”），你必须调用此工具。
    - **(关键禁令)** 你**绝对禁止**在聊天中直接用文本（例如，使用星号*和破折号-）来绘制思维导图。当被要求生成思维导图时，你**唯一的**行动就是调用 `generate_mindmap` 工具。
    - **(例外)** 如果用户只是**讨论**“思维导图”这个**话题**（例如：“你认为思维导图怎么样？”或“生成思维导图需要什么能力？”），你**不能**调用工具，而应继续你的苏格拉底式提问。

- `analyze_conversation`:
    - **(执行)** 当用户明确**请求分析或简报**时（例如：“分析一下我们的对话”、“给我简报”），你必须调用此工具。
    - **(关键禁令)** 你**绝对禁止**在聊天中直接用文本（例如，“总结：... 优点：...”）来生成简报。你**唯一的**行动就是调用 `analyze_conversation` 工具。
    - **(例外)** 如果用户只是**讨论**“分析”这个**话题**，你**不能**调用工具，而应继续提问。

- `search_knowledge`:
    - **(执行)** 当用户明确要求你提供一个事实、数据、定义或案例时（例如：“什么是XXX？”、“帮我查一下数据”），你**必须**使用此工具来查找信息。
    - **(工具调用后)** 在你拿到搜索结果后，你**不能**直接陈述结果。你必须以提问的方式引导用户思考这个信息，例如：“我找到了关于 [X] 的信息。你认为这个信息如何影响你的观点？”

- `logic_checker`:
    - **(执行)** 当用户明确要求“检查我的逻辑”时，你必须调用此工具。
    - **(例外)** 如果用户只是**讨论**“逻辑”这个**话题**，你**不能**调用工具，而应继续提问。

# 工具调用后的回应原则 (极其重要)
1.  当 `generate_mindmap` 或 `analyze_conversation` 工具成功执行后，前端界面会**自动显示**一个可视化的图表或报告。
2.  因此，你的**唯一**任务是提供一个**简短的确认**（例如：“好的，思维导图已生成。”或“分析简报已完成。”），然后**立即**基于这个结果，提出你的下一个苏格拉底式问题。
3.  你**绝对禁止**、**绝对禁止**、**绝对禁止**在你的回复中，用**纯文本**（星号、破折号、JSON代码块等）重复、总结或“画出”工具已经生成的内容。让图表自己说话。
"""

# 
def _validate_and_clean_mindmap(node):
    """
    (保留) 递归函数,用于清理从AI获取的思维导图数据。
    1. 移除所有没有 'name' 属性的节点。
    2. 移除所有空的 'children' 数组。
    """
    if not isinstance(node, dict):
        return False
    
    if 'name' not in node or not node['name']:
        return False 

    if 'children' in node and isinstance(node['children'], list):
        node['children'] = [
            child for child in node['children'] if _validate_and_clean_mindmap(child)
        ]
        
    # (重要) 确保所有节点都有 children 键 (旧 prompt 的要求)
    if 'children' not in node:
        node['children'] = []

    return True

# 
def _generate_mindmap_data(messages_for_ai: List[dict]) -> Dict[str, Any]:
    """
     此函数由工具调用触发。
    它自己调用一次 AI 来生成思维导图 JSON。
    """
    MINDMAP_PROMPT = """你现在是一个专业的对话分析师。你的任务是将一段“苏格格底式对话”的历史记录，转换成一个用于ECharts树状图（Tree）的JSON对象。
这个JSON对象必须只包含一个 `data` 键，其值是一个对象，代表树的根节点。
每个节点都必须包含 'name' (节点文字) 和 'children' (子节点数组) 这两个键。
- 'name' 应该概括该步骤的核心观点或问题，保持简洁，不超过20个字。
- 'children' 是一个数组，包含所有从当前节点延伸出去的子观点或追问。叶子节点的 'children' 数组为空。
- 树的结构应该清晰地反映出对话的逻辑层次，从初始议题（根节点），到层层深入的追问和用户的回答。
**关键指令：**
1.  **优先创建分支**：你的核心目标是生成一个**发散状 (divergent)** 的结构，而不是一个线性的列表。要主动寻找并创造分支。
2.  **识别多维回答**：当用户的回答中包含**多个要点、正反两面、不同可能性或对比项**时，必须将它们拆解成**多个独立的子节点**来创建分支。
3.  **体现逻辑层次**：树的结构应该清晰地反映出对话的逻辑层次，从初始议题（根节点），到层层深入的追问和用户的回答。
- 你的输出必须是且仅是一个能够被 `JSON.parse()` 直接解析的、不包含任何额外说明文字的JSON字符串。

例如：
{
  "data": {
    "name": "初始议题：是否应禁止使用一次性塑料袋？",
    "children": [
      {
        "name": "用户观点：应该禁止，因为它污染环境。",
        "children": [
          {
            "name": "追问：环境污染具体指哪些方面？",
            "children": [
              {
                "name": "用户回答：海洋污染和土壤污染。",
                "children":
              }
            ]
          }
        ]
      },
      {
        "name": "考虑反方视角：禁止可能会带来哪些不便？",
        "children":
      }
    ]
  }
}
"""
    
    # (已改回) 准备用于分析的对话历史 (使用扁平字符串)
    
    
    user_messages_count = sum(1 for m in messages_for_ai if m['role'] == 'user')
    
    # 如果对话太短,返回提示
    if user_messages_count < 2:
        return {
            "data": {
                "name": "对话历史过短",
                "children": [
                    {"name": "请至少再进行几轮对话"},
                    {"name": "以便AI为您生成有意义的思维导图"}
                ]
            }
        }
    
    try:
        dialogue_history = "\n".join([
            f"{m['role']}: {m['content']}" 
            for m in messages_for_ai 
            if m["role"] in ("user", "assistant") and m.get("content")
        ])
        
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": MINDMAP_PROMPT},
                {"role": "user", "content": dialogue_history} # <-- 这才是正确的
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        json_string = completion.choices[0].message.content
        mindmap_data = json.loads(json_string)

        if "data" in mindmap_data:
            if not _validate_and_clean_mindmap(mindmap_data["data"]):
                 raise Exception("AI生成的根节点无效")

        else:
            raise Exception("AI未返回 'data' 键")

        return mindmap_data

    except Exception as e:
        print(f"Error generating or validating mindmap: {e}")
        # 返回一个BPlan,告诉前端出错了
        return {
            "fallback": True, # 告诉前端这是降级方案
            "message": f"AI生成思维导图失败: {str(e)}. 这通常是因为模型返回了无法解析的结构。"
        }

# 
def _analyze_conversation_data(messages_for_ai: List[dict]) -> Dict[str, Any]:
    """
    (补全) 此函数由工具调用触发。
    使用  中提到的 ANALYSIS_PROMPT 来生成 JSON。
    """
    # 
    ANALYSIS_PROMPT = """你是一个冷静、客观的逻辑分析师。你的任务是审查一段对话历史，生成一份“思想简报”。
这份简报必须采用JSON格式，包含三个键：'summary'（对话核心议题的客观总结），'strengths'（用户展现出的逻辑优点和深刻见解），以及'weaknesses'（用户可能存在的逻辑跳跃、未检验的假设或思维盲区）。
- 'strengths' 和 'weaknesses' 都必须是字符串数组。
- 分析必须客观且具有建设性，重点关注用户的论证结构。
- 你的输出必须是且仅是一个能够被 `JSON.parse()` 直接解析的、不包含任何额外说明文字的JSON字符串。

例如：
{
  "summary": "探讨了社交媒体对青少年心理健康影响的利弊。",
  "strengths": [
    "能够从个人经验出发，清晰地阐述观点。",
    "认识到了问题的多面性，没有采取极端立场。"
  ],
  "weaknesses": [
    "在讨论'成瘾性'时，存在轻微的滑坡谬误。",
    "假设了'线下社交'本质上优于'线上社交'，未提供支持。"
  ]
}
"""

# app.py (粘贴这个新版本)
        # (已恢复) 准备用于分析的对话历史 (使用扁平字符串)
    dialogue_history = "\n".join([
            f"{m['role']}: {m['content']}" 
            for m in messages_for_ai 
            if m["role"] in ("user", "assistant") and m.get("content")
        ])
        
    # app.py (粘贴这个新版本)
    completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": ANALYSIS_PROMPT}, # <-- 修正！
                {"role": "user", "content": dialogue_history}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

# 
# app.py (第 424 行)
def _search_knowledge(query: str, purpose: str) -> Dict[str, Any]: # <-- 修正 1: 添加 purpose
    """
    (存根) 模拟知识搜索。
    在实际应用中,这里应该对接一个真正的搜索 API。
    """
    print(f"Executing search_knowledge with query: {query} (Purpose: {purpose})") # <-- 修正 2: 打印 purpose
    return {
        "query": query,
        # 修正 3: 在返回结果中也用上 purpose
        "result": f"关于“{query}”的搜索结果 (搜索目的: {purpose})：这是一个苏格拉底式导师，它不会直接告诉你答案，但它找到了相关信息。请你思考，这个信息对你的观点有何影响？"
    }

# 
def _logic_checker(messages_for_ai: List[dict]) -> Dict[str, Any]:
    """
    (存根) 模拟逻辑检查。
    在实际应用中,这里可以调用一个专门的模型或规则引擎。
    """
    print("Executing logic_checker...")
    return {
        "status": "passed",
        "feedback": "在最近的对话中未发现明显的逻辑谬误。但请注意，你刚才的论证似乎依赖一个未经证实的假设。你能否澄清一下这个假设？"
    }

# (工具注册表，用于将AI调用的名称映射到Python函数)
TOOL_REGISTRY = {
    "generate_mindmap": _generate_mindmap_data,
    "analyze_conversation": _analyze_conversation_data,
    "search_knowledge": _search_knowledge,
    "logic_checker": _logic_checker
}

# --- 9. Flask 路由 (补全) ---

@app.route('/')
def index():
    """提供一个简单的 HTML 页面用于测试"""
    return render_template('index.html')

@app.route('/init_db')
def init_db():
    """(开发用) 初始化数据库"""
    with app.app_context():
        db.create_all()
    return "Database initialized!"

@app.route('/chat_stream', methods=['POST'])
def stream_chat():
    """
     核心聊天路由,支持流式响应和工具调用。
    """
    data = request.json
    conversation_id = data.get('conversation_id')

    # (已修正) 从 'messages' 数组中获取最后一条消息
    messages_from_client = data.get('messages', [])
    if not messages_from_client:
        return jsonify({"error": "No messages payload provided"}), 400
    
    # 获取用户刚刚输入的那条消息 (它在数组的末尾)
    user_input = messages_from_client[-1].get('content')
    if not user_input:
        return jsonify({"error": "Empty user message"}), 400

    # 获取或创建会话
    if conversation_id:
        conversation = db.session.get(Conversation, conversation_id)
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404
    else:
        conversation = Conversation()
        db.session.add(conversation)
        db.session.commit() # 提交以获取 ID
        conversation_id = conversation.id

    # 1. 将用户消息存入数据库
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=user_input
    )
    db.session.add(user_message)
    db.session.commit()

    # 2. 准备流式响应
    def generate_chat_responses():
        try:
            # 3. 构建消息历史
            messages = db.session.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
            # 转换为 API 格式
            api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [msg.to_dict() for msg in messages]

            # 4. (步骤 1) 发起流式 API 调用
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=api_messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                stream=True
            )

            full_delta_content = ""
            tool_calls_buffer = []# 缓冲区，用于聚合工具调用
            
            # 5. 处理流式响应
            for chunk in stream:
                delta = chunk.choices[0].delta
                
                # 5a. 处理文本流
                if delta.content:
                    full_delta_content += delta.content
                    # yield (流式发送数据包)
                    yield f"data: {json.dumps({'type': 'content', 'data': delta.content})}\n\n"
                
                # 5b. (关键) 处理工具调用流
                if delta.tool_calls:
                    # 聚合工具调用数据块
                    for tool_call_chunk in delta.tool_calls:
                        if len(tool_calls_buffer) <= tool_call_chunk.index:
                            tool_calls_buffer.append(
                                {"id": "", "type": "function", "function": {"name": "", "arguments": ""}}
                            )
                        
                        buffer = tool_calls_buffer[tool_call_chunk.index]
                        
                        if tool_call_chunk.id:
                            buffer["id"] = tool_call_chunk.id
                        if tool_call_chunk.function.name:
                            buffer["function"]["name"] = tool_call_chunk.function.name
                        if tool_call_chunk.function.arguments:
                            buffer["function"]["arguments"] += tool_call_chunk.function.arguments
                
                # 5c. 流结束
                finish_reason = chunk.choices[0].finish_reason
                if finish_reason:
                    break # 跳出循环，处理 'tool_calls' 或 'stop'

            # 6. (步骤 2) 检查是否需要工具调用
            if finish_reason == "tool_calls":
                # 6a. 将 AI 的工具调用请求存入数据库
                tool_call = tool_calls_buffer[0]
                tool_call_id = tool_call["id"]
                tool_name = tool_call["function"]["name"]
                tool_args_str = tool_call["function"]["arguments"]

                assistant_tool_message = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=tool_args_str, # 将参数存在 content 中
                    tool_call_id=tool_call_id,
                    name=tool_name
                )
                db.session.add(assistant_tool_message)
                db.session.commit()
                
                # (已修正) 6b. (关键) 向前端发送 "tool_start" 事件
                try:
                    tool_args_json = json.loads(tool_args_str)
                except json.JSONDecodeError:
                    tool_args_json = {"raw_arguments": tool_args_str} # 降级处理
                
                yield f"data: {json.dumps({'type': 'tool_start', 'tool_name': tool_name, 'args': tool_args_json})}\n\n"

                # 6c. (关键) 执行我们本地的 Python 函数
                if tool_name in TOOL_REGISTRY:
                    try:
                        # 构造参数
                        if tool_name == "search_knowledge":
                            # 此工具需要特定参数
                            args_json = json.loads(tool_args_str)
                            tool_result = TOOL_REGISTRY[tool_name](**args_json)
                        else:
                            # 其他工具需要的是完整历史
                            current_msgs = db.session.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
                            history_for_tool = [msg.to_dict() for msg in current_msgs]
                            tool_result = TOOL_REGISTRY[tool_name](history_for_tool)
                        
                        tool_result_str = json.dumps(tool_result, ensure_ascii=False)
                        
                        # (已修正) 6d. 向前端发送 "tool_result" 事件
                        yield f"data: {json.dumps({'type': 'tool_result', 'tool_name': tool_name, 'result': tool_result})}\n\n"
                        
                    except Exception as e:
                        error_msg = f"执行工具 {tool_name} 失败: {str(e)}"
                        tool_result_str = json.dumps({"fallback": True, "message": error_msg})
                        # (已修正) 6d. 向前端发送 "tool_error" 事件
                        yield f"data: {json.dumps({'type': 'tool_error', 'tool_name': tool_name, 'error': error_msg})}\n\n"
                else:
                    error_msg = f"未知的工具名称: {tool_name}"
                    tool_result_str = json.dumps({"fallback": True, "message": error_msg})
                    # (已修正) 6d. 向前端发送 "tool_error" 事件
                    yield f"data: {json.dumps({'type': 'tool_error', 'tool_name': tool_name, 'error': error_msg})}\n\n"

                # 6e. 将工具的执行结果存入数据库 (原 6c)
                tool_message = Message(
                    conversation_id=conversation_id,
                    role="tool",
                    content=tool_result_str,
                    tool_call_id=tool_call_id,
                    name=tool_name
                )
                db.session.add(tool_message)
                db.session.commit()
                
                # 6d. (步骤 3) 带着工具结果，再次调用 AI 获取最终回复
                # (构建包含工具结果的新历史)
                messages_with_tool = db.session.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
                api_messages_with_tool = [{"role": "system", "content": SYSTEM_PROMPT}] + [msg.to_dict() for msg in messages_with_tool]
                
                second_stream = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=api_messages_with_tool,
                    stream=True
                    # (注意) 第二次调用时不传递工具,以强制生成文本
                )

                final_content = ""
                for chunk in second_stream:
                    delta_content = chunk.choices[0].delta.content
                    if delta_content:
                        final_content += delta_content
                        yield f"data: {json.dumps({'type': 'content', 'data': delta_content})}\n\n"
                
                # 6e. 存储第二次调用的最终回复
                assistant_final_message = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=final_content
                )
                db.session.add(assistant_final_message)
                db.session.commit()

            else:
                # 7. (步骤 2) 如果没有工具调用,只是简单停止
                # 将AI的回复存入数据库
                assistant_message = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_delta_content
                )
                db.session.add(assistant_message)
                db.session.commit()
            
            # 8. (所有分支) 发送流结束信号
            yield f"data: {json.dumps({'type': 'end', 'conversation_id': conversation_id})}\n\n"

        except Exception as e:
            print(f"Error in chat stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

    # 将生成器包装在 Flask Response 中
    return Response(stream_with_context(generate_chat_responses()), mimetype='text/event-stream')

# --- 10. (补全) 前端所需的 API 路由 ---

@app.route('/api/get_users', methods=['GET'])
def get_users():
    """
    (补全) 响应 chat_interface.js 的 fetchUsers()
    """
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/start_conversation', methods=['POST'])
def start_conversation():
    """
    (补全) 响应 chat_interface.js 的 startConversation()
    """
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # 创建一个新的会话并与用户关联
    new_convo = Conversation(user_id=user.id)
    db.session.add(new_convo)
    db.session.commit()
    
    return jsonify({"conversation_id": new_convo.id})

@app.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    """
    (补全) 响应 dashboard.html
    """
    user = db.session.get(User, user_id)
    if not user:
        return "User not found", 404
    # 渲染 dashboard.html 模板 (你必须有这个文件在 templates 文件夹)
    # (注意) 你的 dashboard.html 不在 templates 里, 
    # 为了最快运行，我们假设它也在 static 目录
    # return render_template('dashboard.html', user_id=user.id, username=user.username)
    
    # (妥协) 假设 dashboard.html 是静态的,我们用 render_template 来"注入"数据
    # 为了让它 100% 运行，请确保 dashboard.html 在一个名为 'templates' 的文件夹中
    # 如果你没有，就用下面的静态文件方式
    
    # 假设 dashboard.html 在 templates 文件夹
    try:
        return render_template('dashboard.html', user_id=user.id, username=user.username)
    except Exception:
        return "错误：请确保 `dashboard.html` 文件位于 `templates` 文件夹中，而不是 `static` 文件夹。"


@app.route('/api/get_conversations/<int:user_id>')
def get_conversations(user_id):
    """
    (补全) 响应 dashboard.html 的历史记录加载
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    convos = db.session.query(Conversation).filter_by(user_id=user_id).order_by(Conversation.created_at.desc()).all()
    
    # (存根) 为 dashboard 生成简单数据
    results = []
    for convo in convos:
        first_message = db.session.query(Message).filter_by(conversation_id=convo.id, role='user').order_by(Message.timestamp).first()
        topic = first_message.content[:30] + '...' if first_message else "空对话"
        results.append({
            "id": convo.id,
            "topic": topic,
            "start_time": convo.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return jsonify(results)

@app.route('/api/get_long_term_analysis/<int:user_id>')
def get_long_term_analysis(user_id):
    """
    (补全) 响应 dashboard.html 的长期分析 (存根)
    """
    # 这是一个非常复杂的功能。
    # 为了让前端不报错，我们先返回一个“正在处理”的存根 (Stub)
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # (模拟数据)
    return jsonify({
        "overall_progression_summary": f"这是 {user.username} 的 AI 评估报告。目前该功能正在开发中。此数据为模拟数据。",
        "cognitive_skills_evolution": [
            {
                "skill_name": "论证清晰度",
                "trajectory": "显著提升",
                "evidence": "从最初的模糊表述（对话 #1）到能够清晰定义概念（对话 #5）。"
            },
            {
                "skill_name": "假设检验",
                "trajectory": "保持稳定",
                "evidence": "倾向于接受初始假设，在后续对话中需要更多挑战。"
            }
        ],
        "recommendation_for_next_stage": "尝试在下一阶段的对话中，主动挑战苏格拉底导师提出的观点的“反面”。"
    })

# --- 10. 运行 App ---
if __name__ == '__main__':
    # 确保在第一次运行前创建数据库
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, port=5000)
    