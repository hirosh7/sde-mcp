const SEAGLASS_URL = 'http://localhost:8003';

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

function addMessage(text, type, isLoading = false) {
    const messages = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    const id = `msg-${Date.now()}`;
    messageDiv.id = id;
    messageDiv.className = `message ${type}`;
    if (isLoading) messageDiv.classList.add('loading');
    messageDiv.textContent = text;
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
    return id;
}

