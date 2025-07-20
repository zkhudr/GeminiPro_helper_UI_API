// enhanced_webui_v2.js - Refactored for a unified and robust architecture

// ========================================================================
// The Main UI Class - Manages all UI state and component interactions
// ========================================================================
class EnhancedGeminiWebUI {
    constructor() {
        this.autoApproveMode = false;
        this.currentProjectPath = null;
        this.availableTools = [];
        this.workflowTemplates = [];

        this.initializeUI();
        this.setupKeyboardShortcuts();
    }

    initializeUI() {
        this.addToolPanel();
        this.addWorkflowPanel();
        this.addContextPanel();
        this.addMemoryPanel();
        this.setupEnhancedInputArea();
    }

    addToolPanel() {
        const controls = document.getElementById('controls');
        const toolPanel = document.createElement('div');
        toolPanel.id = 'tool-panel';
        toolPanel.innerHTML = `
            <div style="background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                <h4>🔧 Available Tools</h4>
                <div id="tools-list" style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;"></div>
                <div style="margin-top: 10px;">
                    <label style="font-size: 12px;">
                        <input type="checkbox" id="auto-approve-tools" onchange="ui.toggleAutoApprove()"> Auto-approve safe tools
                    </label>
                </div>
            </div>
        `;
        controls.insertBefore(toolPanel, document.getElementById('file-controls'));
    }

    addWorkflowPanel() {
        const controls = document.getElementById('controls');
        const workflowPanel = document.createElement('div');
        workflowPanel.id = 'workflow-panel';
        workflowPanel.innerHTML = `
            <div style="background: #e8f5e8; border: 1px solid #c8e6c9; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                <h4>⚡ Workflow Templates</h4>
                <div id="workflow-list" style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;"></div>
                <div style="margin-top: 10px;">
                    <input type="text" id="custom-workflow-prompt" placeholder="Custom instructions for workflow..." 
                           style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px;">
                </div>
            </div>
        `;
        controls.insertBefore(workflowPanel, document.getElementById('tool-panel'));
    }

    addContextPanel() {
        const chatContainer = document.getElementById('chat-container');
        const contextPanel = document.createElement('div');
        contextPanel.id = 'context-panel';
        contextPanel.style.display = 'none';
        contextPanel.innerHTML = `
            <div style="position: absolute; top: 10px; right: 10px; width: 300px; background: rgba(255,255,255,0.95); 
                        border: 1px solid #ddd; border-radius: 8px; padding: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); z-index: 100;">
                <h4>📋 Project Context</h4>
                <div id="context-summary" style="font-size: 12px; color: #666; margin-top: 8px;"></div>
                <button onclick="ui.hideContextPanel()" style="position: absolute; top: 5px; right: 5px; 
                        background: none; border: none; font-size: 18px; cursor: pointer;">×</button>
            </div>
        `;
        chatContainer.style.position = 'relative';
        chatContainer.appendChild(contextPanel);
    }

    addMemoryPanel() {
        const controls = document.getElementById('controls');
        const memoryPanel = document.createElement('div');
        memoryPanel.id = 'memory-panel';
        memoryPanel.innerHTML = `
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                <h4>🧠 Memory</h4>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <input type="text" id="memory-search" placeholder="Search memory..." 
                           style="flex: 1; padding: 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px;">
                    <button onclick="ui.searchMemory()" style="padding: 6px 12px; background: #ffc107; border: none; border-radius: 4px; cursor: pointer;">Search</button>
                </div>
                <div id="memory-results" style="margin-top: 10px; max-height: 150px; overflow-y: auto; font-size: 12px;"></div>
            </div>
        `;
        controls.insertBefore(memoryPanel, document.getElementById('workflow-panel'));
    }

    setupEnhancedInputArea() {
        const inputArea = document.getElementById('input-area');
        const suggestions = document.createElement('div');
        suggestions.id = 'command-suggestions';
        suggestions.style.display = 'none';
        suggestions.innerHTML = `
            <div style="background: white; border: 1px solid #ddd; border-radius: 4px; padding: 8px; 
                        position: absolute; bottom: 100%; left: 0; right: 0; box-shadow: 0 -2px 8px rgba(0,0,0,0.1);">
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Quick Commands:</div>
                <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                    <button onclick="ui.insertCommand('/tools')" class="suggestion-btn">📋 /tools</button>
                    <button onclick="ui.insertCommand('/memory')" class="suggestion-btn">🧠 /memory</button>
                    <button onclick="ui.insertCommand('/context')" class="suggestion-btn">📁 /context</button>
                    <button onclick="ui.insertCommand('#remember ')" class="suggestion-btn">💾 #remember</button>
                </div>
            </div>
        `;
        inputArea.style.position = 'relative';
        inputArea.appendChild(suggestions);

        const messageInput = document.getElementById('message-input');
        messageInput.addEventListener('input', (e) => {
            suggestions.style.display = (e.target.value.startsWith('/') || e.target.value.startsWith('#')) ? 'block' : 'none';
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.stopCurrentOperation();
            else if (e.ctrlKey && e.key === 'r') { e.preventDefault(); this.showFullOutput(); }
            else if (e.shiftKey && e.key === 'Tab') { e.preventDefault(); this.toggleAutoApprove(); }
            else if (e.ctrlKey && e.key === 'k') { e.preventDefault(); clearChat(); }
            else if (e.ctrlKey && e.key === ';') { e.preventDefault(); this.showContextPanel(); }
        });
    }

    async refreshAgentUI() {
        try {
            const response = await apiCall('initialize_enhanced_session', {});
            if (response.status === 'success') {
                this.availableTools = response.features.tools_available || [];
                this.workflowTemplates = response.features.workflow_templates || [];
                this.updateToolsDisplay();
                this.updateWorkflowsDisplay();
            } else {
                addMessage('error', `Failed to refresh agent UI: ${response.message}`);
            }
        } catch (error) {
            addMessage('error', `Error refreshing agent UI: ${error.message}`);
        }
    }

    updateToolsDisplay() {
        const toolsList = document.getElementById('tools-list');
        toolsList.innerHTML = '';
        this.availableTools.forEach(tool => {
            const toolBtn = document.createElement('button');
            toolBtn.className = 'tool-btn';
            toolBtn.textContent = tool;
            toolBtn.onclick = () => this.showToolHelp(tool);
            toolsList.appendChild(toolBtn);
        });
    }

    updateWorkflowsDisplay() {
        const workflowList = document.getElementById('workflow-list');
        workflowList.innerHTML = '';
        this.workflowTemplates.forEach(workflow => {
            const workflowBtn = document.createElement('button');
            workflowBtn.className = 'workflow-btn';
            workflowBtn.textContent = workflow.replace(/_/g, ' ').toUpperCase();
            workflowBtn.onclick = () => this.applyWorkflow(workflow);
            workflowList.appendChild(workflowBtn);
        });
    }

    async applyWorkflow(workflowName) {
        const customPrompt = document.getElementById('custom-workflow-prompt').value.trim();
        try {
            const response = await apiCall('apply_workflow', { template_name: workflowName, custom_prompt: customPrompt });
            if (response.status === 'success') {
                const workflow = response.workflow;
                addMessage('system', `Applied workflow: ${workflowName}`);
                document.getElementById('message-input').value = workflow.prompt;
                if (workflow.auto_approve && workflow.auto_approve.length > 0) {
                    this.autoApproveMode = true;
                    document.getElementById('auto-approve-tools').checked = true;
                    addMessage('system', `Auto-approve enabled for: ${workflow.auto_approve.join(', ')}`);
                }
                document.getElementById('custom-workflow-prompt').value = '';
            } else {
                addMessage('error', `Failed to apply workflow: ${response.message}`);
            }
        } catch (error) {
            addMessage('error', `Error applying workflow: ${error.message}`);
        }
    }

    async showToolHelp(toolName) {
        try {
            const response = await apiCall('get_tool_help', { tool_name: toolName });
            if (response.status === 'success') {
                const formattedHelp = response.help.replace(/\n/g, '<br>');
                addMessage('system', `<b>Tool: ${toolName}</b><br><br><pre>${formattedHelp}</pre>`);
            } else {
                addMessage('error', `Failed to get help for ${toolName}: ${response.message}`);
            }
        } catch (error) {
            addMessage('error', `Error getting tool help: ${error.message}`);
        }
    }

    async toggleAutoApprove() {
        this.autoApproveMode = document.getElementById('auto-approve-tools').checked;
        try {
            await apiCall('set_auto_approve', { enabled: this.autoApproveMode });
            addMessage('system', `Auto-approve mode ${this.autoApproveMode ? 'enabled' : 'disabled'}`);
        } catch (error) {
            addMessage('error', `Error toggling auto-approve: ${error.message}`);
        }
    }

    async searchMemory() {
        const query = document.getElementById('memory-search').value.trim();
        if (!query) return;
        try {
            const response = await apiCall('search_memory', { query: query });
            const resultsDiv = document.getElementById('memory-results');
            if (response.status === 'success' && response.results.length > 0) {
                let html = '<strong>Found:</strong>';
                response.results.forEach(result => {
                    html += `<div style="margin: 4px 0; padding: 4px; background: #f8f9fa; border-radius: 3px;">
                                <strong>${result.key}</strong> (${result.scope})<br>
                                <span style="color: #666;">${result.content}</span>
                             </div>`;
                });
                resultsDiv.innerHTML = html;
            } else {
                resultsDiv.innerHTML = '<div style="color: #888; font-style: italic;">No results found</div>';
            }
        } catch (error) {
            document.getElementById('memory-results').innerHTML = `<div style="color: #e53935;">Error searching memory: ${error.message}</div>`;
        }
    }

    async showContextPanel() {
        const contextPanel = document.getElementById('context-panel');
        contextPanel.style.display = 'block';
        try {
            const response = await apiCall('get_project_analysis');
            if (response.status === 'success') {
                const { analysis } = response;
                let html = `<div><strong>Project:</strong> ${analysis.project_summary.project_path}</div>
                            <div><strong>Context Size:</strong> ${(analysis.project_summary.context_size / 1024).toFixed(1)}KB</div>
                            <div><strong>Memory Entries:</strong> ${analysis.memory_entries}</div>
                            <div><strong>Tools:</strong> ${analysis.available_tools.length}</div>`;
                if (analysis.suggestions && analysis.suggestions.immediate_actions.length > 0) {
                    html += `<div style="margin-top: 8px;"><strong>Suggestions:</strong></div>`;
                    analysis.suggestions.immediate_actions.forEach(action => {
                        html += `<div style="font-size: 11px; color: #666;">• ${action}</div>`;
                    });
                }
                document.getElementById('context-summary').innerHTML = html;
            }
        } catch (error) {
            document.getElementById('context-summary').innerHTML = `<div style="color: #e53935;">Error loading context: ${error.message}</div>`;
        }
    }

    hideContextPanel() {
        document.getElementById('context-panel').style.display = 'none';
    }

    insertCommand(command) {
        document.getElementById('message-input').value = command;
        document.getElementById('message-input').focus();
        document.getElementById('command-suggestions').style.display = 'none';
    }

    stopCurrentOperation() {
        addMessage('system', '🛑 Operation stopped by user');
        setLoading(false);
        showTypingIndicator(false);
    }

    showFullOutput() {
        const lastMessage = document.querySelector('.assistant-message:last-of-type .message-content');
        if (lastMessage) {
            const modal = this.createModal('Full Output', lastMessage.innerHTML);
            document.body.appendChild(modal);
        }
    }

    createModal(title, content) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'block';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 80%; max-height: 80%; overflow-y: auto;">
                <span class="close" onclick="this.parentElement.parentElement.remove()">&times;</span>
                <h3>${title}</h3>
                <div style="white-space: pre-wrap; font-family: monospace; background: #f8f9fa; padding: 15px; border-radius: 4px;">${content}</div>
            </div>`;
        return modal;
    }

    async setProjectPath() {
        const newPath = prompt('Enter project path:', this.currentProjectPath || '.');
        if (newPath && newPath !== this.currentProjectPath) {
            try {
                const response = await apiCall('set_project_path', { project_path: newPath });
                if (response.status === 'success') {
                    this.currentProjectPath = newPath;
                    addMessage('system', `Project path changed to: ${newPath}`);
                    await this.refreshAgentUI();
                } else {
                    addMessage('error', `Failed to set project path: ${response.message}`);
                }
            } catch (error) {
                addMessage('error', `Error setting project path: ${error.message}`);
            }
        }
    }

    displayToolResults(toolResults) {
        const chatContainer = document.getElementById('chat-container');
        const typingIndicator = document.getElementById('typing-indicator');
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'tool-results';
        let html = '<strong>🔧 Tool Execution Results:</strong><br><br>';
        toolResults.forEach(result => {
            const status = result.result.success ? '✅' : '❌';
            const output = result.result.success ? result.result.output : result.result.error;
            const escapedOutput = output.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            html += `<div style="margin-bottom: 10px; padding: 8px; background: white; border-radius: 4px;">
                        <strong>${status} ${result.tool}</strong><br>
                        <div style="color: #666; margin: 4px 0;">Parameters: ${JSON.stringify(result.parameters)}</div>
                        <pre style="margin-top: 4px; white-space: pre-wrap; font-family: inherit;">${escapedOutput}</pre>
                     </div>`;
        });
        resultsContainer.innerHTML = html;
        chatContainer.insertBefore(resultsContainer, typingIndicator);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}


// ========================================================================
// Global Functions & App Initialization
// ========================================================================

// -- Single, unified API helper function --
async function apiCall(endpoint, data = null) {
    const options = {
        method: data ? 'POST' : 'GET',
        headers: { 'Content-Type': 'application/json' },
    };
    if (data) {
        options.body = JSON.stringify(data);
    }
    const response = await fetch(`/api/${endpoint}`, options);
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API request failed: ${response.status} ${response.statusText} - ${errorText}`);
    }
    return await response.json();
}

// -- Global Variables (to be initialized) --
let ui, chatContainer, messageInput, sendButton, sessionStatus, fileStatus, typingIndicator,
    inputTokens, outputTokens, totalTokens;
let isLoading = false;
let messageHistory = [];

// -- Core App Functions --
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isLoading) return;

    addMessage('user', message);
    messageInput.value = '';
    messageInput.style.height = 'auto';

    setLoading(true);
    showTypingIndicator(true);

    try {
        const response = await apiCall('send_message_enhanced', {
            message: message,
            use_tools: true
        });

        if (response.status === 'success') {
            addMessage('assistant', response.response);
            if (response.tool_results && response.tool_results.length > 0) {
                ui.displayToolResults(response.tool_results);
            }
            updateTokenInfo(response.tokens);
        } else {
            addMessage('error', response.message);
        }
    } catch (error) {
        addMessage('error', `Error sending message: ${error.message}`);
    } finally {
        setLoading(false);
        showTypingIndicator(false);
    }
}

function addMessage(role, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (text && typeof text === 'string') {
        const rawHtml = marked.parse(text, { gfm: true, breaks: true });
        contentDiv.innerHTML = DOMPurify.sanitize(rawHtml);
    } else {
        contentDiv.textContent = 'Received a non-text response.';
    }

    messageDiv.appendChild(contentDiv);
    if (role !== 'system') {
        messageHistory.push({ role, text });
    }
    chatContainer.insertBefore(messageDiv, typingIndicator);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function setLoading(loading) {
    isLoading = loading;
    if (sendButton) sendButton.disabled = loading;
    if (messageInput) messageInput.disabled = loading;
    if (sendButton) sendButton.textContent = loading ? 'Thinking...' : 'Send';
    document.body.classList.toggle('loading', loading);
}

async function updateSessionInfo() {
    try {
        const response = await apiCall('get_enhanced_session_info', {});
        if (response.status === 'success') {
            const info = response.info;
            if (sessionStatus) {
                sessionStatus.textContent = `Model: ${info.model_name} | Turns: ${info.conversation_turns}`;
            }
            updateTokenInfo(info);
            updateFileStatus(info.files_count);
        }
    } catch (error) {
        console.error('Error updating session info:', error);
        if (sessionStatus) {
            sessionStatus.textContent = "Error updating info";
        }
    }
}

function updateFileStatus(count = null) {
    if (count !== null) {
        if (fileStatus) {
            fileStatus.textContent = count > 0 ? `${count} file(s) loaded` : 'No files loaded';
        }
    } else {
        // If count isn't provided, refresh everything
        updateSessionInfo();
    }
}

function updateTokenInfo(info) {
    if (!info) return;
    const totalInput = info.total_input_tokens || 0;
    const totalOutput = info.total_output_tokens || 0;

    if (inputTokens) inputTokens.textContent = totalInput;
    if (outputTokens) outputTokens.textContent = totalOutput;
    if (totalTokens) totalTokens.textContent = totalInput + totalOutput;
}



function showTypingIndicator(show) {
    if (typingIndicator) typingIndicator.classList.toggle('show', show);
}

function updateTokenInfo(tokens) {
    if (!tokens) return;
    inputTokens.textContent = tokens.input;
    outputTokens.textContent = tokens.output;
    totalTokens.textContent = (tokens.input || 0) + (tokens.output || 0);
}

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    document.getElementById('theme-toggle').textContent = isDark ? '☀️ Light Mode' : '🌙 Dark Mode';
    localStorage.setItem('darkMode', isDark ? 'true' : 'false');
}

function exportChat() {
    const chatContent = messageHistory.map(msg => `${msg.role.toUpperCase()}: ${msg.text}`).join('\n\n');
    const blob = new Blob([chatContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gemini_chat_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}

// -- File & Upload Functions --
async function listFiles() {
    try {
        const response = await apiCall('list_uploaded_files');
        if (response.status === 'success') {
            const { files = [], expired_files = [] } = response;
            let fileList = `<div class="file-list-container">`;
            if (files.length > 0) {
                fileList += `<strong>📁 Uploaded Files (${files.length}):</strong><ul>`;
                files.forEach(file => {
                    fileList += `<li>${file.display_name || file.name} <button class="delete-btn" onclick="deleteFile('${file.name}')">🗑️</button></li>`;
                });
                fileList += '</ul>';
            }
            if (expired_files.length > 0) {
                fileList += `<br><strong>⚠️ Expired Files (${expired_files.length}):</strong><ul>`;
                expired_files.forEach(fileName => {
                    fileList += `<li>${fileName} (re-upload needed)</li>`;
                });
                fileList += '</ul>';
            }
            if (files.length === 0 && expired_files.length === 0) {
                fileList += '📂 No files in this session.';
            }
            fileList += '</div>';
            addMessage('system', fileList);
        } else {
            addMessage('error', `⚠️ ${response.message}`);
        }
    } catch (error) {
        addMessage('error', `❌ Error listing files: ${error.message}`);
    }
}

async function deleteFile(fileName) {
    if (!fileName || !confirm(`Are you sure you want to delete "${fileName}"?`)) return;
    try {
        const result = await apiCall('delete_file', { file_name: fileName });
        addMessage(result.status === 'success' ? 'system' : 'error', result.message);
        listFiles();
    } catch (err) {
        addMessage('error', `❌ Error deleting file: ${err.message}`);
    }
}

async function clearFiles() {
    if (!confirm('Are you sure you want to delete all files?')) return;
    try {
        const response = await apiCall('clear_files', {});
        addMessage(response.status === 'success' ? 'system' : 'error', response.message);
        updateFileStatus();
    } catch (error) {
        addMessage('error', 'Error clearing files: ' + error.message);
    }
}

async function clearChat() {
    if (!confirm('Are you sure you want to clear the chat history?')) return;
    try {
        const response = await apiCall('clear_conversation', {});
        if (response.status === 'success') {
            chatContainer.querySelectorAll('.message, .tool-results').forEach(el => el.remove());
            messageHistory = [];
            addMessage('system', 'Chat history cleared.');
        } else {
            addMessage('error', response.message);
        }
    } catch (error) {
        addMessage('error', 'Error clearing chat: ' + error.message);
    }
}

function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = e => resolve(e.target.result);
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(file);
    });
}

async function uploadFromFilePaths() {
    const pathsInput = document.getElementById('file-paths-input').value.trim();
    if (!pathsInput) return;
    const filePaths = pathsInput.split(/[\n,]/).map(p => p.trim()).filter(Boolean);
    if (filePaths.length === 0) return;

    try {
        addMessage('system', `📝 Uploading ${filePaths.length} file(s) from paths...`);
        const response = await apiCall('upload_files', { file_paths: filePaths });
        if (response.status === 'success') {
            addMessage('system', `✅ Successfully uploaded ${response.count} file(s).`);
            document.querySelector('.modal').remove();
            updateFileStatus();
            listFiles();
        } else {
            addMessage('error', `❌ Upload failed: ${response.message}`);
        }
    } catch (error) {
        addMessage('error', `Error uploading from paths: ${error.message}`);
    }
}

async function uploadQuickFiles() {
    const filePicker = document.getElementById('quick-file-picker');
    if (filePicker.files.length === 0) return;

    try {
        addMessage('system', `Quick uploading ${filePicker.files.length} file(s)...`);
        const filesToUpload = [];
        for (const file of filePicker.files) {
            const fileContent = await readFileAsText(file);
            filesToUpload.push({
                name: file.name,
                content: fileContent
            });
        }

        const response = await apiCall('upload_files_enhanced', { files: filesToUpload });

        if (response.status === 'success') {
            addMessage('system', `Quick uploaded ${response.count} file(s) successfully.`);
            closeQuickUploadModal();
            updateFileStatus();
            listFiles();
        } else {
            addMessage('error', `Upload failed: ${response.message}`);
        }
    } catch (error) {
        addMessage('error', `Error during quick upload: ${error.message}`);
    }
}

// -- Session Management Functions --
async function loadSessionsList() {
    try {
        const response = await apiCall('list_sessions');
        const listDiv = document.getElementById('sessions-list');
        if (response.status === 'success' && response.sessions.length > 0) {
            listDiv.innerHTML = response.sessions.map(session => `
                <div class="session-item">
                    <span>${session}</span>
                    <div>
                        <button onclick="loadSessionEnhanced('${session}')">📂 Load</button>
                        <button onclick="deleteSession('${session}')" class="delete-btn">🗑️ Delete</button>
                    </div>
                </div>`).join('');
        } else {
            listDiv.innerHTML = '<p>No saved sessions found</p>';
        }
    } catch (error) {
        document.getElementById('sessions-list').innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
    }
}

async function saveCurrentSessionEnhanced() {
    const sessionName = document.getElementById('session-name').value.trim();
    if (!sessionName) return alert('Please enter a session name.');
    try {
        const response = await apiCall('save_enhanced_session', { session_name: sessionName });
        if (response.status === 'success') {
            addMessage('system', `💾 Enhanced session saved: ${sessionName}`);
            closeSessionModal();
            loadSessionsList();
        } else {
            addMessage('error', response.message);
        }
    } catch (error) {
        addMessage('error', `Error saving session: ${error.message}`);
    }
}

async function loadSessionEnhanced(sessionName) {
    try {
        const response = await apiCall('load_enhanced_session', { session_file: sessionName });
        if (response.status === 'success') {
            addMessage('system', `📂 Enhanced session loaded: ${sessionName}`);
            closeSessionModal();
            await updateSessionInfo();
            await listFiles();
            await ui.refreshAgentUI();
        } else {
            addMessage('error', response.message);
        }
    } catch (error) {
        addMessage('error', `Error loading session: ${error.message}`);
    }
}

async function deleteSession(sessionName) {
    if (!confirm(`Are you sure you want to delete session "${sessionName}"?`)) return;
    try {
        const response = await apiCall('delete_session', { session_name: sessionName });
        addMessage(response.status === 'success' ? 'system' : 'error', response.message);
        loadSessionsList();
    } catch (error) {
        addMessage('error', `Error deleting session: ${error.message}`);
    }
}

// -- Modal & UI Helper Functions --
function showSessionModal() {
    document.getElementById('sessionModal').style.display = 'block';
    loadSessionsList();
}
function closeSessionModal() { document.getElementById('sessionModal').style.display = 'none'; }

function showQuickUploadModal() {
    const modal = document.getElementById('quickUploadModal');
    modal.style.display = 'block';
    modal.querySelector('#quick-file-picker').value = '';
    modal.querySelector('#quick-selected-files').innerHTML = '<p>No files selected</p>';
    modal.querySelector('#quick-upload-button').disabled = true;
}
function closeQuickUploadModal() { document.getElementById('quickUploadModal').style.display = 'none'; }

function showFileUploadModal() {
    const modal = document.getElementById('fileModal');
    modal.style.display = 'block';
    modal.querySelector('#file-picker').value = '';
    modal.querySelector('#selected-files').innerHTML = '<p>No files selected</p>';
    modal.querySelector('#upload-button').disabled = true;
}
function closeFileModal() { document.getElementById('fileModal').style.display = 'none'; }

function showReuploadModal() {
    document.getElementById('reuploadModal').style.display = 'block';
    loadSessionFiles();
}
function closeReuploadModal() { document.getElementById('reuploadModal').style.display = 'none'; }

function showSettingsModal() { document.getElementById('settingsModal').style.display = 'block'; }
function closeSettingsModal() { document.getElementById('settingsModal').style.display = 'none'; }

async function applySettings() {
    const settings = {
        model_name: document.getElementById('model-select').value,
        use_dynamic_tokens: document.getElementById('use-dynamic-tokens').checked,
        max_total_tokens: parseInt(document.getElementById('max-total-tokens').value),
        hard_cap: parseInt(document.getElementById('hard-cap').value),
        truncate_output: document.getElementById('truncate-output').checked,
        truncate_chars: parseInt(document.getElementById('truncate-chars').value),
        add_short_hint: document.getElementById('add-short-hint').checked,
        enable_streaming: document.getElementById('enable-streaming').checked
    };
    try {
        const response = await apiCall('update_settings', settings);
        addMessage('system', 'Settings updated successfully.');
        closeSettingsModal();
        await updateSessionInfo();
    } catch (e) {
        addMessage('error', 'Failed to update settings: ' + e.message);
    }
}

async function loadSessionFiles() {
    try {
        const response = await apiCall('get_session_files');
        const listDiv = document.getElementById('session-files-list');
        if (response.status === 'success' && response.file_paths.length > 0) {
            listDiv.innerHTML = response.file_paths.map((file, index) => `
                <div class="session-file-item">
                    <input type="checkbox" id="file-${index}" value="${file.path}" ${!file.exists ? 'disabled' : ''}>
                    <label for="file-${index}" class="${!file.exists ? 'file-missing' : ''}">
                        <strong>${file.display_name}</strong> (${file.exists ? '✅ Available' : '❌ Missing'})
                        <span>${file.path}</span>
                    </label>
                </div>`).join('');
        } else {
            listDiv.innerHTML = '<p>No re-uploadable files in session.</p>';
        }
    } catch (error) {
        document.getElementById('session-files-list').innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
    }
}

async function reuploadSelectedFiles() {
    const selectedPaths = Array.from(document.querySelectorAll('#session-files-list input:checked')).map(cb => cb.value);
    if (selectedPaths.length === 0) return;
    try {
        const response = await apiCall('reupload_session_files', { selected_paths: selectedPaths });
        addMessage('system', `Re-uploaded ${response.count} file(s).`);
        closeReuploadModal();
        await updateFileStatus();
    } catch (error) {
        addMessage('error', 'Error re-uploading files: ' + error.message);
    }
}

// -- App Entry Point --
document.addEventListener('DOMContentLoaded', function () {
    // Initialize global variables
    chatContainer = document.getElementById('chat-container');
    messageInput = document.getElementById('message-input');
    sendButton = document.getElementById('send-button');
    sessionStatus = document.getElementById('session-status');
    fileStatus = document.getElementById('file-status');
    typingIndicator = document.getElementById('typing-indicator');
    inputTokens = document.getElementById('input-tokens');
    outputTokens = document.getElementById('output-tokens');
    totalTokens = document.getElementById('total-tokens');

    // Instantiate the main UI class
    ui = new EnhancedGeminiWebUI();

    // Attach primary event listeners
    sendButton.onclick = sendMessage;
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
        document.getElementById('theme-toggle').textContent = '☀️ Light Mode';
    }

    // Initial session setup
    initializeSession();
});

async function initializeSession() {
    try {
        sessionStatus.textContent = 'Initializing...';
        const response = await apiCall('initialize_enhanced_session', {});
        if (response.status === 'success') {
            sessionStatus.textContent = 'Session ready';
            addMessage('assistant', 'Hello! I\'m your Gemini Assistant. How can I help you today?');
            updateSessionInfo();
            await ui.refreshAgentUI();
        } else {
            sessionStatus.textContent = 'Session failed';
            addMessage('error', `Failed to initialize session: ${response.message}`);
        }
    } catch (error) {
        sessionStatus.textContent = 'Session error';
        addMessage('error', `Error initializing session: ${error.message}`);
    }
}