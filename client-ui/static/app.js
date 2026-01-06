const SEAGLASS_URL = 'http://localhost:8003';

// Session management - generate and persist session_id for conversation context
function getOrCreateSessionId() {
    let sessionId = localStorage.getItem('sde-mcp-session-id');
    if (!sessionId) {
        // Generate a new session ID (UUID v4 format)
        sessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
        localStorage.setItem('sde-mcp-session-id', sessionId);
        console.log(`[Session] Generated new session_id: ${sessionId}`);
    } else {
        console.log(`[Session] Using existing session_id: ${sessionId}`);
    }
    return sessionId;
}

// Load SDE instance info on page load
async function loadInstanceInfo() {
    try {
        const response = await fetch(`${SEAGLASS_URL}/api/v1/sde-instance`);
        const data = await response.json();
        const instanceUrl = data.instance_url || '';
        
        const instanceNameEl = document.getElementById('instance-name');
        if (instanceUrl && instanceUrl !== 'Unknown') {
            // Construct full URL with https://
            const fullUrl = instanceUrl.startsWith('http://') || instanceUrl.startsWith('https://') 
                ? instanceUrl 
                : `https://${instanceUrl}`;
            
            instanceNameEl.textContent = instanceUrl;
            instanceNameEl.href = fullUrl;
            instanceNameEl.title = `Open SDE instance: ${fullUrl}`;
        } else {
            instanceNameEl.textContent = 'Unknown';
            instanceNameEl.href = '#';
            instanceNameEl.title = 'Instance information unavailable';
        }
    } catch (error) {
        const instanceNameEl = document.getElementById('instance-name');
        instanceNameEl.textContent = 'Unknown';
        instanceNameEl.href = '#';
        instanceNameEl.title = 'Failed to load instance info';
        console.error('Failed to load instance info:', error);
    }
}

// Load instance info when page loads
loadInstanceInfo();

document.getElementById('send-btn').addEventListener('click', sendQuery);
document.getElementById('query-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendQuery();
});

document.querySelectorAll('.example-query').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('query-input').value = e.target.textContent;
        sendQuery();
    });
});

async function sendQuery() {
    const input = document.getElementById('query-input');
    const query = input.value.trim();
    if (!query) return;

    // Add user message
    addMessage(query, 'user');
    input.value = '';

    // Show loading
    const loadingId = addMessage('Processing...', 'assistant', true);

    try {
        const startTime = Date.now();
        const sessionId = getOrCreateSessionId();
        console.log(`[Session] Sending query with session_id: ${sessionId}`);
        
        // Always include session_id, even if it might be null/undefined (defensive)
        const payload = { query };
        if (sessionId) {
            payload.session_id = sessionId;
        }
        console.log(`[Session] Payload being sent:`, JSON.stringify(payload));
        
        const response = await fetch(`${SEAGLASS_URL}/api/v1/nlquery`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
        
        const data = await response.json();
        
        // Update session_id if returned (in case server generated a new one)
        // IMPORTANT: Only update if server returned a different session_id
        // If server didn't return session_id, keep using the one we sent
        if (data.session_id) {
            if (data.session_id !== sessionId) {
                console.warn(`[Session] Session ID changed! Old: ${sessionId}, New: ${data.session_id}`);
                localStorage.setItem('sde-mcp-session-id', data.session_id);
            } else {
                console.log(`[Session] Session ID confirmed: ${sessionId}`);
            }
        } else {
            console.warn(`[Session] No session_id in response! Keeping current: ${sessionId}`);
            // Don't clear localStorage - keep using the session_id we sent
        }
        
        // Remove loading message
        document.getElementById(loadingId).remove();
        
        if (data.success) {
            addMessage(data.response + `\n\n(Response time: ${elapsed}s)`, 'assistant');
        } else {
            addMessage(`Error: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        document.getElementById(loadingId).remove();
        console.error(`[Session] Request failed, but preserving session_id: ${sessionId}`);
        addMessage(`Network error: ${error.message}`, 'error');
        // Don't clear session_id on error - preserve it for retry
    }
}

function linkifyUrls(text) {
    // Escape HTML to prevent XSS
    const escapeHtml = (str) => {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    };
    
    // Split by URLs and rebuild with links
    const urlRegex = /(https?:\/\/[^\s<>"']+)/g;
    const parts = text.split(urlRegex);
    
    // Create a non-global regex for testing individual parts
    const urlTest = /^https?:\/\/[^\s<>"']+$/;
    
    return parts.map(part => {
        if (urlTest.test(part)) {
            // Clean up URL - remove trailing punctuation that might not be part of URL
            const cleanUrl = part.replace(/[.,;!?]+$/, '');
            const trailingPunct = part.slice(cleanUrl.length);
            return `<a href="${escapeHtml(cleanUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(cleanUrl)}</a>${escapeHtml(trailingPunct)}`;
        }
        return escapeHtml(part);
    }).join('');
}

function addMessage(text, type, isLoading = false) {
    const messages = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    const id = `msg-${Date.now()}`;
    messageDiv.id = id;
    messageDiv.className = `message ${type}`;
    if (isLoading) messageDiv.classList.add('loading');
    
    // Convert URLs to clickable links
    const htmlContent = linkifyUrls(text);
    messageDiv.innerHTML = htmlContent;
    
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
    return id;
}

