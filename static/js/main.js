const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const micBtn = document.getElementById('micBtn');
const newChatBtn = document.getElementById('newChatBtn');
const refreshBtn = document.getElementById('refreshBtn');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const results = document.getElementById('results');
const contentArea = document.getElementById('contentArea');
const welcomeMessage = document.getElementById('welcomeMessage');

// 发送按钮点击事件
sendBtn.addEventListener('click', handleQuery);

// 新对话按钮
newChatBtn.addEventListener('click', () => {
    resetChat();
});

// 刷新按钮
refreshBtn.addEventListener('click', () => {
    location.reload();
});

// 提示问题点击事件
document.querySelectorAll('.suggestion-item').forEach(item => {
    item.addEventListener('click', () => {
        const question = item.getAttribute('data-question');
        questionInput.value = question;
        handleQuery();
    });
});

// 回车键发送
questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleQuery();
    }
});

// 重置聊天
function resetChat() {
    questionInput.value = '';
    hideError();
    hideResults();
    hideLoading();
    showWelcome();
    // 滚动到顶部
    contentArea.scrollTop = 0;
}

// 显示欢迎消息
function showWelcome() {
    welcomeMessage.style.display = 'block';
}

// 隐藏欢迎消息
function hideWelcome() {
    welcomeMessage.style.display = 'none';
}

// 切换展开/折叠
function toggleSection(section) {
    const content = document.getElementById(`${section}-content`);
    const toggle = document.getElementById(`${section}-toggle`);
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggle.textContent = '▲';
    } else {
        content.style.display = 'none';
        toggle.textContent = '▼';
    }
}

// 处理查询
async function handleQuery() {
    const question = questionInput.value.trim();
    
    if (!question) {
        showError('请输入问题');
        return;
    }
    
    // 隐藏错误和结果，显示加载
    hideError();
    hideResults();
    hideWelcome();
    showLoading();
    sendBtn.disabled = true;
    
    // 滚动到顶部
    contentArea.scrollTop = 0;
    
    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
        } else {
            showError(data.error || '查询失败');
        }
    } catch (err) {
        showError('网络错误: ' + err.message);
    } finally {
        hideLoading();
        sendBtn.disabled = false;
    }
}

// 显示结果
function displayResults(data) {
    // 显示SQL
    const sqlText = document.getElementById('sql-text');
    sqlText.textContent = data.sql || '无SQL';
    
    // 显示查询结果
    const dataTable = document.getElementById('data-table');
    const rowCount = document.getElementById('row-count');
    
    if (data.rows && data.rows.length > 0) {
        rowCount.textContent = `(${data.rows.length} 条)`;
        dataTable.innerHTML = createTable(data.rows);
    } else {
        rowCount.textContent = '(0 条)';
        dataTable.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">暂无数据</p>';
    }
    
    // 显示总结
    const summaryText = document.getElementById('summary-text');
    summaryText.innerHTML = formatSummary(data.summary);
    
    // 显示结果区域
    showResults();
    
    // 滚动到顶部
    setTimeout(() => {
        contentArea.scrollTop = 0;
    }, 100);
}

// 创建表格
function createTable(rows) {
    if (rows.length === 0) return '<p>暂无数据</p>';
    
    const headers = Object.keys(rows[0]);
    let html = '<table><thead><tr>';
    
    headers.forEach(header => {
        html += `<th>${escapeHtml(header)}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    rows.forEach(row => {
        html += '<tr>';
        headers.forEach(header => {
            const value = row[header];
            const displayValue = value === null || value === undefined ? '' : String(value);
            html += `<td>${escapeHtml(displayValue)}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    return html;
}

// 格式化总结（支持Markdown格式）
function formatSummary(summary) {
    if (!summary) return '<p>暂无总结</p>';
    
    // 先转义HTML，然后处理Markdown格式
    let text = escapeHtml(summary);
    
    // 处理表格（必须在其他处理之前）
    const tableRegex = /\|(.+)\|/g;
    const tableMatches = [];
    let match;
    while ((match = tableRegex.exec(text)) !== null) {
        tableMatches.push({
            start: match.index,
            end: match.index + match[0].length,
            content: match[1]
        });
    }
    
    // 处理表格行
    const lines = text.split('\n');
    let processedLines = [];
    let inTable = false;
    let tableRows = [];
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.trim().match(/^\|.+\|$/)) {
            if (!inTable) {
                inTable = true;
                tableRows = [];
            }
            const cells = line.split('|').map(c => c.trim()).filter(c => c);
            tableRows.push(cells);
        } else {
            if (inTable && tableRows.length > 0) {
                // 生成表格HTML
                let tableHtml = '<table class="summary-table">';
                tableRows.forEach((row, idx) => {
                    const tag = idx === 0 ? 'th' : 'td';
                    tableHtml += '<tr>' + row.map(cell => `<${tag}>${cell}</${tag}>`).join('') + '</tr>';
                });
                tableHtml += '</table>';
                processedLines.push(tableHtml);
                tableRows = [];
                inTable = false;
            }
            processedLines.push(line);
        }
    }
    
    // 处理剩余的表格
    if (inTable && tableRows.length > 0) {
        let tableHtml = '<table class="summary-table">';
        tableRows.forEach((row, idx) => {
            const tag = idx === 0 ? 'th' : 'td';
            tableHtml += '<tr>' + row.map(cell => `<${tag}>${cell}</${tag}>`).join('') + '</tr>';
        });
        tableHtml += '</table>';
        processedLines.push(tableHtml);
    }
    
    text = processedLines.join('\n');
    
    // 处理标题
    text = text.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    text = text.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    text = text.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // 处理粗体
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // 处理列表项
    const finalLines = text.split('\n');
    let inList = false;
    let result = [];
    
    for (let i = 0; i < finalLines.length; i++) {
        const line = finalLines[i];
        if (line.trim().match(/^\- /)) {
            if (!inList) {
                result.push('<ul>');
                inList = true;
            }
            result.push('<li>' + line.replace(/^\- /, '') + '</li>');
        } else {
            if (inList) {
                result.push('</ul>');
                inList = false;
            }
            result.push(line);
        }
    }
    if (inList) {
        result.push('</ul>');
    }
    text = result.join('\n');
    
    // 处理换行
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 显示/隐藏函数
function showLoading() {
    loading.style.display = 'block';
}

function hideLoading() {
    loading.style.display = 'none';
}

function showError(message) {
    error.textContent = message;
    error.style.display = 'block';
    hideWelcome();
}

function hideError() {
    error.style.display = 'none';
}

function showResults() {
    results.style.display = 'block';
}

function hideResults() {
    results.style.display = 'none';
}
