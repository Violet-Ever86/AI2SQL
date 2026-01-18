const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const micBtn = document.getElementById('micBtn');
const micStatus = document.getElementById('micStatus');
const newChatBtn = document.getElementById('newChatBtn');
const refreshBtn = document.getElementById('refreshBtn');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const results = document.getElementById('results');
const contentArea = document.getElementById('contentArea');
const welcomeMessage = document.getElementById('welcomeMessage');
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const expandSidebarBtn = document.getElementById('expandSidebarBtn');

// 语音录音相关变量（使用 MediaRecorder，录音后可上传给后端 STT）
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

function setMicStatus(message, type = 'info') {
    if (!micStatus) return;
    micStatus.textContent = message || '';
    micStatus.dataset.type = type;
    // 简单颜色提示
    if (type === 'error') {
        micStatus.style.color = '#dc2626';
    } else if (type === 'active') {
        micStatus.style.color = '#16a34a';
    } else {
        micStatus.style.color = '#6b7280';
    }
}

// 保存查询数据，用于延迟渲染和异步获取总结
let cachedQueryData = null;
let summaryPollTimer = null;

// 更新按钮显示状态
function updateButtonVisibility() {
    const isCollapsed = sidebar.classList.contains('collapsed');
    expandSidebarBtn.style.display = isCollapsed ? 'flex' : 'none';
}

// 侧边栏折叠功能
sidebarToggle.addEventListener('click', () => {
    sidebar.classList.add('collapsed');
    localStorage.setItem('sidebarCollapsed', 'true');
    updateButtonVisibility();
});

// 侧边栏展开功能
expandSidebarBtn.addEventListener('click', () => {
    sidebar.classList.remove('collapsed');
    localStorage.setItem('sidebarCollapsed', 'false');
    updateButtonVisibility();
});

// 页面加载时恢复侧边栏状态
window.addEventListener('DOMContentLoaded', () => {
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true') {
        sidebar.classList.add('collapsed');
    }
    updateButtonVisibility();
});

// 发送按钮点击事件
sendBtn.addEventListener('click', handleQuery);

// 新对话按钮
newChatBtn.addEventListener('click', () => {
    resetChat();
});

// 刷新按钮
if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
        location.reload();
    });
}

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

// 使用 MediaRecorder 录音，优先 wav，不支持则 webm
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks = [];
        mediaRecorder = MediaRecorder.isTypeSupported('audio/wav')
            ? new MediaRecorder(stream, { mimeType: 'audio/wav' })
            : new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstart = () => {
            isRecording = true;
            micBtn.classList.add('recording');
            micBtn.title = '正在录音...';
            setMicStatus('正在录音，点击再次停止', 'active');
            if (micStatus) micStatus.classList.add('recording');
        };

        mediaRecorder.onstop = () => {
            isRecording = false;
            micBtn.classList.remove('recording');
            micBtn.title = '语音输入';
            if (micStatus) micStatus.classList.remove('recording');

            if (!audioChunks.length) {
                setMicStatus('录音数据为空', 'error');
                return;
            }

            const mimeType = MediaRecorder.isTypeSupported('audio/wav') ? 'audio/wav' : 'audio/webm';
            const ext = mimeType === 'audio/wav' ? 'wav' : 'webm';
            const audioBlob = new Blob(audioChunks, { type: mimeType });
            audioBlob.fileExt = ext;

            setMicStatus('录音完成，可上传识别', 'info');
            uploadAndRecognize(audioBlob);

            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
    } catch (err) {
        console.error('无法访问麦克风:', err);
        setMicStatus('无法访问麦克风，请检查权限', 'error');
        showError('无法访问麦克风，请检查权限');
    }
}

// 上传音频到后端并填充识别结果
async function uploadAndRecognize(audioBlob) {
    setMicStatus('正在上传并识别...', 'info');
    try {
        const formData = new FormData();
        const ext = audioBlob.fileExt || 'wav';
        formData.append('audio', audioBlob, `recording.${ext}`);

        const resp = await fetch('/api/speech-recognize', {
            method: 'POST',
            body: formData,
        });
        const data = await resp.json();

        if (resp.ok && data.success && data.text) {
            questionInput.value = data.text;
            setMicStatus('识别成功，内容已填入输入框', 'active');
        } else {
            const msg = data.error || '识别失败';
            setMicStatus(msg, 'error');
            showError(msg);
        }
    } catch (err) {
        console.error('上传识别失败', err);
        setMicStatus('网络或服务错误', 'error');
        showError('语音识别失败: ' + err.message);
    }
}

// 停止录音
function stopRecording() {
    if (mediaRecorder && isRecording) {
        setMicStatus('正在停止录音...', 'info');
        mediaRecorder.stop();
    }
}

// 语音按钮点击事件（仅录音，不做浏览器端识别）
micBtn.addEventListener('click', () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setMicStatus('浏览器不支持录音', 'error');
        showError('浏览器不支持录音');
        return;
    }

    if (isRecording) {
        stopRecording();
    } else {
        setMicStatus('正在请求麦克风权限...', 'info');
        startRecording();
    }
});

// 页面加载时给出提示
window.addEventListener('DOMContentLoaded', () => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        setMicStatus('点击麦克风开始录音');
    } else {
        setMicStatus('浏览器不支持录音', 'error');
    }
});

// 重置聊天
function resetChat() {
    questionInput.value = '';
    hideError();
    hideResults();
    hideLoading();
    showWelcome();
    // 清空缓存数据和渲染标记
    cachedQueryData = null;
    const keyInfoText = document.getElementById('keyinfo-text');
    const dataTable = document.getElementById('data-table');
    if (keyInfoText) keyInfoText.dataset.rendered = 'false';
    if (dataTable) dataTable.dataset.rendered = 'false';
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

// 渲染关键信息（延迟渲染）
function renderKeyInfo(forceRerender = false) {
    if (!cachedQueryData) return;
    
    const keyInfoText = document.getElementById('keyinfo-text');
    if (!keyInfoText) return;
    
    // 如果已渲染过且不是强制重新渲染，检查数据是否有更新
    if (keyInfoText.dataset.rendered === 'true' && !forceRerender) {
        // 检查数据是否已更新（通过比较当前数据和已渲染的数据）
        const currentKeyInfo = cachedQueryData.summary?.keyInfo || cachedQueryData.summary?.key_info || '';
        const renderedKeyInfo = keyInfoText.dataset.lastRenderedKeyInfo || '';
        // 如果数据相同，跳过；如果数据不同，强制重新渲染
        if (currentKeyInfo === renderedKeyInfo) {
            return;
        }
        forceRerender = true;
    }
    
    const summaryData = {};
    if (typeof cachedQueryData.summary === 'object' && cachedQueryData.summary !== null) {
        summaryData.keyInfo = cachedQueryData.summary.keyInfo || cachedQueryData.summary.key_info || '';
    }
    
    if (summaryData.keyInfo) {
        keyInfoText.innerHTML = formatSummary(summaryData.keyInfo);
        keyInfoText.dataset.lastRenderedKeyInfo = summaryData.keyInfo;
    } else {
        keyInfoText.innerHTML = '<p style="color: #999;">暂无关键信息</p>';
        keyInfoText.dataset.lastRenderedKeyInfo = '';
    }
    
    keyInfoText.dataset.rendered = 'true';
}

// 渲染查询结果表格（延迟渲染）
function renderDataTable() {
    if (!cachedQueryData) return;
    
    const dataTable = document.getElementById('data-table');
    if (dataTable.dataset.rendered === 'true') return; // 已渲染过，跳过
    
    const data = cachedQueryData;
    
    if (data.rows && data.rows.length > 0) {
        const totalRows = data.rows.length;
        const maxDisplayRows = 50;
        const displayRows = data.rows.slice(0, maxDisplayRows);
        dataTable.innerHTML = createTable(displayRows);
    } else {
        dataTable.innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">暂无数据</p>';
    }
    
    dataTable.dataset.rendered = 'true';
}

// 切换展开/折叠
function toggleSection(section) {
    const content = document.getElementById(`${section}-content`);
    const toggle = document.getElementById(`${section}-toggle`);
    
    if (!content || !toggle) return;
    
    if (content.style.display === 'none') {
        // 展开时，如果是第一次展开，则渲染内容
        if (section === 'keyinfo') {
            renderKeyInfo();
        } else if (section === 'data') {
            renderDataTable();
        } else if (section === 'summary') {
            // 展开总结区域时，如果还没有内容，显示占位
            const summaryText = document.getElementById('summary-text');
            if (!summaryText.innerHTML) {
                summaryText.innerHTML = '<p style="color: #999;">正在生成总结...</p>';
            }
        }
        
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
    // 停止上一次的总结轮询
    if (summaryPollTimer) {
        clearTimeout(summaryPollTimer);
        summaryPollTimer = null;
    }
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
    // 保存数据供延迟渲染使用
    cachedQueryData = data;
    // 直接使用结构化的summary数据（已经是字典格式）
    let summaryData = {};
    
    // 兼容处理：如果summary是字符串（旧格式），尝试解析；如果是对象（新格式），直接使用
    let charts = [];
    if (typeof data.summary === 'string') {
        // 向后兼容：如果后端返回的是字符串，尝试解析
        const summaryMatch = data.summary.match(/1[\.、]\s*总结内容\s*[:：]?\s*\n?([\s\S]*?)(?=\n\s*2[\.、]|$)/i);
        const keyInfoMatch = data.summary.match(/2[\.、]\s*关键信息\s*[:：]?\s*\n?([\s\S]*?)(?=\n\s*3[\.、]|$)/i);
        summaryData = {
            summaryContent: summaryMatch ? summaryMatch[1].trim() : data.summary,
            keyInfo: keyInfoMatch ? keyInfoMatch[1].trim() : '',
            recordOverview: ''
        };
        charts = [];
    } else if (typeof data.summary === 'object' && data.summary !== null) {
        // 新格式：直接使用结构化数据
        summaryData = {
            summaryContent: data.summary.summaryContent || data.summary.summary_content || '',
            keyInfo: data.summary.keyInfo || data.summary.key_info || '',
            recordOverview: data.summary.recordOverview || data.summary.record_overview || ''
        };
        // 获取图表数组
        charts = data.summary.charts || [];
    } else {
        summaryData = {
            summaryContent: '',
            keyInfo: '',
            recordOverview: ''
        };
        charts = [];
    }
    
    // 显示总结内容（只显示summaryContent部分）
    const summaryText = document.getElementById('summary-text');
    const summaryContent = summaryData.summaryContent;
    const summaryStatus = data.summary_status || 'pending';

    // 初始状态：折叠总结卡片，显示占位提示
    const summaryContentDiv = document.getElementById('summary-content');
    const summaryToggle = document.getElementById('summary-toggle');
    if (summaryContentDiv && summaryToggle) {
        summaryContentDiv.style.display = 'none';
        summaryToggle.textContent = '▼';
    }

    if (summaryStatus === 'done' && summaryContent) {
        // 如果后端已经生成好了总结（例如刷新页面后的重放），直接渲染并展开
        renderSummaryArea(summaryData, charts);
        if (summaryContentDiv && summaryToggle) {
            summaryContentDiv.style.display = 'block';
            summaryToggle.textContent = '▲';
        }
    } else {
        // 总结尚未就绪，显示占位文本，并启动轮询
        summaryText.innerHTML = '<p style="color: #999;">正在生成总结...</p>';
        if (data.query_id) {
            startSummaryPolling(data.query_id);
        }
    }
    
    // 关键信息和查询结果延迟渲染，只更新标题和计数
    // 关键信息：只更新标题，内容在点击时渲染
    const keyInfoText = document.getElementById('keyinfo-text');
    if (keyInfoText) {
        keyInfoText.innerHTML = ''; // 清空，延迟渲染
        keyInfoText.dataset.rendered = 'false'; // 重置渲染标志
        keyInfoText.dataset.lastRenderedKeyInfo = ''; // 清空上次渲染的数据
    }
    
    // 查询结果：只更新计数，表格在点击时渲染
    const rowCount = document.getElementById('row-count');
    const dataTable = document.getElementById('data-table');
    
    if (data.rows && data.rows.length > 0) {
        const totalRows = data.rows.length;
        const maxDisplayRows = 50;
        
        if (totalRows > maxDisplayRows) {
            rowCount.textContent = `(显示前${maxDisplayRows}条，共${totalRows}条)`;
        } else {
            rowCount.textContent = `(${totalRows} 条)`;
        }
        
        // 直接渲染表格，并展开“查询结果”区域（先给用户看数据）
        const displayRows = data.rows.slice(0, maxDisplayRows);
        dataTable.innerHTML = createTable(displayRows);
        dataTable.dataset.rendered = 'true';

        const dataContent = document.getElementById('data-content');
        const dataToggle = document.getElementById('data-toggle');
        if (dataContent && dataToggle) {
            dataContent.style.display = 'block';
            dataToggle.textContent = '▲';
        }
    } else {
        rowCount.textContent = '(0 条)';
        dataTable.innerHTML = '';
    }
    
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

// 渲染总结区域（文本 + 图表）
function renderSummaryArea(summaryData, charts) {
    const summaryText = document.getElementById('summary-text');
    if (!summaryText) return;

    let summaryHTML = '';
    if (summaryData.summaryContent) {
        summaryHTML = formatSummary(summaryData.summaryContent);
    } else {
        summaryHTML = '<p style="color: #999;">暂无总结内容</p>';
    }

    if (charts && charts.length > 0) {
        // 先设置HTML内容
        summaryText.innerHTML = summaryHTML;

        // 然后在总结内容后面添加图表
        charts.forEach((chartConfig, index) => {
            const chartContainer = createChartContainer(chartConfig, index);
            summaryText.appendChild(chartContainer);
        });
    } else {
        summaryText.innerHTML = summaryHTML;
    }
}

// 启动轮询后端总结接口
function startSummaryPolling(queryId) {
    const pollInterval = 2000; // 2 秒轮询一次

    async function poll() {
        try {
            const resp = await fetch(`/api/query-summary/${queryId}`);
            if (!resp.ok) {
                throw new Error('获取总结失败');
            }
            const data = await resp.json();

            if (data.status === 'done') {
                // 更新缓存数据中的summary
                if (!cachedQueryData) {
                    cachedQueryData = {};
                }
                cachedQueryData.summary = data.summary || {};

                const charts = (data.summary && data.summary.charts) ? data.summary.charts : [];
                const summaryData = {
                    summaryContent: data.summary.summaryContent || data.summary.summary_content || '',
                    keyInfo: data.summary.keyInfo || data.summary.key_info || '',
                    recordOverview: data.summary.recordOverview || data.summary.record_overview || ''
                };

                // 渲染总结并自动展开
                renderSummaryArea(summaryData, charts);
                const summaryContentDiv = document.getElementById('summary-content');
                const summaryToggle = document.getElementById('summary-toggle');
                if (summaryContentDiv && summaryToggle) {
                    summaryContentDiv.style.display = 'block';
                    summaryToggle.textContent = '▲';
                }

                // 同时收起“查询结果”区域
                const dataContent = document.getElementById('data-content');
                const dataToggle = document.getElementById('data-toggle');
                if (dataContent && dataToggle) {
                    dataContent.style.display = 'none';
                    dataToggle.textContent = '▼';
                }

                // 如果关键信息区域已经展开，立即重新渲染（因为数据已更新）
                const keyInfoContent = document.getElementById('keyinfo-content');
                if (keyInfoContent && keyInfoContent.style.display !== 'none') {
                    renderKeyInfo(true); // 强制重新渲染
                }

                summaryPollTimer = null;
                return;
            }

            if (data.status === 'error') {
                const summaryText = document.getElementById('summary-text');
                if (summaryText) {
                    summaryText.innerHTML = `<p style="color: #f97316;">总结生成失败：${data.error || '未知错误'}</p>`;
                }
                summaryPollTimer = null;
                return;
            }

            // 仍在 pending 状态，继续轮询
            summaryPollTimer = setTimeout(poll, pollInterval);
        } catch (e) {
            console.error('轮询总结接口失败', e);
            summaryPollTimer = null;
        }
    }

    // 启动第一次轮询
    summaryPollTimer = setTimeout(poll, pollInterval);
}

// 解析图表指令
function parseChartInstructions(text) {
    const parts = [];
    let lastIndex = 0;
    
    // 查找所有 {"chart": 的位置
    const chartStartRegex = /\{"chart":\s*\{/g;
    let match;
    
    while ((match = chartStartRegex.exec(text)) !== null) {
        const startIndex = match.index;
        
        // 添加图表前的文本
        if (startIndex > lastIndex) {
            parts.push({
                type: 'text',
                content: text.substring(lastIndex, startIndex)
            });
        }
        
        // 从 {"chart": 开始，找到完整的JSON对象
        let braceCount = 0;
        let inString = false;
        let escapeNext = false;
        let jsonEndIndex = startIndex;
        
        for (let i = startIndex; i < text.length; i++) {
            const char = text[i];
            
            if (escapeNext) {
                escapeNext = false;
                continue;
            }
            
            if (char === '\\') {
                escapeNext = true;
                continue;
            }
            
            if (char === '"' && !escapeNext) {
                inString = !inString;
                continue;
            }
            
            if (!inString) {
                if (char === '{') {
                    braceCount++;
                } else if (char === '}') {
                    braceCount--;
                    if (braceCount === 0) {
                        jsonEndIndex = i + 1;
                        break;
                    }
                }
            }
        }
        
        // 提取JSON字符串
        const jsonStr = text.substring(startIndex, jsonEndIndex);
        
        // 尝试解析JSON
        try {
            const chartConfig = JSON.parse(jsonStr);
            if (chartConfig.chart && chartConfig.chart.type && chartConfig.chart.data) {
                // 验证数据格式
                if (Array.isArray(chartConfig.chart.data) && chartConfig.chart.data.length > 0) {
                    parts.push({
                        type: 'chart',
                        config: chartConfig.chart
                    });
                    lastIndex = jsonEndIndex;
                } else {
                    console.warn('图表数据为空或格式不正确:', chartConfig.chart);
                    parts.push({
                        type: 'text',
                        content: jsonStr
                    });
                    lastIndex = jsonEndIndex;
                }
            } else {
                // 如果格式不对，当作普通文本处理
                parts.push({
                    type: 'text',
                    content: jsonStr
                });
                lastIndex = jsonEndIndex;
            }
        } catch (e) {
            console.error('图表配置解析失败:', e, jsonStr);
            // 解析失败，当作普通文本处理
            parts.push({
                type: 'text',
                content: jsonStr
            });
            lastIndex = jsonEndIndex;
        }
    }
    
    // 添加剩余文本
    if (lastIndex < text.length) {
        parts.push({
            type: 'text',
            content: text.substring(lastIndex)
        });
    }
    
    return parts.length > 0 ? parts : [{ type: 'text', content: text }];
}

// 创建图表容器和渲染图表
function createChartContainer(chartConfig, index) {
    const chartContainer = document.createElement('div');
    chartContainer.className = 'chart-container';
    chartContainer.style.cssText = 'margin: 20px 0; padding: 20px; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb; position: relative; height: 400px;';
    
    const chartId = `chart-container-${Date.now()}-${index}`;
    chartContainer.id = chartId;
    
    // 创建占位符
    const placeholder = document.createElement('div');
    placeholder.className = 'chart-placeholder';
    placeholder.textContent = '正在加载图表...';
    chartContainer.appendChild(placeholder);
    
    // 使用setTimeout确保DOM已更新后再渲染图表
    setTimeout(() => {
        const container = document.getElementById(chartId);
        if (container) {
            // 移除占位符
            const placeholder = container.querySelector('.chart-placeholder');
            if (placeholder) {
                placeholder.remove();
            }
            
            // 渲染图表
            const canvas = renderChart(chartConfig, chartId);
            container.appendChild(canvas);
        }
    }, 100);
    
    return chartContainer;
}

// 渲染图表（核心函数）
function renderChart(config, containerId) {
    const canvas = document.createElement('canvas');
    const chartId = `chart-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    canvas.id = chartId;
    
    // 验证配置
    if (!config || !config.type || !config.data || !Array.isArray(config.data) || config.data.length === 0) {
        console.error('图表配置无效:', config);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'chart-error';
        errorDiv.textContent = '图表配置无效';
        return errorDiv;
    }
    
    // 准备数据
    const labels = config.data.map(item => item.label || String(item.value));
    const values = config.data.map(item => {
        const val = item.value;
        return typeof val === 'number' ? val : parseFloat(val) || 0;
    });
    
    // 获取颜色
    const colors = getChartColors(config.type, values.length);
    const borderColors = getChartColors(config.type, values.length, true);
    
    // 根据图表类型创建配置
    let chartConfig = {
        type: config.type,
        data: {
            labels: labels,
            datasets: [{
                label: config.title || '数据',
                data: values,
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: config.type === 'pie' || config.type === 'area' ? 2 : 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: !!config.title,
                    text: config.title || '',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: config.type === 'pie' || config.type === 'doughnut',
                    position: 'bottom'
                }
            },
            scales: config.type !== 'pie' && config.type !== 'doughnut' ? {
                x: {
                    title: {
                        display: !!config.xLabel,
                        text: config.xLabel || ''
                    }
                },
                y: {
                    title: {
                        display: !!config.yLabel,
                        text: config.yLabel || ''
                    },
                    beginAtZero: true
                }
            } : {}
        }
    };
    
    // 创建图表
    try {
        new Chart(canvas, chartConfig);
        return canvas;
    } catch (e) {
        console.error('图表渲染失败:', e, config);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'chart-error';
        errorDiv.textContent = '图表渲染失败: ' + e.message;
        return errorDiv;
    }
}

// 获取图表颜色
function getChartColors(type, count, isBorder = false) {
    const colors = [
        'rgba(79, 70, 229, 0.8)',   // indigo
        'rgba(124, 58, 237, 0.8)',  // purple
        'rgba(236, 72, 153, 0.8)',  // pink
        'rgba(239, 68, 68, 0.8)',   // red
        'rgba(245, 158, 11, 0.8)',  // amber
        'rgba(34, 197, 94, 0.8)',   // green
        'rgba(59, 130, 246, 0.8)',  // blue
        'rgba(168, 85, 247, 0.8)',  // violet
        'rgba(251, 146, 60, 0.8)',  // orange
        'rgba(14, 165, 233, 0.8)',  // sky
    ];
    
    const borderColors = colors.map(c => c.replace('0.8', '1'));
    
    if (type === 'pie' || type === 'doughnut') {
        return isBorder ? borderColors.slice(0, count) : colors.slice(0, count);
    }
    
    // 对于bar/line/area，使用渐变或单一颜色
    if (type === 'area') {
        return isBorder ? borderColors[0] : colors[0].replace('0.8', '0.5');
    }
    
    return isBorder ? borderColors[0] : colors[0];
}

// 格式化总结（支持Markdown格式和图表）
function formatSummary(summary) {
    if (!summary) return '<p>暂无总结</p>';
    
    // 先解析图表指令（在HTML转义之前，因为JSON中的引号不能被转义）
    const parts = parseChartInstructions(summary);
    
    let result = '';
    let chartIndex = 0;
    
    parts.forEach(part => {
        if (part.type === 'text') {
            // 处理文本部分（原有的Markdown处理）
            // 对文本部分进行HTML转义
            let processedText = escapeHtml(part.content);
            
            // 处理表格（必须在其他处理之前）
            const lines = processedText.split('\n');
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
    
            processedText = processedLines.join('\n');
    
    // 处理标题
            processedText = processedText.replace(/^### (.*$)/gim, '<h3>$1</h3>');
            processedText = processedText.replace(/^## (.*$)/gim, '<h2>$1</h2>');
            processedText = processedText.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // 处理粗体
            processedText = processedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // 处理列表项
            const finalLines = processedText.split('\n');
    let inList = false;
            let textResult = [];
    
    for (let i = 0; i < finalLines.length; i++) {
        const line = finalLines[i];
        if (line.trim().match(/^\- /)) {
            if (!inList) {
                        textResult.push('<ul>');
                inList = true;
            }
                    textResult.push('<li>' + line.replace(/^\- /, '') + '</li>');
        } else {
            if (inList) {
                        textResult.push('</ul>');
                inList = false;
            }
                    textResult.push(line);
        }
    }
    if (inList) {
                textResult.push('</ul>');
    }
            processedText = textResult.join('\n');
    
    // 处理换行
            processedText = processedText.replace(/\n/g, '<br>');
            
            result += processedText;
        } else if (part.type === 'chart') {
            // 渲染图表
            const chartContainer = document.createElement('div');
            chartContainer.className = 'chart-container';
            chartContainer.style.cssText = 'margin: 20px 0; padding: 20px; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb; position: relative; height: 400px;';
            
            const chartId = `chart-container-${Date.now()}-${chartIndex++}`;
            chartContainer.id = chartId;
            
            // 创建占位符，稍后渲染
            const placeholder = document.createElement('div');
            placeholder.className = 'chart-placeholder';
            placeholder.textContent = '正在加载图表...';
            chartContainer.appendChild(placeholder);
            
            // 使用setTimeout确保DOM已更新后再渲染图表
            setTimeout(() => {
                const container = document.getElementById(chartId);
                if (container) {
                    // 移除占位符
                    const placeholder = container.querySelector('.chart-placeholder');
                    if (placeholder) {
                        placeholder.remove();
                    }
                    
                    // 渲染图表
                    const canvas = renderChart(part.config, chartId);
                    container.appendChild(canvas);
                }
            }, 100);
            
            result += chartContainer.outerHTML;
        }
    });
    
    return result || '<p>暂无总结</p>';
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
