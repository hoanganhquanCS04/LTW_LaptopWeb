// Chatbot script for e-commerce support

document.addEventListener('DOMContentLoaded', function() {
    // Create chatbot container
    const chatbotContainer = document.createElement('div');
    chatbotContainer.id = 'chatbot-container';
    document.body.appendChild(chatbotContainer);

    // Create chatbot icon
    const chatbotIcon = document.createElement('div');
    chatbotIcon.id = 'chatbot-icon';
    chatbotIcon.className = 'chatbot-icon';
    chatbotIcon.innerHTML = '<i class="fa fa-comments" aria-hidden="true"></i>';
    chatbotContainer.appendChild(chatbotIcon);

    // Create chat window
    const chatWindow = document.createElement('div');
    chatWindow.id = 'chat-window';
    chatWindow.className = 'chatbot-container';
    chatbotContainer.appendChild(chatWindow);

    // Create chat header
    const chatHeader = document.createElement('div');
    chatHeader.id = 'chat-header';
    chatHeader.className = 'chatbot-header';
    chatHeader.innerHTML = '<h3>Hỗ trợ trực tuyến</h3><button id="close-chat" class="chatbot-close">×</button>';
    chatWindow.appendChild(chatHeader);

    // Create chat messages container
    const chatMessages = document.createElement('div');
    chatMessages.id = 'chat-messages';
    chatMessages.className = 'chatbot-messages';
    chatWindow.appendChild(chatMessages);

    // Add welcome message
    const welcomeMessage = document.createElement('div');
    welcomeMessage.className = 'bot-message message';
    welcomeMessage.textContent = 'Xin chào! Tôi có thể giúp gì cho bạn về các sản phẩm của chúng tôi?';
    chatMessages.appendChild(welcomeMessage);

    // Create chat input area
    const chatInputArea = document.createElement('div');
    chatInputArea.id = 'chat-input-area';
    chatInputArea.className = 'chatbot-input';
    chatWindow.appendChild(chatInputArea);

    // Create chat input
    const chatInput = document.createElement('input');
    chatInput.id = 'chat-input';
    chatInput.type = 'text';
    chatInput.placeholder = 'Nhập câu hỏi của bạn...';
    chatInputArea.appendChild(chatInput);

    // Create send button
    const sendButton = document.createElement('button');
    sendButton.id = 'send-button';
    sendButton.innerHTML = '<i class="fa fa-paper-plane" aria-hidden="true"></i>';
    chatInputArea.appendChild(sendButton);

    // Toggle chat window when icon is clicked
    chatbotIcon.addEventListener('click', function() {
        chatWindow.classList.toggle('active');
    });

    // Close chat window when close button is clicked
    document.getElementById('close-chat').addEventListener('click', function() {
        chatWindow.classList.remove('active');
    });

    // Function to add user message to chat
    function addUserMessage(message) {
        const userMessage = document.createElement('div');
        userMessage.className = 'user-message message';
        userMessage.textContent = message;
        chatMessages.appendChild(userMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to add bot message to chat
    function addBotMessage(message) {
        const botMessage = document.createElement('div');
        botMessage.className = 'bot-message message';
        botMessage.textContent = message;
        chatMessages.appendChild(botMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to show typing indicator
    function showTypingIndicator() {
        const typingIndicator = document.createElement('div');
        typingIndicator.id = 'typing-indicator';
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return typingIndicator;
    }

    // Function to send message to ChatGPT API
    async function sendToChatGPT(message) {
        const typingIndicator = showTypingIndicator();
        
        try {
            const response = await fetch('/chatbot/ask/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            typingIndicator.remove();
            addBotMessage(data.response);
        } catch (error) {
            console.error('Error:', error);
            typingIndicator.remove();
            addBotMessage('Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau.');
        }
    }

    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Send message when send button is clicked
    sendButton.addEventListener('click', function() {
        const message = chatInput.value.trim();
        if (message) {
            addUserMessage(message);
            chatInput.value = '';
            sendToChatGPT(message);
        }
    });

    // Send message when Enter key is pressed
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const message = chatInput.value.trim();
            if (message) {
                addUserMessage(message);
                chatInput.value = '';
                sendToChatGPT(message);
            }
        }
    });
});