// Bike Share Analytics Assistant Frontend
class BikeShareAssistant {
    constructor() {
        this.chatContainer = document.getElementById('chat-container');
        this.chatMessages = document.getElementById('chat-messages');
        this.welcomeSection = document.getElementById('welcome-section');
        this.queryForm = document.getElementById('query-form');
        this.questionInput = document.getElementById('question-input');
        this.submitBtn = document.getElementById('submit-btn');
        this.loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        this.queryForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleQuery();
        });
        
        // Enable/disable submit button based on input
        this.questionInput.addEventListener('input', () => {
            const hasText = this.questionInput.value.trim().length > 0;
            this.submitBtn.disabled = !hasText;
        });
        
        // Focus on input when page loads
        this.questionInput.focus();
    }
    
    async handleQuery() {
        const question = this.questionInput.value.trim();
        if (!question) return;
        
        // Hide welcome section and show chat
        this.showChatInterface();
        
        // Add user message
        this.addMessage(question, 'user');
        
        // Clear input and show loading
        this.questionInput.value = '';
        this.submitBtn.disabled = true;
        this.loadingModal.show();
        
        try {
            // Send query to backend
            const response = await fetch('/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question })
            });
            
            const data = await response.json();
            
            // Hide loading modal
            this.loadingModal.hide();
            
            if (data.error) {
                this.addErrorMessage(data.error, data.sql);
            } else {
                this.addSuccessMessage(data.result, data.sql, question);
            }
            
        } catch (error) {
            this.loadingModal.hide();
            this.addErrorMessage(`Network error: ${error.message}`);
        }
    }
    
    showChatInterface() {
        if (this.welcomeSection.style.display !== 'none') {
            this.welcomeSection.style.display = 'none';
            this.chatContainer.style.display = 'flex';
        }
    }
    
    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message mb-3`;
        
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="d-flex justify-content-end">
                    <div class="card bg-primary text-white" style="max-width: 70%;">
                        <div class="card-body py-2 px-3">
                            <p class="mb-0">${this.escapeHtml(content)}</p>
                        </div>
                    </div>
                </div>
            `;
        }
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addSuccessMessage(result, sql, originalQuestion) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message mb-3';
        
        let resultDisplay;
        if (typeof result === 'number' || typeof result === 'string') {
            resultDisplay = `<div class="result-display">
                <h5 class="mb-2" style="color: #ffffff !important;"><i data-feather="check-circle" class="me-2"></i>Answer</h5>
                <p class="mb-0 fs-4" style="color: #ffffff !important; font-weight: bold;">${result}</p>
            </div>`;
        } else if (Array.isArray(result) && result.length > 0) {
            resultDisplay = `<div class="result-display">
                <h5 class="mb-2" style="color: #ffffff !important;"><i data-feather="database" class="me-2"></i>Results (${result.length} records)</h5>
                <div style="color: #ffffff !important;">
                    ${this.formatTableResult(result)}
                </div>
            </div>`;
        } else {
            resultDisplay = `<div class="alert alert-warning mb-3">
                <h5 class="alert-heading" style="color: #ffffff !important;"><i data-feather="info" class="me-2"></i>No Results</h5>
                <p class="mb-0" style="color: #ffffff !important;">No data found matching your criteria.</p>
            </div>`;
        }
        
        messageDiv.innerHTML = `
            <div class="d-flex justify-content-start">
                <div class="card" style="max-width: 90%;">
                    <div class="card-body">
                        ${resultDisplay}
                        
                        <details class="mt-3">
                            <summary class="small cursor-pointer" style="color: rgba(255,255,255,0.7) !important;">
                                <i data-feather="code" class="me-1"></i>
                                View SQL Query
                            </summary>
                            <div class="mt-2">
                                <pre class="p-2 rounded small" style="background: rgba(255,255,255,0.1); color: #ffffff !important;"><code>${this.escapeHtml(sql)}</code></pre>
                            </div>
                        </details>
                    </div>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        
        // Re-render feather icons
        feather.replace();
        this.scrollToBottom();
    }
    
    addErrorMessage(error, sql = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message mb-3';
        
        let sqlSection = '';
        if (sql) {
            sqlSection = `
                <details class="mt-3">
                    <summary class="small cursor-pointer" style="color: rgba(255,255,255,0.7) !important;">
                        <i data-feather="code" class="me-1"></i>
                        View Generated SQL
                    </summary>
                    <div class="mt-2">
                        <pre class="p-2 rounded small" style="background: rgba(255,255,255,0.1); color: #ffffff !important;"><code>${this.escapeHtml(sql)}</code></pre>
                    </div>
                </details>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="d-flex justify-content-start">
                <div class="card" style="max-width: 90%;">
                    <div class="card-body">
                        <div class="error-display">
                            <h5 class="mb-2" style="color: #ffffff !important;">
                                <i data-feather="alert-circle" class="me-2"></i>
                                Error Processing Query
                            </h5>
                            <p class="mb-0" style="color: #ffffff !important; font-weight: 500;">${this.escapeHtml(error)}</p>
                        </div>
                        ${sqlSection}
                    </div>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        
        // Re-render feather icons
        feather.replace();
        this.scrollToBottom();
    }
    
    formatTableResult(data) {
        if (!data || data.length === 0) {
            return '<p>No data to display</p>';
        }
        
        const keys = Object.keys(data[0]);
        let html = '<div class="table-responsive"><table class="table table-sm table-striped" style="color: #ffffff !important;">';
        
        // Header
        html += '<thead><tr>';
        keys.forEach(key => {
            html += `<th>${this.escapeHtml(key)}</th>`;
        });
        html += '</tr></thead>';
        
        // Body
        html += '<tbody>';
        data.slice(0, 10).forEach(row => { // Limit to 10 rows for display
            html += '<tr>';
            keys.forEach(key => {
                let value = row[key];
                if (value === null || value === undefined) {
                    value = '<em class="text-muted">null</em>';
                } else {
                    value = this.escapeHtml(String(value));
                }
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody></table></div>';
        
        if (data.length > 10) {
            html += `<p class="small mt-2" style="color: rgba(255,255,255,0.7) !important;">Showing first 10 of ${data.length} results</p>`;
        }
        
        return html;
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global function for example queries
function setExampleQuery(query) {
    document.getElementById('question-input').value = query;
    document.getElementById('submit-btn').disabled = false;
    document.getElementById('question-input').focus();
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new BikeShareAssistant();
});
