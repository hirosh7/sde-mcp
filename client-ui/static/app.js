const SEAGLASS_URL = 'http://localhost:8003';

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
        const response = await fetch(`${SEAGLASS_URL}/api/v1/nlquery`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
        
        const data = await response.json();
        
        // Remove loading message
        document.getElementById(loadingId).remove();
        
        if (data.success) {
            addMessage(data.response + `\n\n(Response time: ${elapsed}s)`, 'assistant');
        } else {
            addMessage(`Error: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        document.getElementById(loadingId).remove();
        addMessage(`Network error: ${error.message}`, 'error');
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
    
    return parts.map(part => {
        if (urlRegex.test(part)) {
            urlRegex.lastIndex = 0; // Reset regex state
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

