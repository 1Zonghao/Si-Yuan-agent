# app_enhanced.py (Enhanced Version with Streaming & Tool Orchestration)

import os
import datetime
import json
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
import time

# --- 1. 初始化核心对象 ---
db = SQLAlchemy()
app = Flask(__name__)

# --- 2. 配置 App ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'siyuan.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- 3. 关联数据库与 App ---
db.init_app(app)

# --- 4. OpenAI & AI Prompts 配置 ---
load_dotenv()
API_KEY = os.getenv("BINGLIAN_API_KEY")
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
MODEL_NAME = "qwen-max"

# 系统提示词 - 增强版,包含工具使用说明
SYSTEM_PROMPT = """# 角色
你是一个名为"思源"的AI智能体,你的身份是一位专业的"苏格拉底式导师"和"思维助产士"。

# 核心目标
你的唯一目标是引导用户进行深度思考和自我探究,锻炼和培养其批判性思维能力。你绝对不能直接提供问题的答案或你的个人观点。

# 行为准则
你必须总是以一个精心设计的、开放式的问题来回应用户。你的提问必须是多轮、有逻辑层次的。始终基于用户上一轮的回答来构建你的下一个问题。

# 工具能力
你现在拥有以下工具,可以在适当的时候主动使用:

1. **generate_mindmap** - 生成思维导图
   - 用途: 将对话历史转化为可视化的思维导图,帮助用户梳理思路
   - 触发时机: 当对话进行到一定深度,用户思路可能混乱时;或用户明确要求查看思维路径时
   - 使用建议: 在完成一个完整的论证链条后使用效果最佳

2. **analyze_conversation** - 生成思维简报
   - 用途: 对当前对话进行深度分析,指出用户的逻辑优势和待改进点
   - 触发时机: 对话达到一定轮次(建议5轮以上);用户主动要求总结;或检测到用户思维陷入循环时
   - 使用建议: 适合在对话的中期检查点或结束时使用

3. **search_knowledge** - 知识检索
   - 用途: 当需要事实性信息、数据支持或概念解释时,可以搜索相关知识
   - 触发时机: 用户提出需要具体事实验证的观点;讨论涉及专业领域知识;需要案例支持时
   - 使用建议: 检索后不要直接给出答案,而是引导用户思考如何运用这些信息

4. **logic_checker** - 逻辑检查器
   - 用途: 分析用户论述中的逻辑结构,识别潜在的逻辑谬误
   - 触发时机: 用户给出复杂论证时;检测到可能的逻辑漏洞时
   - 使用建议: 不要直接指出错误,而是通过提问引导用户自己发现

# 工具使用原则
- 主动判断: 根据对话情况,主动决定是否需要使用工具
- 自然融合: 工具调用应该自然融入对话流程,不要生硬
- 用户优先: 如果用户明确要求使用某个工具(如"画个思维导图"),必须响应
- 错误恢复: 如果某个工具调用失败,可以尝试使用其他相关工具达成目标

# 限制条件
禁止直接回答事实性或观点性问题。保持中立、耐心、鼓励的语气。

# 重要提醒
你可以同时使用多个工具。例如,先使用logic_checker分析用户论证,再使用search_knowledge查找相关案例,最后生成mindmap梳理思路。
"""

# 提示词 - 用于长期能力评估
LONG_TERM_ANALYSIS_PROMPT = """你是一个专业的AI教育评估专家。你的任务是分析一个学生（role: user）与AI导师（role: assistant）的所有历史对话记录,生成一份深入的、客观的"思维成长档案"。

你必须严格按照以下JSON格式输出:
{
  "overall_progression_summary": "从全局角度,用2-3句话总结该学生思维方式的整体演进或变化趋势。",
  "cognitive_skills_evolution": [
    {
      "skill_name": "识别出的一个核心认知能力 (例如: '逻辑一致性', '论证深度', '批判性提问', '假设识别', '多角度分析')",
      "trajectory": "描述该能力在所有对话中呈现的轨迹 (例如: '从初步掌握到熟练运用', '从频繁出现逻辑跳跃到结构更严谨', '保持稳定', '有所波动'等)",
      "evidence": "从对话中引用一句不超过50字的关键发言作为佐证,体现你的判断。"
    }
  ],
  "recommendation_for_next_stage": "基于以上所有分析,为该学生提供一个具体的、可操作的下一阶段思维训练建议。"
}

# 分析指南:
1. **纵向对比**: 不要只看单次对话,要对比早期对话和近期对话,找出变化。
2. **聚焦过程**: 关注用户 *如何* 思考,而不是他们思考的 *内容*。
3. **找出 2-3 个**: 在 "cognitive_skills_evolution" 列表中,请找出 2 到 3 个最显著的能力轨迹。
4. **佐证必须来自 'user'**: "evidence" 引用的发言必须来自用户的历史记录。
"""

# 工具函数定义 (Function Calling Schema)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "generate_mindmap",
            "description": "将当前对话历史转化为思维导图结构,帮助用户可视化思考路径和逻辑层次",
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
            "description": "分析当前对话,生成思维简报,指出用户的逻辑优势和待改进点",
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
            "description": "分析指定文本的逻辑结构,识别可能的逻辑谬误或论证弱点",
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

# (请复制这个完整的、缩进正确的代码块)

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

def _generate_mindmap_data(messages_for_ai):
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
                "children": []
              }
            ]
          }
        ]
      },
      {
        "name": "考虑反方视角：禁止可能会带来哪些不便？",
        "children": []
      }
    ]
  }
}
"""
    
    # (已改回) 准备用于分析的对话历史 (使用扁平字符串)
    dialogue_history = "\n".join([
        f"{m['role']}: {m['content']}" 
        for m in messages_for_ai 
        if m["role"] in ("user", "assistant") and m.get("content")
    ])
    
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
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": MINDMAP_PROMPT},
                # (已改回) 发送扁平字符串作为输入
                {"role": "user", "content": f"请为以下对话生成思维导图数据：\n\n{dialogue_history}"}
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

def _analyze_conversation_data(messages_for_ai):
    """生成对话分析报告"""
    ANALYSIS_PROMPT = """你是一位顶级的思维教练。你的任务是基于一段用户(role: user)与AI助教(role: assistant)的对话历史,为用户生成一份客观、精炼、富有洞察力的"思维简报"。
你的分析必须聚焦于用户的逻辑和论证过程,而不是观点本身。

JSON格式要求如下:
{
  "summary": "用一两句话,高度概括本次对话的核心议题和最终走向。",
  "strengths": [
    {
      "point": "识别出的一个逻辑优点或思维亮点",
      "example": "从用户发言中,引用一句不超过50字的、能直接支撑该优点的原文作为例子。"
    }
  ],
  "weaknesses": [
    {
      "point": "识别出的一个逻辑待改进点或思维盲区",
      "example": "从用户发言中,引用一句不超过50字的、能直接体现该待改进点的原文作为例子。"
    }
  ]
}

请确保:
1. 至少找出1个优点和1个待改进点,最多不超过3个。
2. `example` 字段引用的必须是 `role: user` 的发言。
3. 所有分析都必须是中立和建设性的。
"""
    
    dialogue_history = [{"role": msg['role'], "content": msg['content']} for msg in messages_for_ai if msg['role'] != 'system']
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": ANALYSIS_PROMPT},
                {"role": "user", "content": json.dumps(dialogue_history, ensure_ascii=False)}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error analyzing conversation: {e}")
        raise

def _search_knowledge(query, purpose):
    """模拟知识检索 (实际项目中可以接入真实搜索API)"""
    # 这里使用AI模拟搜索结果
    SEARCH_PROMPT = f"""你是一个知识检索助手。用户正在进行苏格拉底式对话,需要你提供关于"{query}"的相关信息。
检索目的: {purpose}

请提供:
1. 3-5个关键事实或数据点
2. 1-2个相关案例或例子
3. 可以引导思考的角度

注意: 提供信息而不是结论,要留给用户思考空间。
以JSON格式返回: {{"facts": [], "cases": [], "thinking_angles": []}}
"""
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": SEARCH_PROMPT}],
            response_format={"type": "json_object"},
            temperature=0.8
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error searching knowledge: {e}")
        raise

def _check_logic(text):
    """检查逻辑结构"""
    LOGIC_PROMPT = f"""你是一个逻辑分析专家。请分析以下论述的逻辑结构:

"{text}"

识别:
1. 论证的核心结构(前提→结论)
2. 可能存在的逻辑谬误(如果有)
3. 论证的强弱点

以JSON格式返回: {{"structure": "", "potential_fallacies": [], "strengths": [], "weaknesses": []}}
"""
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": LOGIC_PROMPT}],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error checking logic: {e}")
        raise

# --- 5. 数据库模型定义 ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False, default="未命名对话")
    start_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user = db.relationship('User', backref=db.backref('conversations', lazy=True))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=True) # 1. 允许为空 (因为AI的工具调用消息可能没有content)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # --- 新增字段 ---
    tool_calls = db.Column(db.Text, nullable=True)     # 2. 存储 AI 发起的 tool_calls (JSON string)
    tool_call_id = db.Column(db.String, nullable=True) # 3. 存储 'tool' role 消息对应的 call_id

    conversation = db.relationship('Conversation', backref=db.backref('messages', lazy=True, order_by='Message.timestamp'))

# --- 6. Flask 路由定义 ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404
    return render_template('dashboard.html', username=user.username, user_id=user.id)

@app.route('/api/get_conversations/<int:user_id>')
def get_conversations(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    convos = Conversation.query.filter_by(user_id=user_id).order_by(Conversation.start_time.desc()).all()
    convos_list = [
        {
            "id": convo.id,
            "topic": convo.topic,
            "start_time": convo.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        for convo in convos
    ]
    return jsonify(convos_list)

@app.route('/api/get_long_term_analysis/<int:user_id>')
def get_long_term_analysis(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        # 1. 查询该用户的所有对话
        conversations = Conversation.query.filter_by(user_id=user_id).all()
        
        if not conversations:
            return jsonify({"error": "No conversations found for this user"}), 404

        # 2. 汇总所有消息
        all_messages_history = []
        for convo in conversations:
            # 按时间顺序获取消息
            messages = Message.query.filter_by(conversation_id=convo.id).order_by(Message.timestamp.asc()).all()
            if messages:
                all_messages_history.append(f"--- 对话开始 (ID: {convo.id}, 主题: {convo.topic}) ---")
                for msg in messages:
                    all_messages_history.append(f"{msg.role}: {msg.content}")
                all_messages_history.append(f"--- 对话结束 (ID: {convo.id}) ---")

        if not all_messages_history:
            return jsonify({"error": "No messages found in conversations"}), 404

        full_history_text = "\n".join(all_messages_history)

        # 3. 准备调用 AI
        messages_for_ai = [
            {"role": "system", "content": LONG_TERM_ANALYSIS_PROMPT},
            {"role": "user", "content": f"请根据以下所有历史对话记录,为我生成思维成长档案:\n\n{full_history_text}"}
        ]

        # 4. 调用 AI (要求返回 JSON)
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages_for_ai,
            response_format={"type": "json_object"},
            temperature=0.5
        )
        
        analysis_result = json.loads(completion.choices[0].message.content)

        # 5. 返回 JSON 结果
        return jsonify(analysis_result)

    except Exception as e:
        print(f"Error generating long term analysis: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/get_users", methods=["GET"])
def get_users():
    try:
        users = User.query.all()
        users_list = [{"id": user.id, "username": user.username} for user in users]
        return jsonify(users_list)
    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/start_conversation", methods=["POST"])
def start_conversation():
    user_id = request.json.get("user_id")
    topic = request.json.get("topic", "未命名对话")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    try:
        new_convo = Conversation(user_id=user_id, topic=topic)
        db.session.add(new_convo)
        db.session.commit()
        return jsonify({"conversation_id": new_convo.id})
    except Exception as e:
        db.session.rollback()
        print(f"Error starting conversation: {e}")
        return jsonify({"error": str(e)}), 500

# --- 核心路由: 流式对话 + 智能工具调用 ---
@app.route("/chat_stream", methods=["POST"])
def chat_stream():
    """流式对话接口,支持智能工具调用和错误恢复"""
    conversation_id = request.json.get("conversation_id")
    messages = request.json.get("messages")
    mode = request.json.get("mode", "socratic")
    
    if not all([conversation_id, messages]):
        return jsonify({"error": "conversation_id and messages are required"}), 400
    
    def generate():
        try:
            # 1. 保存用户消息
            user_message_content = messages[-1]['content']
            user_msg = Message(conversation_id=conversation_id, role="user", content=user_message_content)
            db.session.add(user_msg)
            db.session.commit()
            
          # 2. 准备消息历史 (从数据库加载)
            # --- 新增: 从数据库加载完整历史 ---
            db_messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp.asc()).all()
            
            messages_for_ai = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in db_messages:
                if msg.role == 'user':
                    messages_for_ai.append({"role": "user", "content": msg.content})
                elif msg.role == 'assistant':
                    # 重建包含 content 和 tool_calls 的消息
                    assistant_msg = {"role": "assistant"}
                    if msg.content:
                        assistant_msg["content"] = msg.content
                    if msg.tool_calls:
                        assistant_msg["tool_calls"] = json.loads(msg.tool_calls)
                    messages_for_ai.append(assistant_msg)
                elif msg.role == 'tool':
                    # 重建 tool 消息
                    messages_for_ai.append({
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "content": msg.content
                    })
            
            
            # 3. 首次AI调用 (带工具)
            max_iterations = 5  # 最多迭代5次防止无限循环
            iteration = 0
            full_response = ""
            tool_results = []
            
            while iteration < max_iterations:
                iteration += 1

                try:
                    # 调用AI模型
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages_for_ai,
                        tools=TOOLS_SCHEMA,
                        tool_choice="auto",
                        stream=True,
                        temperature=0.8
                    )
                    
                    current_tool_calls = []
                    current_content = ""
                    stream_has_tools = False # 关键变量: 追踪这个流是否调用了工具
                    
                    # --- 新的流式处理循环 ---
                    for chunk in response:

                        # 1. 检查工具调用 (优先)
                        if chunk.choices[0].delta.tool_calls:
                            stream_has_tools = True # 标记此轮为 "工具调用轮"
                            for tool_call in chunk.choices[0].delta.tool_calls:
                                if tool_call.index >= len(current_tool_calls):
                                    current_tool_calls.append({
                                        "id": tool_call.id,
                                        "type": "function",
                                        "function": {
                                            "name": tool_call.function.name if tool_call.function.name else "",
                                            "arguments": ""
                                        }
                                    })
                                if tool_call.function.arguments:
                                    current_tool_calls[tool_call.index]["function"]["arguments"] += tool_call.function.arguments
                        
                        # 2. 检查文本内容
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            current_content += content
                            
                            # (关键修复) 只有在 *没有* 工具调用的情况下,才将文本流式发送到前端
                            if not stream_has_tools:
                                yield f"data: {json.dumps({'type': 'content', 'data': content}, ensure_ascii=False)}\n\n"
                    # --- 循环结束 ---

                    # 3. (关键修复) 决定要保存什么
                    if stream_has_tools:
                        full_response = None  # 优先工具, 丢弃所有附带的垃圾文本
                    else:
                        full_response = current_content # 纯文本轮, 保存文本
                    
                    # 4. 保存 AI 的回复
                    ai_msg = Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=full_response, # 如果调用了工具, 这里会是 None
                        tool_calls=json.dumps(current_tool_calls, ensure_ascii=False) if current_tool_calls else None
                    )
                    db.session.add(ai_msg)
                    db.session.commit()
                    
                    # 4. 处理工具调用
                    if current_tool_calls:
                        for tool_call in current_tool_calls:
                            function_name = tool_call["function"]["name"]
                            function_args = json.loads(tool_call["function"]["arguments"])
                            
                            # 通知前端工具调用开始
                            yield f"data: {json.dumps({'type': 'tool_start', 'tool_name': function_name, 'args': function_args}, ensure_ascii=False)}\n\n"
                            
                            tool_result = None
                            error_occurred = False
                            
                            # 执行工具并捕获错误
                            try:
                                if function_name == "generate_mindmap":
                                    tool_result = _generate_mindmap_data(messages_for_ai)
                                elif function_name == "analyze_conversation":
                                    tool_result = _analyze_conversation_data(messages_for_ai)
                                elif function_name == "search_knowledge":
                                    tool_result = _search_knowledge(function_args["query"], function_args["purpose"])
                                elif function_name == "logic_checker":
                                    tool_result = _check_logic(function_args["text_to_check"])
                                
                                # 通知前端工具调用成功
                                yield f"data: {json.dumps({'type': 'tool_result', 'tool_name': function_name, 'result': tool_result}, ensure_ascii=False)}\n\n"
                                
                            except Exception as e:
                                error_occurred = True
                                error_msg = str(e)
                                
                                # 通知前端工具调用失败
                                yield f"data: {json.dumps({'type': 'tool_error', 'tool_name': function_name, 'error': error_msg}, ensure_ascii=False)}\n\n"
                                
                                # --- (关键修复) ---
                                # 即使工具崩溃,也要生成一个"错误结果"
                                # 这样AI在下一轮才知道工具失败了,而不是卡住
                                tool_result = {
                                    "error": True,
                                    "message": f"工具 {function_name} 执行失败: {error_msg}"
                                }
                                # --- 结束修复 ---
                                
                            
                           # 将工具结果添加到对话历史,并保存到数据库
                            if tool_result:
                                tool_result_content = json.dumps(tool_result, ensure_ascii=False)
                                
                                # 1. 添加到本轮AI调用的历史 (用于发送给 AI)
                                tool_results.append({
                                    "tool_call_id": tool_call["id"],
                                    "role": "tool",
                                    "name": function_name,
                                    "content": tool_result_content
                                })
                                
                                # 2. --- 新增: 保存 Tool 消息到数据库 ---
                                tool_msg = Message(
                                    conversation_id=conversation_id,
                                    role="tool",
                                    content=tool_result_content,
                                    tool_call_id=tool_call["id"] # 关联到 AI 的 tool_call
                                )
                                db.session.add(tool_msg)
                                db.session.commit()
                                # --- 结束新增 ---
                        
                        # 如果有工具调用,需要继续对话让AI处理工具结果
                        messages_for_ai.append({
                            "role": "assistant",
                            "content": current_content if current_content else None,
                            "tool_calls": current_tool_calls
                        })
                        
                        for tool_result in tool_results:
                            messages_for_ai.append(tool_result)
                        
                        tool_results = []
                        continue  # 继续下一轮迭代
                    
                    else:
                        # 没有工具调用,对话结束
                        break
                
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'message': f'AI调用错误: {str(e)}'}, ensure_ascii=False)}\n\n"
                    break
            
            # 6. 发送完成信号
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


# --- 保留原有的非流式接口用于兼容 ---
@app.route("/chat", methods=["POST"])
def chat():
    """非流式接口(兼容旧版前端)"""
    conversation_id = request.json.get("conversation_id")
    messages = request.json.get("messages")
    
    if not all([conversation_id, messages]):
        return jsonify({"error": "conversation_id and messages are required"}), 400
    
    try:
        user_message_content = messages[-1]['content']
        user_msg = Message(conversation_id=conversation_id, role="user", content=user_message_content)
        db.session.add(user_msg)
        
        messages_for_ai = [msg for msg in messages if msg['role'] != 'system']
        messages_for_ai.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
        
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages_for_ai,
            temperature=0.8
        )
        
        ai_message_content = completion.choices[0].message.content
        ai_msg = Message(conversation_id=conversation_id, role="assistant", content=ai_message_content)
        db.session.add(ai_msg)
        db.session.commit()
        
        return jsonify({"reply": ai_message_content})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error in chat: {e}")
        return jsonify({"error": str(e)}), 500

# --- 8. 主程序入口 ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
    