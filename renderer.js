let inputFolder = null;
let outputFolder = null;
let videoFiles = [];
let isProcessing = false;
let selectedModel = 'medium';

// Settings modal elements
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeModal = document.querySelector('.close');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');
const cancelSettingsBtn = document.getElementById('cancelSettingsBtn');

const themeSelect = document.getElementById('themeSelect');
const modelSelect = document.getElementById('modelSelect');
const transcriptFormat = document.getElementById('transcriptFormat');
const modelSize = document.getElementById('modelSize');
const modelRam = document.getElementById('modelRam');
const modelSpeed = document.getElementById('modelSpeed');
const modelAccuracy = document.getElementById('modelAccuracy');
const modelDescription = document.getElementById('modelDescription');
const modelStatus = document.getElementById('modelStatus');
const enableLLM = document.getElementById('enableLLM');
const llmOptions = document.getElementById('llmOptions');
const llmProvider = document.getElementById('llmProvider');
const llmTemplate = document.getElementById('llmTemplate');
const llmApiKey = document.getElementById('llmApiKey');
const llmModel = document.getElementById('llmModel');
const selectInputBtn = document.getElementById('selectInputBtn');
const selectOutputBtn = document.getElementById('selectOutputBtn');
const processBtn = document.getElementById('processBtn');
const stopBtn = document.getElementById('stopBtn');
const inputFolderPath = document.getElementById('inputFolderPath');
const outputFolderPath = document.getElementById('outputFolderPath');
const videoList = document.getElementById('videoList');
const progressSection = document.getElementById('progressSection');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const filesProcessed = document.getElementById('filesProcessed');
const totalFiles = document.getElementById('totalFiles');
const logOutput = document.getElementById('logOutput');
const terminalOutput = document.getElementById('terminalOutput');
const clearTerminalBtn = document.getElementById('clearTerminalBtn');
const verifyModelBtn = document.getElementById('verifyModelBtn');
const downloadModelBtn = document.getElementById('downloadModelBtn');
const modelVerificationStatus = document.getElementById('modelVerificationStatus');
const modelLocationInfo = document.getElementById('modelLocationInfo');
const modelLocationPath = document.getElementById('modelLocationPath');

let currentProcessId = null;

const modelInfo = {
    tiny: {
        size: '39 MB',
        ram: '~1 GB',
        speed: 'Very Fast',
        accuracy: 'Basic',
        description: 'Fastest model, suitable for quick drafts. Limited accuracy for Japanese.'
    },
    base: {
        size: '74 MB',
        ram: '~1 GB',
        speed: 'Fast',
        accuracy: 'Good',
        description: 'Good balance for simple audio. Decent for English, limited Japanese support.'
    },
    small: {
        size: '244 MB',
        ram: '~2 GB',
        speed: 'Medium',
        accuracy: 'Better',
        description: 'Good for most use cases. Handles Japanese reasonably well.'
    },
    medium: {
        size: '769 MB',
        ram: '~5 GB',
        speed: 'Slow',
        accuracy: 'Excellent',
        description: 'Recommended for Japanese/English mixed audio. Best balance of accuracy and speed.'
    },
    large: {
        size: '2.9 GB',
        ram: '~10 GB',
        speed: 'Very Slow',
        accuracy: 'Best',
        description: 'Highest accuracy for all languages (large-v3). Best for professional transcription.'
    }
};

function updateModelInfo(model) {
    const info = modelInfo[model];
    modelSize.textContent = info.size;
    modelRam.textContent = info.ram;
    modelSpeed.textContent = info.speed;
    modelAccuracy.textContent = info.accuracy;
    modelDescription.textContent = info.description;
    selectedModel = model;
}

function applyTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('selectedTheme', theme);
}

function loadSavedTheme() {
    const savedTheme = localStorage.getItem('selectedTheme') || 'violet';
    themeSelect.value = savedTheme;
    applyTheme(savedTheme);
}

themeSelect.addEventListener('change', (e) => {
    applyTheme(e.target.value);
});

modelSelect.addEventListener('change', (e) => {
    updateModelInfo(e.target.value);
});

loadSavedTheme();

enableLLM.addEventListener('change', (e) => {
    llmOptions.style.display = e.target.checked ? 'flex' : 'none';
});

selectInputBtn.addEventListener('click', async () => {
    const result = await window.electronAPI.selectInputFolder();
    
    if (result) {
        inputFolder = result.folderPath;
        videoFiles = result.videoFiles;
        
        inputFolderPath.textContent = inputFolder;
        inputFolderPath.classList.add('selected');
        
        displayVideoList();
        updateProcessButton();
    }
});

selectOutputBtn.addEventListener('click', async () => {
    const result = await window.electronAPI.selectOutputFolder();
    
    if (result) {
        outputFolder = result;
        outputFolderPath.textContent = outputFolder;
        outputFolderPath.classList.add('selected');
        
        updateProcessButton();
    }
});

processBtn.addEventListener('click', async () => {
    if (isProcessing || !inputFolder || !outputFolder || videoFiles.length === 0) {
        return;
    }
    
    isProcessing = true;
    processBtn.disabled = true;
    processBtn.style.display = 'none';
    stopBtn.style.display = 'inline-block';
    selectInputBtn.disabled = true;
    selectOutputBtn.disabled = true;
    modelSelect.disabled = true;
    
    modelStatus.textContent = 'Processing...';
    modelStatus.className = 'info-value status-loading';
    
    progressSection.style.display = 'block';
    logOutput.innerHTML = '';
    progressBar.style.width = '0%';
    progressText.textContent = 'Starting processing...';
    totalFiles.textContent = videoFiles.length;
    filesProcessed.textContent = '0';
    
    try {
        const llmConfig = enableLLM.checked ? {
            enabled: true,
            provider: llmProvider.value,
            template: llmTemplate.value,
            apiKey: llmApiKey.value,
            model: llmModel.value
        } : {
            enabled: false
        };
        
        const result = await window.electronAPI.processVideos({
            videoFiles,
            outputFolder,
            model: selectedModel,
            llm: llmConfig,
            format: transcriptFormat.value
        });
        
        if (result.stopped) {
            progressText.textContent = 'Processing stopped by user';
            addLog('⚠ Processing stopped. Converted files have been saved.', 'warning');
        } else {
            progressBar.style.width = '100%';
            progressText.textContent = 'Processing complete!';
            addLog('All videos processed successfully!', 'success');
            
            // Show search section after processing
            searchSection.style.display = 'block';
        }
        
        modelStatus.textContent = 'Ready';
        modelStatus.className = 'info-value status-ready';
        searchSection.scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        addLog(`Error: ${error.message || 'Processing failed'}`, 'error');
        progressText.textContent = 'Processing failed';
        modelStatus.textContent = 'Error';
        modelStatus.className = 'info-value status-error';
    } finally {
        isProcessing = false;
        processBtn.disabled = false;
        processBtn.style.display = 'inline-block';
        stopBtn.style.display = 'none';
        selectInputBtn.disabled = false;
        selectOutputBtn.disabled = false;
        modelSelect.disabled = false;
        currentProcessId = null;
    }
});

stopBtn.addEventListener('click', async () => {
    if (currentProcessId) {
        await window.electronAPI.stopProcessing(currentProcessId);
        addLog('⏹ Stop signal sent. Finishing current file...', 'warning');
        stopBtn.disabled = true;
        stopBtn.textContent = 'Stopping...';
    }
});

function displayVideoList() {
    if (videoFiles.length === 0) {
        videoList.innerHTML = '<div style="padding: 10px; color: #999;">No video files found in this folder</div>';
        return;
    }
    
    videoList.innerHTML = '';
    videoFiles.forEach(filePath => {
        const fileName = filePath.split('/').pop();
        const div = document.createElement('div');
        div.className = 'video-item';
        div.textContent = fileName;
        videoList.appendChild(div);
    });
    
    const summary = document.createElement('div');
    summary.style.marginTop = '10px';
    summary.style.fontWeight = '600';
    summary.style.color = '#667eea';
    summary.textContent = `Found ${videoFiles.length} video file${videoFiles.length !== 1 ? 's' : ''}`;
    videoList.appendChild(summary);
}

function updateProcessButton() {
    processBtn.disabled = !inputFolder || !outputFolder || videoFiles.length === 0 || isProcessing;
}

function addLog(message, type = 'info') {
    if (!logOutput) return;
    const logLine = document.createElement('div');
    logLine.className = `log-line ${type}`;
    const timestamp = new Date().toLocaleTimeString();
    logLine.textContent = `[${timestamp}] ${message}`;
    logOutput.appendChild(logLine);
    logOutput.scrollTop = logOutput.scrollHeight;
}

function addTerminalLine(message, type = 'info') {
    console.log('[Terminal]', message);  // Debug logging
    if (!terminalOutput) {
        console.error('terminalOutput element not found!');
        return;
    }
    const line = document.createElement('div');
    line.className = `terminal-line ${type}`;
    line.textContent = message;
    terminalOutput.appendChild(line);
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

clearTerminalBtn.addEventListener('click', () => {
    terminalOutput.innerHTML = '';
});

verifyModelBtn.addEventListener('click', async () => {
    const model = modelSelect.value;
    
    modelVerificationStatus.style.display = 'flex';
    modelVerificationStatus.className = 'model-verification checking';
    modelVerificationStatus.querySelector('.verification-icon').textContent = '⏳';
    modelVerificationStatus.querySelector('.verification-text').textContent = `Checking ${model} model...`;
    modelLocationInfo.style.display = 'none';
    
    try {
        const result = await window.electronAPI.verifyModel(model);
        
        if (result.exists) {
            modelVerificationStatus.className = 'model-verification verified';
            modelVerificationStatus.querySelector('.verification-icon').textContent = '✅';
            modelVerificationStatus.querySelector('.verification-text').textContent = 
                `Model '${model}' is downloaded (${result.size})`;
            
            // Show location
            modelLocationInfo.style.display = 'block';
            modelLocationPath.textContent = result.path;
        } else {
            modelVerificationStatus.className = 'model-verification not-verified';
            modelVerificationStatus.querySelector('.verification-icon').textContent = '⚠️';
            modelVerificationStatus.querySelector('.verification-text').textContent = 
                `Model '${model}' not found. Click "Download Model" to download it now.`;
            
            // Show cache directory
            modelLocationInfo.style.display = 'block';
            modelLocationPath.textContent = `Will be downloaded to: ${result.cache_dir}`;
        }
    } catch (error) {
        modelVerificationStatus.className = 'model-verification not-verified';
        modelVerificationStatus.querySelector('.verification-icon').textContent = '❌';
        modelVerificationStatus.querySelector('.verification-text').textContent = 
            `Error checking model: ${error.message}`;
        modelLocationInfo.style.display = 'none';
    }
});

downloadModelBtn.addEventListener('click', async () => {
    const model = modelSelect.value;
    
    downloadModelBtn.disabled = true;
    downloadModelBtn.textContent = '⏳ Downloading...';
    verifyModelBtn.disabled = true;
    
    modelVerificationStatus.style.display = 'flex';
    modelVerificationStatus.className = 'model-verification checking';
    modelVerificationStatus.querySelector('.verification-icon').textContent = '⏳';
    modelVerificationStatus.querySelector('.verification-text').textContent = `Downloading ${model} model... Check terminal for progress`;
    
    // Clear terminal and show progress section
    terminalOutput.innerHTML = '';
    progressSection.style.display = 'block';
    addTerminalLine(`Starting download of Whisper model: ${model}`, 'info');
    
    try {
        const result = await window.electronAPI.downloadModel(model);
        
        if (result.success) {
            modelVerificationStatus.className = 'model-verification verified';
            modelVerificationStatus.querySelector('.verification-icon').textContent = '✅';
            modelVerificationStatus.querySelector('.verification-text').textContent = 
                `Model '${model}' downloaded successfully! (${result.size})`;
            
            modelLocationInfo.style.display = 'block';
            modelLocationPath.textContent = result.path;
            
            addTerminalLine(`✓ Download complete: ${result.path}`, 'success');
            addLog(`Model '${model}' downloaded successfully!`, 'success');
        } else {
            modelVerificationStatus.className = 'model-verification not-verified';
            modelVerificationStatus.querySelector('.verification-icon').textContent = '❌';
            modelVerificationStatus.querySelector('.verification-text').textContent = 
                `Download failed: ${result.message}`;
            
            addTerminalLine(`✗ Download failed: ${result.message}`, 'error');
            addLog(`Failed to download model: ${result.message}`, 'error');
        }
    } catch (error) {
        modelVerificationStatus.className = 'model-verification not-verified';
        modelVerificationStatus.querySelector('.verification-icon').textContent = '❌';
        modelVerificationStatus.querySelector('.verification-text').textContent = 
            `Download error: ${error.message}`;
        
        addTerminalLine(`✗ Error: ${error.message}`, 'error');
        addLog(`Download error: ${error.message}`, 'error');
    } finally {
        downloadModelBtn.disabled = false;
        downloadModelBtn.textContent = '⬇️ Download Model';
        verifyModelBtn.disabled = false;
    }
});

window.electronAPI.onProcessingUpdate((message) => {
    console.log('[IPC Update]', message);  // Debug logging
    // Add all messages to terminal
    addTerminalLine(message.trim(), 'info');
    
    // Check for PROGRESS: prefix for file count updates
    if (message.startsWith('PROGRESS:')) {
        const progressMatch = message.match(/PROGRESS: (\d+)\/(\d+)/);
        if (progressMatch) {
            const current = parseInt(progressMatch[1]);
            const total = parseInt(progressMatch[2]);
            const percentage = (current / total) * 100;
            progressBar.style.width = `${percentage}%`;
            progressText.textContent = `Processing file ${current} of ${total}...`;
            filesProcessed.textContent = current;
            totalFiles.textContent = total;
        }
    } else {
        addLog(message.trim(), 'info');
    }
});

window.electronAPI.onProcessingError((error) => {
    addLog(error.trim(), 'error');
    addTerminalLine(error.trim(), 'error');
});

// Search functionality
const searchSection = document.getElementById('searchSection');
const searchTabs = document.querySelectorAll('.search-tab');
const searchTabContents = document.querySelectorAll('.search-tab-content');
const keywordInput = document.getElementById('keywordInput');
const keywordSearchBtn = document.getElementById('keywordSearchBtn');
const caseSensitive = document.getElementById('caseSensitive');
const keywordResults = document.getElementById('keywordResults');
const semanticInput = document.getElementById('semanticInput');
const semanticSearchBtn = document.getElementById('semanticSearchBtn');
const semanticResults = document.getElementById('semanticResults');
const chatInput = document.getElementById('chatInput');
const chatSendBtn = document.getElementById('chatSendBtn');
const chatMessages = document.getElementById('chatMessages');

// Show search section after processing completes
window.addEventListener('DOMContentLoaded', () => {
    if (outputFolder) {
        searchSection.style.display = 'block';
    }
});

// Tab switching
searchTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const targetTab = tab.dataset.tab;
        
        searchTabs.forEach(t => t.classList.remove('active'));
        searchTabContents.forEach(c => c.classList.remove('active'));
        
        tab.classList.add('active');
        document.getElementById(`${targetTab}Tab`).classList.add('active');
    });
});

// Keyword search
keywordSearchBtn.addEventListener('click', async () => {
    const query = keywordInput.value.trim();
    if (!query || !outputFolder) return;
    
    keywordResults.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const llmConfig = enableLLM.checked ? {
            enabled: true,
            provider: llmProvider.value,
            apiKey: llmApiKey.value,
            model: llmModel.value
        } : null;
        
        const result = await window.electronAPI.searchTranscripts({
            action: 'keyword',
            query: query,
            outputFolder: outputFolder,
            caseSensitive: caseSensitive.checked,
            llmConfig: llmConfig
        });
        
        displaySearchResults(result.results, keywordResults);
    } catch (error) {
        keywordResults.innerHTML = `<div class="no-results">Error: ${error.error || 'Search failed'}</div>`;
    }
});

keywordInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') keywordSearchBtn.click();
});

// Semantic search
semanticSearchBtn.addEventListener('click', async () => {
    const query = semanticInput.value.trim();
    if (!query || !outputFolder) return;
    
    semanticResults.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const llmConfig = enableLLM.checked ? {
            enabled: true,
            provider: llmProvider.value,
            apiKey: llmApiKey.value,
            model: llmModel.value
        } : null;
        
        const result = await window.electronAPI.searchTranscripts({
            action: 'semantic',
            query: query,
            outputFolder: outputFolder,
            llmConfig: llmConfig
        });
        
        displaySearchResults(result.results, semanticResults);
    } catch (error) {
        semanticResults.innerHTML = `<div class="no-results">Error: ${error.error || 'Search failed'}</div>`;
    }
});

semanticInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') semanticSearchBtn.click();
});

// Chat/Ask questions
chatSendBtn.addEventListener('click', async () => {
    const question = chatInput.value.trim();
    if (!question || !outputFolder) return;
    
    addChatMessage(question, 'user');
    chatInput.value = '';
    
    addChatMessage('Thinking...', 'assistant', true);
    
    try {
        const llmConfig = enableLLM.checked ? {
            enabled: true,
            provider: llmProvider.value,
            apiKey: llmApiKey.value,
            model: llmModel.value
        } : null;
        
        const result = await window.electronAPI.searchTranscripts({
            action: 'ask',
            query: question,
            outputFolder: outputFolder,
            llmConfig: llmConfig
        });
        
        // Remove "Thinking..." message
        const lastMessage = chatMessages.lastElementChild;
        if (lastMessage && lastMessage.classList.contains('assistant')) {
            chatMessages.removeChild(lastMessage);
        }
        
        addChatMessage(result.answer, 'assistant');
    } catch (error) {
        const lastMessage = chatMessages.lastElementChild;
        if (lastMessage && lastMessage.classList.contains('assistant')) {
            chatMessages.removeChild(lastMessage);
        }
        addChatMessage(`Error: ${error.error || 'Failed to get answer'}`, 'assistant');
    }
});

chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') chatSendBtn.click();
});

function displaySearchResults(results, container) {
    if (!results || results.length === 0) {
        container.innerHTML = '<div class="no-results">No results found</div>';
        return;
    }
    
    let html = '';
    results.forEach(result => {
        html += `
            <div class="search-result-item">
                <div class="result-header">
                    <div class="result-title">📄 ${result.file_name}</div>
                    <div class="result-meta">
                        <span class="result-badge">${result.language}</span>
                        <span>${result.match_count} match${result.match_count !== 1 ? 'es' : ''}</span>
                    </div>
                </div>
                <div class="result-matches">
                    ${result.matches.map(match => `
                        <div class="match-item">
                            ${match.timestamp ? `<div class="match-timestamp">⏱ ${match.timestamp}</div>` : ''}
                            ${match.speaker ? `<div class="match-speaker">👤 ${match.speaker}</div>` : ''}
                            <div class="match-text">${match.highlight || match.text}</div>
                            ${match.relevance_score ? `<div class="match-timestamp">Relevance: ${(match.relevance_score * 100).toFixed(1)}%</div>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function addChatMessage(text, role, isLoading = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'chat-message-content';
    contentDiv.textContent = text;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'chat-message-time';
    timeDiv.textContent = new Date().toLocaleTimeString();
    
    messageDiv.appendChild(contentDiv);
    if (!isLoading) {
        messageDiv.appendChild(timeDiv);
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

// Settings Modal Functionality
settingsBtn.addEventListener('click', async () => {
    settingsModal.style.display = 'block';
    
    // Load current settings
    const settings = await window.electronAPI.loadSettings();
    
    // Populate form fields
    document.getElementById('huggingfaceToken').value = settings.HUGGINGFACE_TOKEN || '';
    document.getElementById('openaiKey').value = settings.OPENAI_API_KEY || '';
    document.getElementById('geminiKey').value = settings.GOOGLE_API_KEY || '';
    document.getElementById('claudeKey').value = settings.ANTHROPIC_API_KEY || '';
    document.getElementById('defaultWhisperModel').value = settings.DEFAULT_WHISPER_MODEL || 'medium';
    document.getElementById('defaultFormat').value = settings.DEFAULT_TRANSCRIPT_FORMAT || 'txt';
    document.getElementById('defaultLLMProvider').value = settings.DEFAULT_LLM_PROVIDER || 'none';
    document.getElementById('defaultLLMTemplate').value = settings.DEFAULT_LLM_TEMPLATE || 'clean';
    document.getElementById('mp3Bitrate').value = settings.MP3_BITRATE || '128k';
});

closeModal.addEventListener('click', () => {
    settingsModal.style.display = 'none';
});

cancelSettingsBtn.addEventListener('click', () => {
    settingsModal.style.display = 'none';
});

window.addEventListener('click', (event) => {
    if (event.target === settingsModal) {
        settingsModal.style.display = 'none';
    }
});

saveSettingsBtn.addEventListener('click', async () => {
    const settings = {
        HUGGINGFACE_TOKEN: document.getElementById('huggingfaceToken').value,
        OPENAI_API_KEY: document.getElementById('openaiKey').value,
        GOOGLE_API_KEY: document.getElementById('geminiKey').value,
        ANTHROPIC_API_KEY: document.getElementById('claudeKey').value,
        DEFAULT_WHISPER_MODEL: document.getElementById('defaultWhisperModel').value,
        DEFAULT_TRANSCRIPT_FORMAT: document.getElementById('defaultFormat').value,
        DEFAULT_LLM_PROVIDER: document.getElementById('defaultLLMProvider').value,
        DEFAULT_LLM_TEMPLATE: document.getElementById('defaultLLMTemplate').value,
        MP3_BITRATE: document.getElementById('mp3Bitrate').value
    };
    
    const result = await window.electronAPI.saveSettings(settings);
    
    if (result.success) {
        settingsModal.style.display = 'none';
        
        // Apply default settings to current UI
        modelSelect.value = settings.DEFAULT_WHISPER_MODEL;
        transcriptFormat.value = settings.DEFAULT_TRANSCRIPT_FORMAT;
        
        // Update model info display
        updateModelInfo();
        
        // Show success message
        addLog('✓ Settings saved successfully!', 'success');
    } else {
        alert('Failed to save settings: ' + result.error);
    }
});
