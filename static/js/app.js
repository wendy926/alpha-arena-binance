// 全局变量
let profitChart = null;
let signalChart = null;
let confidenceChart = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initCharts();
    updateData();
    // 每10秒更新一次数据
    setInterval(updateData, 10000);
});

// 初始化图表
function initCharts() {
    // 收益曲线图
    profitChart = echarts.init(document.getElementById('profitChart'));
    
    // 信号分布图
    signalChart = echarts.init(document.getElementById('signalChart'));
    
    // 信心分布图
    confidenceChart = echarts.init(document.getElementById('confidenceChart'));
    
    // 响应窗口大小变化
    window.addEventListener('resize', function() {
        profitChart.resize();
        signalChart.resize();
        confidenceChart.resize();
    });
}

// 更新所有数据
async function updateData() {
    try {
        // 更新AI模型信息
        await updateAIModelInfo();
        
        // 更新仪表板数据
        await updateDashboard();
        
        // 更新收益曲线图
        await updateProfitChart();
        
        // 更新AI决策
        await updateAIDecisions();
        
        // 更新交易记录
        await updateTrades();
        
        // 更新信号统计
        await updateSignalStats();
        
    } catch (error) {
        console.error('数据更新失败:', error);
    }
}

// 更新AI模型信息
async function updateAIModelInfo() {
    try {
        const response = await fetch('/api/ai_model_info');
        const data = await response.json();
        
        // 更新模型名称
        const modelNameMap = {
            'deepseek': 'DeepSeek',
            'qwen': '阿里百炼 Qwen'
        };
        const modelName = modelNameMap[data.provider] || data.provider;
        document.getElementById('aiModelName').textContent = `${modelName} (${data.model})`;
        
        // 更新连接状态
        const statusDot = document.getElementById('aiStatusDot');
        const statusText = document.getElementById('aiStatusText');
        
        // 清除旧的状态类
        statusDot.className = 'status-dot';
        
        // 设置新的状态
        if (data.status === 'connected') {
            statusDot.classList.add('connected');
            statusText.textContent = '已连接';
            statusText.style.color = 'var(--success-color)';
        } else if (data.status === 'error') {
            statusDot.classList.add('error');
            statusText.textContent = '连接失败';
            statusText.style.color = 'var(--danger-color)';
            if (data.error_message) {
                statusText.title = data.error_message; // 鼠标悬停显示错误信息
            }
        } else {
            statusDot.classList.add('unknown');
            statusText.textContent = '检测中';
            statusText.style.color = 'var(--warning-color)';
        }
        
    } catch (error) {
        console.error('AI模型信息更新失败:', error);
        document.getElementById('aiModelName').textContent = 'AI模型加载失败';
        document.getElementById('aiStatusText').textContent = '错误';
    }
}

// 更新仪表板
async function updateDashboard() {
    try {
        const response = await fetch('/api/dashboard');
        const data = await response.json();
        
        // 账户信息
        document.getElementById('usdtBalance').textContent = 
            data.account_info?.usdt_balance ? `$${data.account_info.usdt_balance.toFixed(2)}` : '--';
        document.getElementById('totalEquity').textContent = 
            data.account_info?.total_equity ? `$${data.account_info.total_equity.toFixed(2)}` : '--';
        
        // 配置信息
        document.getElementById('leverage').textContent = 
            data.config?.leverage ? `${data.config.leverage}x` : '--';
        document.getElementById('timeframe').textContent = 
            data.config?.timeframe || '--';
        document.getElementById('tradeMode').textContent = 
            data.config?.test_mode ? '模拟模式' : '实盘模式';
        
        // 当前价格
        if (data.current_price) {
            document.getElementById('currentPrice').textContent = 
                `$${data.current_price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        }
        
        // 持仓信息
        if (data.current_position) {
            const pos = data.current_position;
            const posType = document.getElementById('positionType');
            posType.textContent = pos.side === 'long' ? '多头持仓' : '空头持仓';
            posType.className = `position-type ${pos.side}`;
            
            document.getElementById('positionSize').textContent = `${pos.size} BTC`;
            document.getElementById('entryPrice').textContent = `$${pos.entry_price.toFixed(2)}`;
            
            const pnlElement = document.getElementById('unrealizedPnl');
            pnlElement.textContent = `$${pos.unrealized_pnl.toFixed(2)}`;
            pnlElement.className = `value pnl ${pos.unrealized_pnl >= 0 ? 'positive' : 'negative'}`;
        } else {
            document.getElementById('positionType').textContent = '无持仓';
            document.getElementById('positionType').className = 'position-type';
            document.getElementById('positionSize').textContent = '--';
            document.getElementById('entryPrice').textContent = '--';
            document.getElementById('unrealizedPnl').textContent = '--';
        }
        
        // 绩效统计
        const totalProfitEl = document.getElementById('totalProfit');
        if (data.performance?.total_profit !== undefined) {
            totalProfitEl.textContent = `$${data.performance.total_profit.toFixed(2)}`;
            totalProfitEl.className = `value pnl ${data.performance.total_profit >= 0 ? 'positive' : 'negative'}`;
        }
        
        const winRateVal = data.performance?.win_rate;
        document.getElementById('winRate').textContent =
            (winRateVal !== undefined && winRateVal !== null)
                ? `${Number(winRateVal).toFixed(1)}%`  // 后端已返回百分比值
                : '--';
        document.getElementById('totalTrades').textContent = 
            data.performance?.total_trades || '0';
        
        // 更新时间
        document.getElementById('lastUpdate').textContent = 
            data.last_update || '--';
            
    } catch (error) {
        console.error('仪表板更新失败:', error);
    }
}

// 更新K线图
async function updateKlineChart() {
    try {
        const response = await fetch('/api/kline');
        const data = await response.json();
        
        if (!data || data.length === 0) return;
        
        // 准备K线数据
        const dates = [];
        const klineData = [];
        const volumes = [];
        
        data.forEach(item => {
            const date = new Date(item.timestamp);
            dates.push(date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'}));
            klineData.push([item.open, item.close, item.low, item.high]);
            volumes.push(item.volume);
        });
        
        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                },
                backgroundColor: 'rgba(26, 26, 46, 0.95)',
                borderColor: '#2d2d44',
                textStyle: {
                    color: '#fff'
                }
            },
            legend: {
                data: ['K线', '成交量'],
                textStyle: {
                    color: '#9ca3af'
                }
            },
            grid: [
                {
                    left: '10%',
                    right: '10%',
                    top: '10%',
                    height: '60%'
                },
                {
                    left: '10%',
                    right: '10%',
                    top: '75%',
                    height: '15%'
                }
            ],
            xAxis: [
                {
                    type: 'category',
                    data: dates,
                    scale: true,
                    boundaryGap: false,
                    axisLine: { lineStyle: { color: '#2d2d44' } },
                    axisLabel: { color: '#9ca3af' },
                    splitLine: { show: false },
                    min: 'dataMin',
                    max: 'dataMax'
                },
                {
                    type: 'category',
                    gridIndex: 1,
                    data: dates,
                    scale: true,
                    boundaryGap: false,
                    axisLine: { lineStyle: { color: '#2d2d44' } },
                    axisLabel: { show: false },
                    splitLine: { show: false }
                }
            ],
            yAxis: [
                {
                    scale: true,
                    splitArea: { show: false },
                    axisLine: { lineStyle: { color: '#2d2d44' } },
                    axisLabel: { color: '#9ca3af' },
                    splitLine: { lineStyle: { color: '#2d2d44' } }
                },
                {
                    scale: true,
                    gridIndex: 1,
                    splitNumber: 2,
                    axisLabel: { show: false },
                    axisLine: { show: false },
                    splitLine: { show: false }
                }
            ],
            dataZoom: [
                {
                    type: 'inside',
                    xAxisIndex: [0, 1],
                    start: 50,
                    end: 100
                },
                {
                    show: true,
                    xAxisIndex: [0, 1],
                    type: 'slider',
                    bottom: '5%',
                    start: 50,
                    end: 100,
                    backgroundColor: '#1a1a2e',
                    fillerColor: 'rgba(26, 115, 232, 0.2)',
                    borderColor: '#2d2d44',
                    textStyle: { color: '#9ca3af' }
                }
            ],
            series: [
                {
                    name: 'K线',
                    type: 'candlestick',
                    data: klineData,
                    itemStyle: {
                        color: '#34a853',
                        color0: '#ea4335',
                        borderColor: '#34a853',
                        borderColor0: '#ea4335'
                    }
                },
                {
                    name: '成交量',
                    type: 'bar',
                    xAxisIndex: 1,
                    yAxisIndex: 1,
                    data: volumes,
                    itemStyle: {
                        color: function(params) {
                            const kline = klineData[params.dataIndex];
                            return kline[1] > kline[0] ? '#34a853' : '#ea4335';
                        }
                    }
                }
            ]
        };
        
        klineChart.setOption(option);
        
    } catch (error) {
        console.error('K线图更新失败:', error);
    }
}

// 更新收益曲线图
async function updateProfitChart() {
    try {
        const response = await fetch('/api/profit_curve');
        const data = await response.json();
        
        if (!data || data.length === 0) {
            const option = {
                backgroundColor: 'transparent',
                title: {
                    text: '暂无收益数据，等待交易执行...',
                    left: 'center',
                    top: 'center',
                    textStyle: { color: '#9ca3af', fontSize: 18 }
                }
            };
            profitChart.setOption(option);
            return;
        }
        
        const timestamps = [], profitRates = [], profits = [], equities = [];
        
        data.forEach(item => {
            const date = new Date(item.timestamp);
            timestamps.push(date.toLocaleString('zh-CN', {
                month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
            }));
            profitRates.push(item.profit_rate.toFixed(2));
            profits.push(item.profit.toFixed(2));
            equities.push(item.equity.toFixed(2));
        });
        
        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } },
                backgroundColor: 'rgba(26, 26, 46, 0.95)',
                borderColor: '#2d2d44',
                textStyle: { color: '#fff' },
                formatter: function(params) {
                    let result = params[0].name + '<br/>';
                    params.forEach(param => {
                        result += '<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:' + param.color + ';"></span>';
                        result += param.seriesName + ': ' + param.value;
                        result += (param.seriesName === '收益率') ? '%<br/>' : ' USDT<br/>';
                    });
                    return result;
                }
            },
            legend: {
                data: ['收益率', '累计盈亏', '账户权益'],
                textStyle: { color: '#9ca3af' },
                top: '5%'
            },
            grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: timestamps,
                axisLine: { lineStyle: { color: '#2d2d44' } },
                axisLabel: { color: '#9ca3af', rotate: 45 },
                splitLine: { show: true, lineStyle: { color: '#2d2d44' } }
            },
            yAxis: [
                {
                    type: 'value',
                    name: '收益率(%)',
                    position: 'left',
                    axisLine: { lineStyle: { color: '#2d2d44' } },
                    axisLabel: { color: '#9ca3af', formatter: '{value}%' },
                    splitLine: { lineStyle: { color: '#2d2d44' } }
                },
                {
                    type: 'value',
                    name: '金额(USDT)',
                    position: 'right',
                    axisLine: { lineStyle: { color: '#2d2d44' } },
                    axisLabel: { color: '#9ca3af' },
                    splitLine: { show: false }
                }
            ],
            dataZoom: [
                { type: 'inside', start: 0, end: 100 },
                { show: true, type: 'slider', bottom: '5%', start: 0, end: 100,
                  backgroundColor: '#1a1a2e', fillerColor: 'rgba(26, 115, 232, 0.2)',
                  borderColor: '#2d2d44', textStyle: { color: '#9ca3af' } }
            ],
            series: [
                {
                    name: '收益率',
                    type: 'line',
                    yAxisIndex: 0,
                    data: profitRates,
                    smooth: true,
                    lineStyle: { width: 3, color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
                        colorStops: [{ offset: 0, color: '#1a73e8' }, { offset: 1, color: '#34a853' }] } },
                    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [{ offset: 0, color: 'rgba(26, 115, 232, 0.3)' }, { offset: 1, color: 'rgba(26, 115, 232, 0.05)' }] } },
                    markLine: { silent: true, symbol: 'none', lineStyle: { color: '#9ca3af', type: 'dashed' },
                        data: [{ yAxis: 0, label: { formatter: '盈亏平衡线', position: 'end' } }] }
                },
                {
                    name: '累计盈亏',
                    type: 'line',
                    yAxisIndex: 1,
                    data: profits,
                    smooth: true,
                    lineStyle: { width: 2, color: '#fbbc04' },
                    itemStyle: { color: '#fbbc04' }
                },
                {
                    name: '账户权益',
                    type: 'line',
                    yAxisIndex: 1,
                    data: equities,
                    smooth: true,
                    lineStyle: { width: 2, color: '#34a853', type: 'dashed' },
                    itemStyle: { color: '#34a853' }
                }
            ]
        };
        
        profitChart.setOption(option);
        
    } catch (error) {
        console.error('收益曲线图更新失败:', error);
    }
}

// 更新AI决策
async function updateAIDecisions() {
    try {
        const response = await fetch('/api/ai_decisions');
        
        // 检查响应状态
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // 检查响应内容类型
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('响应不是JSON格式');
        }
        
        // 获取响应文本，然后尝试解析JSON
        const responseText = await response.text();
        if (!responseText || responseText.trim() === '') {
            console.warn('AI决策API返回空响应');
            return;
        }
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (jsonError) {
            console.error('JSON解析失败:', jsonError);
            console.error('响应内容:', responseText);
            return;
        }
        
        // 确保data是数组
        if (!Array.isArray(data)) {
            console.warn('AI决策数据格式错误，期望数组:', data);
            return;
        }
        
        if (data.length === 0) {
            // 显示无数据状态
            const latestDiv = document.getElementById('latestDecision');
            const historyDiv = document.getElementById('aiHistory');
            
            latestDiv.innerHTML = '<div style="color: #9ca3af; text-align: center; padding: 20px;">暂无AI决策数据</div>';
            historyDiv.innerHTML = '<div style="color: #9ca3af; text-align: center; padding: 20px;">暂无历史记录</div>';
            return;
        }
        
        // 显示最新决策
        const latest = data[data.length - 1];
        const latestDiv = document.getElementById('latestDecision');
        
        // 验证最新决策数据完整性
        if (!latest || typeof latest !== 'object') {
            console.warn('最新AI决策数据无效:', latest);
            return;
        }
        
        latestDiv.innerHTML = `
            <div class="ai-signal">
                <span class="signal-badge ${latest.signal || 'HOLD'}">${latest.signal || 'HOLD'}</span>
                <span class="confidence-badge ${latest.confidence || 'LOW'}">${latest.confidence || 'LOW'}</span>
            </div>
            <div class="ai-reason">${latest.reason || '暂无分析'}</div>
            <div class="ai-prices">
                <span class="stop-loss">止损: $${(latest.stop_loss || 0).toFixed(2)}</span>
                <span class="take-profit">止盈: $${(latest.take_profit || 0).toFixed(2)}</span>
            </div>
            <div style="color: #9ca3af; font-size: 0.85em; margin-top: 10px;">
                ${latest.timestamp || '未知时间'}
            </div>
        `;
        
        // 显示历史决策
        const historyDiv = document.getElementById('aiHistory');
        const historyData = data.slice(-10).reverse().slice(1);
        
        const historyHTML = historyData.map(decision => {
            if (!decision || typeof decision !== 'object') return '';
            return `
                <div class="ai-history-item">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span class="signal-badge ${decision.signal || 'HOLD'}" style="font-size: 0.8em; padding: 4px 10px;">${decision.signal || 'HOLD'}</span>
                        <span style="color: #9ca3af; font-size: 0.8em;">${decision.timestamp || '未知时间'}</span>
                    </div>
                    <div style="color: #9ca3af;">${decision.reason || '暂无分析'}</div>
                </div>
            `;
        }).filter(html => html !== '').join('');
        
        historyDiv.innerHTML = historyHTML || '<div style="color: #9ca3af; text-align: center; padding: 20px;">暂无历史记录</div>';
        
    } catch (error) {
        console.error('AI决策更新失败:', error);
        
        // 显示错误状态
        const latestDiv = document.getElementById('latestDecision');
        const historyDiv = document.getElementById('aiHistory');
        
        if (latestDiv) {
            latestDiv.innerHTML = '<div style="color: #ef4444; text-align: center; padding: 20px;">AI决策数据加载失败</div>';
        }
        if (historyDiv) {
            historyDiv.innerHTML = '<div style="color: #ef4444; text-align: center; padding: 20px;">历史数据加载失败</div>';
        }
    }
}

// 更新交易记录
async function updateTrades() {
    try {
        const response = await fetch('/api/trades');
        const data = await response.json();
        
        const tbody = document.getElementById('tradesBody');
        
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">暂无交易记录</td></tr>';
            return;
        }
        
        const rows = data.slice(-20).reverse().map(trade => `
            <tr>
                <td>${trade.timestamp}</td>
                <td><span class="signal-badge ${trade.signal}" style="font-size: 0.8em; padding: 4px 10px;">${trade.signal}</span></td>
                <td>$${trade.price.toFixed(2)}</td>
                <td>${trade.amount} BTC</td>
                <td><span class="confidence-badge ${trade.confidence}" style="font-size: 0.75em; padding: 3px 8px;">${trade.confidence}</span></td>
                <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${trade.reason}">${trade.reason}</td>
            </tr>
        `).join('');
        
        tbody.innerHTML = rows;
        
    } catch (error) {
        console.error('交易记录更新失败:', error);
    }
}

// 更新信号统计
async function updateSignalStats() {
    try {
        const response = await fetch('/api/signals');
        const data = await response.json();
        
        if (!data) return;
        
        // 信号分布饼图
        const signalOption = {
            backgroundColor: 'transparent',
            title: {
                text: '信号分布',
                left: 'center',
                textStyle: {
                    color: '#9ca3af',
                    fontSize: 16
                }
            },
            tooltip: {
                trigger: 'item',
                backgroundColor: 'rgba(26, 26, 46, 0.95)',
                borderColor: '#2d2d44',
                textStyle: { color: '#fff' }
            },
            legend: {
                orient: 'vertical',
                left: 'left',
                textStyle: { color: '#9ca3af' }
            },
            series: [
                {
                    type: 'pie',
                    radius: '50%',
                    data: [
                        { value: data.signal_stats.BUY || 0, name: 'BUY', itemStyle: { color: '#34a853' } },
                        { value: data.signal_stats.SELL || 0, name: 'SELL', itemStyle: { color: '#ea4335' } },
                        { value: data.signal_stats.HOLD || 0, name: 'HOLD', itemStyle: { color: '#fbbc04' } }
                    ],
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }
            ]
        };
        
        signalChart.setOption(signalOption);
        
        // 信心分布饼图
        const confidenceOption = {
            backgroundColor: 'transparent',
            title: {
                text: '信心分布',
                left: 'center',
                textStyle: {
                    color: '#9ca3af',
                    fontSize: 16
                }
            },
            tooltip: {
                trigger: 'item',
                backgroundColor: 'rgba(26, 26, 46, 0.95)',
                borderColor: '#2d2d44',
                textStyle: { color: '#fff' }
            },
            legend: {
                orient: 'vertical',
                left: 'left',
                textStyle: { color: '#9ca3af' }
            },
            series: [
                {
                    type: 'pie',
                    radius: '50%',
                    data: [
                        { value: data.confidence_stats.HIGH || 0, name: 'HIGH', itemStyle: { color: '#34a853' } },
                        { value: data.confidence_stats.MEDIUM || 0, name: 'MEDIUM', itemStyle: { color: '#fbbc04' } },
                        { value: data.confidence_stats.LOW || 0, name: 'LOW', itemStyle: { color: '#ea4335' } }
                    ],
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }
            ]
        };
        
        confidenceChart.setOption(confidenceOption);
        
    } catch (error) {
        console.error('信号统计更新失败:', error);
    }
}

