// chat_interface.js - 流式对话前端处理示例

class StreamingChatInterface {
    constructor() {
        this.conversationId = null;
        this.messages = [];
        this.toolCallsInProgress = new Set();
    }

    async startConversation() {
    const userId = document.getElementById('user-select').value;
    if (!userId) {
        alert('请先选择一个用户！');
        return;
    }

    try {
        const response = await fetch('/start_conversation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await response.json();

        if (data.error) {
            alert('启动对话失败: ' + data.error);
            return;
        }

        // 成功获取 conversation_id
        this.conversationId = data.conversation_id;
        this.messages = []; // 清空历史消息
        document.getElementById('chat-messages').innerHTML = ''; // 清空聊天界面

        // 提示用户可以开始
        this.addMessageToUI('ai', '对话已启动，我是您的苏格拉底式导师思源，请提出您的问题或想法。');

    } catch (error) {
        alert('网络错误，无法连接服务器。');
        console.error(error);
    }
}

    /**
     * 发送消息并处理流式响应
     */
    async sendMessage(userMessage) {
        if (!this.conversationId) {
            alert('请先点击 "开始新对话"！');
            return; // 阻止消息发送
        }
        // 1. 添加用户消息到界面
        this.addMessageToUI('user', userMessage);
        this.messages.push({ role: 'user', content: userMessage });

        // 2. 创建AI消息容器
        const aiMessageElement = this.createAIMessageElement();
        const contentDiv = aiMessageElement.querySelector('.message-content');
        const toolStatusDiv = aiMessageElement.querySelector('.tool-status');

        try {
            // 3. 建立SSE连接
            const response = await fetch('/chat_stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    conversation_id: this.conversationId,
                    messages: this.messages,
                    mode: 'socratic'
                })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let aiFullResponse = '';

            // 4. 读取流式数据
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop(); // 保留未完成的行

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));
                        
                        // 处理不同类型的数据
                        switch (data.type) {
                            case 'content':
                                // 流式显示文本内容
                                aiFullResponse += data.data;
                                contentDiv.textContent = aiFullResponse;
                                this.scrollToBottom();
                                break;

                            case 'tool_start':
                                // 显示工具调用开始
                                this.showToolStart(toolStatusDiv, data.tool_name, data.args);
                                this.toolCallsInProgress.add(data.tool_name);
                                break;

                            case 'tool_result':
                                // 显示工具调用成功
                                this.showToolSuccess(toolStatusDiv, data.tool_name, data.result);
                                this.toolCallsInProgress.delete(data.tool_name);
                                
                                // 根据工具类型显示结果
                                this.renderToolResult(data.tool_name, data.result);
                                break;

                            case 'tool_error':
                                // 显示工具调用失败
                                this.showToolError(toolStatusDiv, data.tool_name, data.error);
                                this.toolCallsInProgress.delete(data.tool_name);
                                break;

                            case 'tool_fallback':
                                // 显示替代方案
                                this.showToolFallback(toolStatusDiv, data.original_tool, data.result);
                                break;

                            case 'done':
                                // 对话完成
                                if (aiFullResponse) {
                                    this.messages.push({ role: 'assistant', content: aiFullResponse });
                                }
                                this.clearToolStatus(toolStatusDiv);
                                break;

                            case 'error':
                                // 错误处理
                                this.showError(contentDiv, data.message);
                                break;
                        }
                    }
                }
            }

        } catch (error) {
            console.error('Streaming error:', error);
            this.showError(contentDiv, '连接错误,请重试');
        }
    }

    /**
     * 创建AI消息元素
     */
    createAIMessageElement() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message';
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="sender">思源AI</span>
                <span class="timestamp">${this.getTimestamp()}</span>
            </div>
            <div class="tool-status"></div>
            <div class="message-content"></div>
        `;
        
        const chatContainer = document.getElementById('chat-messages');
        chatContainer.appendChild(messageDiv);
        return messageDiv;
    }

    /**
     * 显示工具调用开始
     */
    showToolStart(container, toolName, args) {
        const toolDiv = document.createElement('div');
        toolDiv.className = 'tool-call-status active';
        toolDiv.id = `tool-${toolName}`;
        
        const toolNameChinese = this.getToolNameChinese(toolName);
        const argsText = this.formatToolArgs(args);
        
        toolDiv.innerHTML = `
            <div class="tool-icon">🔧</div>
            <div class="tool-info">
                <div class="tool-name">${toolNameChinese}</div>
                <div class="tool-args">${argsText}</div>
                <div class="tool-progress">
                    <div class="spinner"></div>
                    <span>执行中...</span>
                </div>
            </div>
            <div class="tool-time">${this.getTimestamp()}</div>
        `;
        
        container.appendChild(toolDiv);
    }

    /**
     * 显示工具调用成功
     */
    showToolSuccess(container, toolName, result) {
        const toolDiv = container.querySelector(`#tool-${toolName}`);
        if (toolDiv) {
            toolDiv.className = 'tool-call-status success';
            const progressDiv = toolDiv.querySelector('.tool-progress');
            progressDiv.innerHTML = `
                <span class="success-icon">✓</span>
                <span>完成</span>
            `;
        }
    }

    /**
     * 显示工具调用失败
     */
    showToolError(container, toolName, error) {
        const toolDiv = container.querySelector(`#tool-${toolName}`);
        if (toolDiv) {
            toolDiv.className = 'tool-call-status error';
            const progressDiv = toolDiv.querySelector('.tool-progress');
            progressDiv.innerHTML = `
                <span class="error-icon">✗</span>
                <span>失败: ${error}</span>
            `;
        }
    }

    /**
     * 显示替代方案
     */
    showToolFallback(container, originalTool, result) {
        const toolDiv = document.createElement('div');
        toolDiv.className = 'tool-call-status fallback';
        
        toolDiv.innerHTML = `
            <div class="tool-icon">🔄</div>
            <div class="tool-info">
                <div class="tool-name">使用备选方案</div>
                <div class="tool-args">原工具 ${this.getToolNameChinese(originalTool)} 不可用</div>
            </div>
        `;
        
        container.appendChild(toolDiv);
    }

    /**
     * 渲染工具结果
     */
    renderToolResult(toolName, result) {
        switch (toolName) {
            case 'generate_mindmap':
                this.renderMindmap(result);
                break;
            case 'analyze_conversation':
                this.renderAnalysis(result);
                break;
            case 'search_knowledge':
                this.renderSearchResults(result);
                break;
            case 'logic_checker':
                this.renderLogicCheck(result);
                break;
        }
    }

    /**
     * 渲染思维导图
     */
    renderMindmap(data) {
        // 检查是否为降级方案
        if (data.fallback) {
            this.showFallbackMessage('思维导图', data.message);
            return;
        }

        // 创建独立的思维导图容器
        const mindmapContainer = document.createElement('div');
        mindmapContainer.className = 'tool-result mindmap-result';
        mindmapContainer.innerHTML = `
            <div class="result-header">
                <h3>📊 思维导图</h3>
                <button class="expand-btn" onclick="expandMindmap(this)">展开</button>
            </div>
            <div class="result-content">
                <div id="mindmap-${Date.now()}" style="width: 100%; height: 500px;"></div>
            </div>
        `;

        document.getElementById('chat-messages').appendChild(mindmapContainer);

        // 使用 ECharts 渲染 (需要引入 echarts.js)
        const chartDom = mindmapContainer.querySelector('[id^="mindmap-"]');
        const myChart = echarts.init(chartDom);
        
        const option = {
            tooltip: {
                trigger: 'item',
                triggerOn: 'mousemove'
            },
            series: [{
                type: 'tree',
                data: [data.data],
                left: '2%',
                right: '2%',
                top: '8%',
                bottom: '20%',
                symbol: 'emptyCircle',
                symbolSize: 7,
                orient: 'vertical',
                expandAndCollapse: true,
                label: {
                    position: 'top',
                    rotate: 0,
                    verticalAlign: 'middle',
                    align: 'center',
                    fontSize: 12
                },
                leaves: {
                    label: {
                        position: 'bottom',
                        rotate: 0,
                        verticalAlign: 'middle',
                        align: 'center'
                    }
                },
                animationDurationUpdate: 750
            }]
        };
        
        myChart.setOption(option);
    }

    /**
     * 渲染分析报告
     */
    renderAnalysis(data) {
        if (data.fallback) {
            this.showFallbackMessage('思维简报', data.message);
            return;
        }

        const analysisContainer = document.createElement('div');
        analysisContainer.className = 'tool-result analysis-result';
        
        let strengthsHTML = data.strengths.map(s => `
            <div class="point-item">
                <div class="point-label">💪 ${s.point}</div>
                <div class="point-example">"${s.example}"</div>
            </div>
        `).join('');

        let weaknessesHTML = data.weaknesses.map(w => `
            <div class="point-item">
                <div class="point-label">🎯 ${w.point}</div>
                <div class="point-example">"${w.example}"</div>
            </div>
        `).join('');

        analysisContainer.innerHTML = `
            <div class="result-header">
                <h3>📝 思维简报</h3>
            </div>
            <div class="result-content">
                <div class="summary-section">
                    <h4>总体概述</h4>
                    <p>${data.summary}</p>
                </div>
                <div class="strengths-section">
                    <h4>思维亮点</h4>
                    ${strengthsHTML}
                </div>
                <div class="weaknesses-section">
                    <h4>提升空间</h4>
                    ${weaknessesHTML}
                </div>
            </div>
        `;

        document.getElementById('chat-messages').appendChild(analysisContainer);
    }

    /**
     * 渲染搜索结果
     */
    renderSearchResults(data) {
        if (data.fallback) {
            this.showFallbackMessage('知识检索', data.message);
            return;
        }

        const searchContainer = document.createElement('div');
        searchContainer.className = 'tool-result search-result';
        
        searchContainer.innerHTML = `
            <div class="result-header">
                <h3>🔍 知识检索结果</h3>
            </div>
            <div class="result-content">
                ${data.facts ? `
                    <div class="facts-section">
                        <h4>关键事实</h4>
                        <ul>${data.facts.map(f => `<li>${f}</li>`).join('')}</ul>
                    </div>
                ` : ''}
                ${data.cases ? `
                    <div class="cases-section">
                        <h4>相关案例</h4>
                        <ul>${data.cases.map(c => `<li>${c}</li>`).join('')}</ul>
                    </div>
                ` : ''}
                ${data.thinking_angles ? `
                    <div class="angles-section">
                        <h4>思考角度</h4>
                        <ul>${data.thinking_angles.map(a => `<li>${a}</li>`).join('')}</ul>
                    </div>
                ` : ''}
            </div>
        `;

        document.getElementById('chat-messages').appendChild(searchContainer);
    }

    /**
     * 渲染逻辑检查结果
     */
    renderLogicCheck(data) {
        if (data.fallback) {
            this.showFallbackMessage('逻辑检查', data.message);
            return;
        }

        const logicContainer = document.createElement('div');
        logicContainer.className = 'tool-result logic-result';
        
        logicContainer.innerHTML = `
            <div class="result-header">
                <h3>🧠 逻辑分析</h3>
            </div>
            <div class="result-content">
                <div class="structure-section">
                    <h4>论证结构</h4>
                    <p>${data.structure}</p>
                </div>
                ${data.potential_fallacies && data.potential_fallacies.length > 0 ? `
                    <div class="fallacies-section">
                        <h4>⚠️ 可能的逻辑问题</h4>
                        <ul>${data.potential_fallacies.map(f => `<li>${f}</li>`).join('')}</ul>
                    </div>
                ` : ''}
                <div class="logic-strengths">
                    <h4>✓ 论证优势</h4>
                    <ul>${data.strengths.map(s => `<li>${s}</li>`).join('')}</ul>
                </div>
                <div class="logic-weaknesses">
                    <h4>→ 改进方向</h4>
                    <ul>${data.weaknesses.map(w => `<li>${w}</li>`).join('')}</ul>
                </div>
            </div>
        `;

        document.getElementById('chat-messages').appendChild(logicContainer);
    }

    /**
     * 显示降级方案消息
     */
    showFallbackMessage(toolName, message) {
        const fallbackDiv = document.createElement('div');
        fallbackDiv.className = 'tool-result fallback-message';
        fallbackDiv.innerHTML = `
            <div class="result-header">
                <h3>ℹ️ ${toolName}</h3>
            </div>
            <div class="result-content">
                <p>${message}</p>
            </div>
        `;
        document.getElementById('chat-messages').appendChild(fallbackDiv);
    }

    // --- 辅助方法 ---

    getToolNameChinese(toolName) {
        const nameMap = {
            'generate_mindmap': '生成思维导图',
            'analyze_conversation': '生成思维简报',
            'search_knowledge': '知识检索',
            'logic_checker': '逻辑检查'
        };
        return nameMap[toolName] || toolName;
    }

    formatToolArgs(args) {
        if (args.reason) return args.reason;
        if (args.query) return `查询: ${args.query}`;
        if (args.text_to_check) return `检查内容: ${args.text_to_check.substring(0, 30)}...`;
        return JSON.stringify(args);
    }

    getTimestamp() {
        const now = new Date();
        return `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`;
    }

    addMessageToUI(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="sender">${role === 'user' ? '你' : '思源AI'}</span>
                <span class="timestamp">${this.getTimestamp()}</span>
            </div>
            <div class="message-content">${content}</div>
        `;
        document.getElementById('chat-messages').appendChild(messageDiv);
        this.scrollToBottom();
    }

    showError(element, message) {
        element.innerHTML = `<span class="error-message">❌ ${message}</span>`;
    }

    clearToolStatus(container) {
        setTimeout(() => {
            const toolDivs = container.querySelectorAll('.tool-call-status');
            toolDivs.forEach(div => {
                if (div.classList.contains('success')) {
                    div.style.opacity = '0.7';
                }
            });
        }, 2000);
    }

    scrollToBottom() {
        const chatContainer = document.getElementById('chat-messages');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// 使用示例
const chatInterface = new StreamingChatInterface();

// 绑定发送按钮
document.getElementById('send-button').addEventListener('click', () => {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    if (message) {
        chatInterface.sendMessage(message);
        input.value = '';
    }
});

// 绑定“开始新对话”按钮 (新增)
document.getElementById('new-convo-button').addEventListener('click', () => {
    chatInterface.startConversation();
});
// chat_interface.js 文件的末尾或单独的 JS 文件中

// 绑定“思维成长档案”按钮
document.getElementById('dashboard-button').addEventListener('click', () => {
    const userSelect = document.getElementById('user-select');
    const userId = userSelect.value;

    // 检查用户是否已选择
    if (!userId) {
        alert('请先从下拉菜单中选择一个用户！');
        return;
    }

    // 在新标签页中打开仪表盘
    // 这将导航到 /dashboard/1 (或选择的任何 user_id)
    window.open(`/dashboard/${userId}`, '_blank');
});

/**
 * 页面加载时获取用户列表并填充到下拉菜单
 */
async function fetchUsers() {
    const userSelect = document.getElementById('user-select');
    userSelect.innerHTML = '<option value="">加载中...</option>';

    try {
        // 调用后端 API
        const response = await fetch('/api/get_users'); 
        const users = await response.json();

        // 检查是否有错误信息
        if (users.error) {
            userSelect.innerHTML = `<option value="">加载失败: ${users.error}</option>`;
            return;
        }

        // 成功获取用户列表
        userSelect.innerHTML = '<option value="">--- 请选择一个用户 ---</option>';
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = `${user.username} (ID: ${user.id})`;
            userSelect.appendChild(option);
        });
        
        // 自动选择第一个用户（如果存在）
        if (users.length > 0) {
            userSelect.value = users[0].id;
        }
        
    } catch (error) {
        userSelect.innerHTML = '<option value="">加载用户失败 (网络或服务器问题)</option>';
        console.error('获取用户列表失败:', error);
    }
}

// 页面加载完成后调用这个函数
window.addEventListener('load', fetchUsers);

/**
 * 展开/折叠思维导图
 */
function expandMindmap(button) {
    const mindmapContainer = button.closest('.mindmap-result');
    const resultContent = mindmapContainer.querySelector('.result-content');
    const chartDom = resultContent.querySelector('[id^="mindmap-"]');
    
    if (chartDom.style.display === 'none') {
        chartDom.style.display = 'block';
        button.textContent = '展开';
    } else {
        chartDom.style.display = 'none';
        button.textContent = '收起';
    }
}