// Session variables
let chatHistory = [];

// DOM Elements
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');
const newsFeed = document.getElementById('news-feed');
const clearChatBtn = document.getElementById('clear-chat-btn');

// Configure marked options
marked.setOptions({
    gfm: true,
    breaks: true,
    headerIds: false,
    mangle: false
});

/**
 * Updates the header terminal clock dynamically.
 */
function updateClock() {
    const clock = document.getElementById('clock');
    if (clock) {
        const now = new Date();
        const hrs = String(now.getHours()).padStart(2, '0');
        const mins = String(now.getMinutes()).padStart(2, '0');
        const secs = String(now.getSeconds()).padStart(2, '0');
        clock.textContent = `${hrs}:${mins}:${secs}`;
    }
}
setInterval(updateClock, 1000);
updateClock();

/**
 * Autogrows chat input text area based on line count.
 */
chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

/**
 * Handles Enter key without Shift for form submit.
 */
chatInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

/**
 * Appends a message bubble to the messages list container.
 */
function appendMessage(role, content) {
    // Remove typing indicator if it exists
    hideTypingIndicator();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    if (role === 'system') {
        messageContent.innerHTML = `<span class="system-tag">SYSTEM INITIALIZED</span>${content}`;
    } else if (role === 'assistant') {
        // Parse markdown text using marked library
        messageContent.innerHTML = marked.parse(content);
    } else {
        // User message (treat as plain text)
        const p = document.createElement('p');
        p.textContent = content;
        messageContent.appendChild(p);
    }
    
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    
    // Auto-scroll chat area
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Appends typing indicator dots inside chat list.
 */
function showTypingIndicator() {
    if (document.getElementById('typing-indicator')) return;
    
    const indicatorDiv = document.createElement('div');
    indicatorDiv.id = 'typing-indicator';
    indicatorDiv.className = 'typing-indicator';
    indicatorDiv.innerHTML = `
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
    `;
    
    chatMessages.appendChild(indicatorDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Removes typing indicator from chat list.
 */
function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * Renders list of news headlines in the Portfolio Buzz sidebar.
 */
function updateNewsFeed(newsItems) {
    newsFeed.innerHTML = '';
    
    if (!newsItems || newsItems.length === 0) {
        newsFeed.innerHTML = `
            <div class="empty-news-state">
                <p>No active ticker analysis running.</p>
                <span>Crawl details will populate once a stock query executes.</span>
            </div>
        `;
        return;
    }
    
    newsItems.forEach(item => {
        const card = document.createElement('a');
        card.className = 'news-card';
        card.href = item.link;
        card.target = '_blank';
        card.rel = 'noopener noreferrer';
        
        card.innerHTML = `
            <div class="news-meta">
                <span class="news-source">${item.source}</span>
                <span class="news-time">${item.pub_date}</span>
            </div>
            <div class="news-title" title="${item.title}">${item.title}</div>
            <div class="news-footer">
                <span class="sentiment-badge ${item.sentiment.toLowerCase()}">${item.sentiment}</span>
            </div>
        `;
        newsFeed.appendChild(card);
    });
}

/**
 * Chat Form submission listener.
 */
chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const query = chatInput.value.trim();
    if (!query) return;
    
    // Reset textarea sizing
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    // 1. Render User Message bubble
    appendMessage('user', query);
    
    // 2. Display Typing State
    showTypingIndicator();
    
    // Add user message to history
    chatHistory.push({ role: 'user', content: query });
    
    try {
        // Make endpoint call
        const baseUrl = window.location.protocol === 'file:' ? 'http://127.0.0.1:8080' : '';
        const response = await fetch(`${baseUrl}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: query,
                history: chatHistory
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 3. Render Assistant Response
        appendMessage('assistant', data.response);
        
        // Add assistant response to history
        chatHistory.push({ role: 'assistant', content: data.response });
        
        // 4. Update News Sidebar
        updateNewsFeed(data.news || []);
        
        // 5. Update Interactive Dashboard
        if (data.payload) {
            updateDashboard(data.payload);
        }
        
    } catch (err) {
        console.error('API call failed: ', err);
        appendMessage('assistant', '⚠️ **Error:** Unable to connect to the StockVibe AI Backend. Please ensure the server is running on localhost and try again.');
    }
});

/**
 * Reset terminal click handler.
 */
clearChatBtn.addEventListener('click', () => {
    chatMessages.innerHTML = `
        <div class="message system-message">
            <div class="message-content">
                <span class="system-tag">SYSTEM INITIALIZED</span>
                <p>Welcome to <strong>StockVibe Elite Institutional Terminal</strong>. Enter a stock name or ticker (e.g. <code>TCS</code>, <code>RELIANCE</code>, <code>COAL INDIA</code>, <code>INFY</code>) to launch real-time mathematical valuation, momentum technicals, Google News sentiment scoring, and risk boundaries.</p>
            </div>
        </div>
    `;
    chatHistory = [];
    updateNewsFeed([]);
    
    // Reset dashboard panel to welcome standby state
    dashboardTickerTitle.textContent = "QUANTITATIVE WORKSPACE";
    dashboardStateBadge.textContent = "STANDBY";
    dashboardWelcome.classList.remove('hidden');
    dashboardActive.classList.add('hidden');
    const container = document.getElementById('tradingview-chart-container');
    if (container) container.innerHTML = '';
});

// Cache DOM elements for dashboard
const dashboardPanel = document.getElementById('dashboard-panel');
const chatPanel = document.getElementById('chat-panel');
const buzzPanel = document.getElementById('buzz-panel');

const dashboardWelcome = document.getElementById('dashboard-welcome');
const dashboardActive = document.getElementById('dashboard-active');
const dashboardTickerTitle = document.getElementById('dashboard-ticker-title');
const dashboardStateBadge = document.getElementById('dashboard-state-badge');

const predTakeProfit = document.getElementById('pred-take-profit');
const predCurrentPrice = document.getElementById('pred-current-price');
const predStopLoss = document.getElementById('pred-stop-loss');
const predRangeProgress = document.getElementById('pred-range-progress');
const rangeCurrentMarker = document.getElementById('range-current-marker');
const predVerdict = document.getElementById('pred-verdict');
const predConfidence = document.getElementById('pred-confidence');

const techRegime = document.getElementById('tech-regime');
const techRsi = document.getElementById('tech-rsi');
const techMacd = document.getElementById('tech-macd');
const techEma = document.getElementById('tech-ema');

const fundPe = document.getElementById('fund-pe');
const fundRoe = document.getElementById('fund-roe');
const fundDe = document.getElementById('fund-de');
const fundDiv = document.getElementById('fund-div');

// Quick-links watchlist buttons
document.querySelectorAll('.quick-stock-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const ticker = btn.getAttribute('data-ticker');
        chatInput.value = `Analyze ${ticker}`;
        chatForm.dispatchEvent(new Event('submit'));
        // On mobile, switch to chat panel so user can see it processing
        switchTab('chat');
    });
});

// Mobile Tabs Switching logic
const tabChatBtn = document.getElementById('tab-chat-btn');
const tabDashboardBtn = document.getElementById('tab-dashboard-btn');
const tabNewsBtn = document.getElementById('tab-news-btn');

function switchTab(activeTab) {
    // Remove active classes
    tabChatBtn.classList.remove('active');
    tabDashboardBtn.classList.remove('active');
    tabNewsBtn.classList.remove('active');
    
    chatPanel.classList.add('mobile-hidden');
    dashboardPanel.classList.add('mobile-hidden');
    buzzPanel.classList.add('mobile-hidden');
    
    if (activeTab === 'chat') {
        tabChatBtn.classList.add('active');
        chatPanel.classList.remove('mobile-hidden');
    } else if (activeTab === 'dashboard') {
        tabDashboardBtn.classList.add('active');
        dashboardPanel.classList.remove('mobile-hidden');
        // Re-trigger TradingView resize
        const tvIframe = document.querySelector('#tradingview-chart-container iframe');
        if (tvIframe) {
            tvIframe.style.width = '99%';
            setTimeout(() => tvIframe.style.width = '100%', 50);
        }
    } else if (activeTab === 'news') {
        tabNewsBtn.classList.add('active');
        buzzPanel.classList.remove('mobile-hidden');
    }
}

tabChatBtn.addEventListener('click', () => switchTab('chat'));
tabDashboardBtn.addEventListener('click', () => switchTab('dashboard'));
tabNewsBtn.addEventListener('click', () => switchTab('news'));

// TradingView Widget Loader
function loadTradingViewChart(symbol) {
    const container = document.getElementById('tradingview-chart-container');
    container.innerHTML = '';
    
    let cleanSymbol = symbol;
    if (symbol.endsWith('.NS')) {
        cleanSymbol = "NSE:" + symbol.slice(0, -3);
    } else if (symbol.endsWith('.BO')) {
        cleanSymbol = "BSE:" + symbol.slice(0, -3);
    }
    
    if (window.TradingView) {
        new TradingView.widget({
            "autosize": true,
            "symbol": cleanSymbol,
            "interval": "D",
            "timezone": "Asia/Kolkata",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "enable_publishing": false,
            "hide_side_toolbar": true,
            "allow_symbol_change": false,
            "container_id": "tradingview-chart-container"
        });
    }
}

// Dashboard Updater
function updateDashboard(payload) {
    if (!payload) return;
    
    // Change state and ticker
    dashboardTickerTitle.textContent = `${payload.company_name} (${payload.ticker})`;
    dashboardStateBadge.textContent = "LIVE DATA";
    
    // Pricing
    const price = payload.current_price;
    const sl = payload.risk_map.stop_loss;
    const tp = payload.risk_map.take_profit;
    
    predCurrentPrice.textContent = `₹${price.toFixed(2)}`;
    predStopLoss.textContent = `₹${sl.toFixed(2)}`;
    predTakeProfit.textContent = `₹${tp.toFixed(2)}`;
    
    // Progress calculation for price range marker
    let progressPct = ((price - sl) / (tp - sl)) * 100;
    progressPct = Math.max(0, Math.min(100, progressPct));
    predRangeProgress.style.width = `${progressPct}%`;
    rangeCurrentMarker.style.left = `${progressPct}%`;
    
    // Determine simple verdict/confidence based on indicators
    let verdict = "HOLD";
    let confidence = 65;
    const rsi = payload.technicals.rsi;
    const emaCross = payload.technicals.moving_averages.cross;
    
    if (rsi < 40 && emaCross === "GOLDEN CROSS") {
        verdict = "STRONG BUY";
        confidence = 85;
        predVerdict.style.color = "var(--accent-green)";
    } else if (rsi > 70 && emaCross === "DEATH CROSS") {
        verdict = "STRONG SELL";
        confidence = 80;
        predVerdict.style.color = "#ff5555";
    } else if (rsi < 45) {
        verdict = "ACCUMULATE";
        confidence = 72;
        predVerdict.style.color = "#80ffd4";
    } else if (rsi > 65) {
        verdict = "REDUCE";
        confidence = 70;
        predVerdict.style.color = "#ff8080";
    } else {
        verdict = "HOLD / NEUTRAL";
        confidence = 65;
        predVerdict.style.color = "var(--text-main)";
    }
    
    predVerdict.textContent = verdict;
    predConfidence.textContent = `${confidence}%`;
    
    // Technicals Section
    techRegime.textContent = payload.technicals.adx.regime;
    techRsi.textContent = rsi.toFixed(1);
    techMacd.textContent = payload.technicals.macd.crossover;
    techEma.textContent = `${payload.technicals.moving_averages.cross} (EMA50/200)`;
    
    // Fundamentals Section
    const f = payload.fundamentals;
    fundPe.textContent = f.pe_ratio;
    fundRoe.textContent = f.roe;
    fundDe.textContent = f.de_ratio;
    fundDiv.textContent = f.dividend_yield;
    
    // Toggle panels
    dashboardWelcome.classList.add('hidden');
    dashboardActive.classList.remove('hidden');
    
    // Load TradingView
    loadTradingViewChart(payload.ticker);
    
    // On mobile, automatically show the dashboard/workspace tab when data arrives
    if (window.innerWidth <= 900) {
        switchTab('dashboard');
    }
}
