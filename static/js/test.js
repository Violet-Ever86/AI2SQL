// 测试问题数据（从服务器加载）
let TEST_QUESTIONS = [];

// 测试结果存储
let testResults = {};
// 展开状态
let expandedQuestions = new Set();

// 初始化页面
async function initPage() {
    // 从服务器加载测试问题
    await loadTestQuestions();
    renderQuestions();
    updateStats();
}

// 从服务器加载测试问题
async function loadTestQuestions() {
    try {
        const response = await fetch('/api/test-questions');
        const data = await response.json();
        
        if (data.success && data.questions) {
            TEST_QUESTIONS = data.questions;
            console.log(`成功加载 ${TEST_QUESTIONS.length} 个测试问题`);
        } else {
            console.error('加载测试问题失败:', data.error);
            // 如果加载失败，显示错误提示
            alert('加载测试问题失败: ' + (data.error || '未知错误'));
            TEST_QUESTIONS = [];
        }
    } catch (err) {
        console.error('加载测试问题时出错:', err);
        alert('加载测试问题时出错: ' + err.message);
        TEST_QUESTIONS = [];
    }
}

// 渲染问题列表
function renderQuestions() {
    const container = document.getElementById('test-questions');
    
    // 如果没有问题，显示提示
    if (!TEST_QUESTIONS || TEST_QUESTIONS.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">正在加载测试问题...</div>';
        return;
    }
    
    const categories = {};
    
    // 按分类分组
    TEST_QUESTIONS.forEach(q => {
        if (!categories[q.category]) {
            categories[q.category] = [];
        }
        categories[q.category].push(q);
    });
    
    let html = '';
    Object.keys(categories).forEach(category => {
        html += `<div class="test-category">
            <h3>${category}测试 (${categories[category].length}个问题)</h3>`;
        
        categories[category].forEach(q => {
            const result = testResults[q.id] || { status: 'pending' };
            const isExpanded = expandedQuestions.has(q.id);
            html += `
                <div class="test-question ${result.status}">
                    <div onclick="testQuestion('${q.id}')" style="cursor: pointer;">
                        <span class="question-id">[${q.id}]</span>
                        <span class="question-text">${q.question}</span>
                        <span class="test-status status-${result.status}">
                            ${result.status === 'pending' ? '待测试' : 
                              result.status === 'testing' ? '测试中...' :
                              result.status === 'success' ? '✓ 成功' :
                              result.status === 'error' ? '✗ 失败' : ''}
                        </span>
                        ${result.status !== 'pending' && result.status !== 'testing' ? 
                          `<span class="toggle-details" onclick="event.stopPropagation(); toggleDetails('${q.id}')">
                            ${isExpanded ? '▼ 收起详情' : '▶ 查看详情'}
                          </span>` : ''}
                    </div>
                    ${result.status !== 'pending' && result.status !== 'testing' ? 
                      `<div class="question-details ${isExpanded ? 'expanded' : ''}" id="details-${q.id}">
                        ${renderDetails(q.id, result)}
                      </div>` : ''}
                </div>
            `;
        });
        
        html += '</div>';
    });
    
    container.innerHTML = html;
}

// 测试单个问题
async function testQuestion(questionId) {
    const question = TEST_QUESTIONS.find(q => q.id === questionId);
    if (!question) return;
    
    // 更新状态为测试中
    testResults[questionId] = { status: 'testing' };
    renderQuestions();
    updateStats();
    
    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question.question })
        });
        
        const data = await response.json();
        
        if (data.success) {
            testResults[questionId] = {
                status: 'success',
                sql: data.sql,
                rowCount: data.rows ? data.rows.length : 0,
                rows: data.rows || [],
                summary: data.summary,
                query_id: data.query_id,
                template_info: data.template_info,
                attempts: data.attempts || 1
            };
        } else {
            testResults[questionId] = {
                status: 'error',
                error: data.error || '查询失败',
                sql: data.sql || '',
                query_id: data.query_id,
                attempts: data.attempts || 1
            };
        }
    } catch (err) {
        testResults[questionId] = {
            status: 'error',
            error: '网络错误: ' + err.message
        };
    }
    
    renderQuestions();
    updateStats();
}

// 测试所有问题
async function testAll() {
    if (!confirm('确定要测试所有问题吗？这可能需要一些时间。')) {
        return;
    }
    
    for (const q of TEST_QUESTIONS) {
        await testQuestion(q.id);
        // 添加小延迟，避免请求过快
        await new Promise(resolve => setTimeout(resolve, 500));
    }
}

// 测试指定分类
async function testCategory(category) {
    const questions = TEST_QUESTIONS.filter(q => q.category === category);
    if (questions.length === 0) {
        alert('没有找到该分类的问题');
        return;
    }
    
    if (!confirm(`确定要测试"${category}"分类的 ${questions.length} 个问题吗？`)) {
        return;
    }
    
    for (const q of questions) {
        await testQuestion(q.id);
        await new Promise(resolve => setTimeout(resolve, 500));
    }
}

// 清除结果
function clearResults() {
    if (!confirm('确定要清除所有测试结果吗？')) {
        return;
    }
    
    testResults = {};
    renderQuestions();
    updateStats();
}

// 更新统计信息
function updateStats() {
    const total = TEST_QUESTIONS.length;
    let tested = 0;
    let success = 0;
    let error = 0;
    
    Object.values(testResults).forEach(result => {
        if (result.status !== 'pending') {
            tested++;
            if (result.status === 'success') {
                success++;
            } else if (result.status === 'error') {
                error++;
            }
        }
    });
    
    document.getElementById('total-count').textContent = total;
    document.getElementById('tested-count').textContent = tested;
    document.getElementById('success-count').textContent = success;
    document.getElementById('error-count').textContent = error;
}

// 切换详情显示
function toggleDetails(questionId) {
    if (expandedQuestions.has(questionId)) {
        expandedQuestions.delete(questionId);
    } else {
        expandedQuestions.add(questionId);
    }
    renderQuestions();
}

// 渲染详情内容
function renderDetails(questionId, result) {
    if (result.status === 'error') {
        return `
            <div class="detail-section">
                <h4>错误信息</h4>
                <div class="error-msg">${escapeHtml(result.error || '未知错误')}</div>
            </div>
            <div class="detail-row">
                <span class="detail-label">运行次数:</span>
                <span class="detail-value">${result.attempts || 1} 次</span>
            </div>
            ${result.sql ? `
            <div class="detail-section">
                <h4>生成的SQL</h4>
                <pre>${escapeHtml(result.sql)}</pre>
            </div>` : ''}
            ${result.query_id ? `
            <div class="detail-section">
                <button class="btn-view-logs" onclick="viewLogs('${questionId}')">查看运行日志</button>
            </div>` : ''}
        `;
    }
    
    if (result.status === 'success') {
        return `
            <div class="detail-row">
                <span class="detail-label">查询结果:</span>
                <span class="detail-value">${result.rowCount || 0} 条记录</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">运行次数:</span>
                <span class="detail-value">${result.attempts || 1} 次</span>
            </div>
            ${result.template_info ? `
            <div class="detail-section">
                <h4>要点概述</h4>
                <div class="summary">
                    <div class="detail-row">
                        <span class="detail-label">模板:</span>
                        <span class="detail-value">${escapeHtml(result.template_info.template_id || 'N/A')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">描述:</span>
                        <span class="detail-value">${escapeHtml(result.template_info.description || 'N/A')}</span>
                    </div>
                    ${result.template_info.params ? `
                    <div class="detail-row">
                        <span class="detail-label">参数:</span>
                        <span class="detail-value">${escapeHtml(JSON.stringify(result.template_info.params, null, 2))}</span>
                    </div>` : ''}
                </div>
            </div>` : ''}
            <div class="detail-section">
                <h4>生成的SQL</h4>
                <pre>${escapeHtml(result.sql || '无SQL')}</pre>
            </div>
            ${result.summary ? `
            <div class="detail-section">
                <h4>AI总结</h4>
                <div class="summary">${formatSummary(result.summary)}</div>
            </div>` : ''}
            ${result.rows && result.rows.length > 0 ? `
            <div class="detail-section">
                <h4>查询结果预览 (前5条)</h4>
                <div style="overflow-x: auto;">
                    ${createTable(result.rows.slice(0, 5))}
                </div>
            </div>` : ''}
            ${result.query_id ? `
            <div class="detail-section">
                <button class="btn-view-logs" onclick="viewLogs('${questionId}')">查看运行日志</button>
            </div>` : ''}
        `;
    }
    
    return '';
}

// HTML转义
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 格式化总结（简化版，从main.js复制）
function formatSummary(summary) {
    if (!summary) return '';
    let text = escapeHtml(summary);
    // 处理换行
    text = text.replace(/\n/g, '<br>');
    return text;
}

// 创建表格
function createTable(rows) {
    if (rows.length === 0) return '<p>暂无数据</p>';
    
    const headers = Object.keys(rows[0]);
    let html = '<table style="width: 100%; border-collapse: collapse; font-size: 12px;"><thead><tr>';
    
    headers.forEach(header => {
        html += `<th style="border: 1px solid #ddd; padding: 8px; background: #f5f5f5; text-align: left;">${escapeHtml(header)}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    rows.forEach(row => {
        html += '<tr>';
        headers.forEach(header => {
            const value = row[header];
            const displayValue = value === null || value === undefined ? '' : String(value);
            html += `<td style="border: 1px solid #ddd; padding: 8px;">${escapeHtml(displayValue)}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    return html;
}

// 查看日志
async function viewLogs(questionId) {
    const result = testResults[questionId];
    if (!result || !result.query_id) {
        alert('没有可用的日志信息');
        return;
    }
    
    try {
        const response = await fetch(`/api/query-logs/${result.query_id}`);
        const data = await response.json();
        
        if (data.success && data.logs) {
            showLogModal(data.logs);
        } else {
            alert('获取日志失败: ' + (data.error || '未知错误'));
        }
    } catch (err) {
        alert('获取日志时出错: ' + err.message);
    }
}

// 显示日志弹窗
function showLogModal(logData) {
    // 创建模态框
    const modal = document.createElement('div');
    modal.className = 'log-modal';
    modal.innerHTML = `
        <div class="log-modal-content">
            <div class="log-modal-header">
                <h3>运行日志</h3>
                <span class="log-modal-close" onclick="this.closest('.log-modal').remove()">&times;</span>
            </div>
            <div class="log-modal-body">
                <div class="log-info">
                    <div class="log-info-item">
                        <strong>问题:</strong> ${escapeHtml(logData.question || 'N/A')}
                    </div>
                    <div class="log-info-item">
                        <strong>时间:</strong> ${escapeHtml(logData.timestamp || 'N/A')}
                    </div>
                    <div class="log-info-item">
                        <strong>状态:</strong> ${logData.success ? '<span style="color: green;">成功</span>' : '<span style="color: red;">失败</span>'}
                    </div>
                </div>
                <div class="log-content">
                    <h4>详细日志:</h4>
                    <pre class="log-text">${escapeHtml(logData.logs ? logData.logs.join('\n') : '无日志')}</pre>
                </div>
            </div>
            <div class="log-modal-footer">
                <button onclick="this.closest('.log-modal').remove()">关闭</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 点击背景关闭
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', initPage);

