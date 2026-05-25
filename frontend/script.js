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
        const response = await fetch('/api/chat', {
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
});
