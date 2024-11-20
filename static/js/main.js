document.addEventListener('DOMContentLoaded', function() {
     const chatMessages = document.getElementById('chat-messages');
     const userInput = document.getElementById('user-input');
     const sendBtn = document.getElementById('send-btn');
     const modelSelector = document.getElementById('model-selector');
     let conversationHistory = [];
 
     // Load conversation history
     async function loadHistory() {
         try {
             const response = await fetch('/history');
             const history = await response.json();
             conversationHistory = history;
             
             chatMessages.innerHTML = '';
             
             history.forEach(conv => {
                 addMessage(conv.user_message, true, conv.timestamp);
                 addMessage(conv.bot_response, false, conv.timestamp);
             });
 
             scrollToBottom();
         } catch (error) {
             console.error('Error loading history:', error);
         }
     }
 
     function scrollToBottom() {
         chatMessages.scrollTop = chatMessages.scrollHeight;
     }
 
     function formatTimestamp(timestamp) {
         const date = new Date(timestamp);
         return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
     }
 
     function addMessage(content, isUser = false, timestamp = new Date().toISOString()) {
         const messageDiv = document.createElement('div');
         messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
         messageDiv.innerHTML = `
             <div class="message-content">
                 ${content}
                 <div class="message-timestamp">${formatTimestamp(timestamp)}</div>
             </div>
         `;
         chatMessages.appendChild(messageDiv);
         scrollToBottom();
     }
 
     async function sendMessage() {
         const message = userInput.value.trim();
         if (!message) return;
 
         addMessage(message, true);
         userInput.value = '';
 
         const loadingDiv = document.createElement('div');
         loadingDiv.className = 'message bot';
         loadingDiv.innerHTML = '<div class="message-content">Typing...<div class="typing-indicator"></div></div>';
         chatMessages.appendChild(loadingDiv);
         scrollToBottom();
 
         try {
             const response = await fetch('/chat', {
                 method: 'POST',
                 headers: {
                     'Content-Type': 'application/json'
                 },
                 body: JSON.stringify({
                     message: message,
                     model: modelSelector.value,
                     history: conversationHistory
                 })
             });
 
             const data = await response.json();
             
             chatMessages.removeChild(loadingDiv);
 
             if (data.error) {
                 addMessage('Sorry, there was an error. Please try again later.');
             } else {
                 addMessage(data.response);
                 conversationHistory.push({
                     timestamp: new Date().toISOString(),
                     user_message: message,
                     bot_response: data.response,
                     model: data.model
                 });
             }
 
         } catch (error) {
             chatMessages.removeChild(loadingDiv);
             addMessage('Sorry, there was an error. Please try again later.');
         }
     }
 
     // Event listeners
     sendBtn.addEventListener('click', sendMessage);
     userInput.addEventListener('keypress', function(e) {
         if (e.key === 'Enter') {
             sendMessage();
         }
     });
 
     modelSelector.addEventListener('change', function() {
         addMessage(`Model changed to ${this.value}`, false);
     });
 
     // Theme Toggle Functionality
     const settingsBtn = document.getElementById('settings-btn');
     const settingsPanel = document.getElementById('settings-panel');
     const closeSettings = document.querySelector('.close-settings');
     const themeToggle = document.getElementById('theme-toggle');
 
     // Load saved theme
     const savedTheme = localStorage.getItem('theme') || 'light';
     document.documentElement.setAttribute('data-theme', savedTheme);
     themeToggle.checked = savedTheme === 'dark';
 
     // Toggle settings panel
     settingsBtn.addEventListener('click', () => {
         settingsPanel.classList.add('active');
     });
 
     closeSettings.addEventListener('click', () => {
         settingsPanel.classList.remove('active');
     });
 
     // Theme toggle
     themeToggle.addEventListener('change', (e) => {
         const theme = e.target.checked ? 'dark' : 'light';
         document.documentElement.setAttribute('data-theme', theme);
         localStorage.setItem('theme', theme);
     });
 
     // Close settings panel when clicking outside
     document.addEventListener('click', (e) => {
         if (!settingsPanel.contains(e.target) && !settingsBtn.contains(e.target)) {
             settingsPanel.classList.remove('active');
         }
     });
 
     // Load history when page loads
     loadHistory();
 });