// ==================== Chatbot Functions ====================

// Chatbot state
let chatbotState = {
    isOpen: false,
    isLoading: false
};

// Initialize chatbot on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeChatbot();
});

function initializeChatbot() {
    const chatbotToggle = document.getElementById('chatbotToggle');
    const chatbotClose = document.getElementById('chatbotClose');
    const chatbotClear = document.getElementById('chatbotClear');
    const chatbotForm = document.getElementById('chatbotForm');

    if (chatbotToggle) {
        chatbotToggle.addEventListener('click', toggleChatbot);
    }
    if (chatbotClose) {
        chatbotClose.addEventListener('click', closeChatbot);
    }
    if (chatbotClear) {
        chatbotClear.addEventListener('click', clearChatbot);
    }
    if (chatbotForm) {
        chatbotForm.addEventListener('submit', sendChatMessage);
    }

    // Close chatbot when clicking outside
    document.addEventListener('click', function(event) {
        const chatbotContainer = document.querySelector('.chatbot-container');
        const chatbotWindow = document.getElementById('chatbotWindow');
        const chatbotToggle = document.getElementById('chatbotToggle');
        
        if (chatbotContainer && !chatbotContainer.contains(event.target)) {
            if (chatbotWindow && chatbotWindow.classList.contains('active')) {
                closeChatbot();
            }
        }
    });
}

function toggleChatbot() {
    const chatbotWindow = document.getElementById('chatbotWindow');
    const chatbotToggle = document.getElementById('chatbotToggle');
    
    if (chatbotState.isOpen) {
        closeChatbot();
    } else {
        openChatbot();
    }
}

function openChatbot() {
    const chatbotWindow = document.getElementById('chatbotWindow');
    const chatbotToggle = document.getElementById('chatbotToggle');
    const chatbotInput = document.getElementById('chatbotInput');

    if (chatbotWindow) {
        chatbotWindow.classList.add('active');
        chatbotToggle.classList.add('active');
        chatbotState.isOpen = true;
        
        // Focus on input
        setTimeout(() => {
            if (chatbotInput) {
                chatbotInput.focus();
            }
        }, 100);
    }
}

function closeChatbot() {
    const chatbotWindow = document.getElementById('chatbotWindow');
    const chatbotToggle = document.getElementById('chatbotToggle');

    if (chatbotWindow) {
        chatbotWindow.classList.remove('active');
        chatbotToggle.classList.remove('active');
        chatbotState.isOpen = false;
    }
}

async function sendChatMessage(event) {
    if (event && event.preventDefault) {
        event.preventDefault();
    }

    const chatbotInput = document.getElementById('chatbotInput');
    const message = chatbotInput ? chatbotInput.value.trim() : '';

    if (!message) return;

    // Clear input
    if (chatbotInput) {
        chatbotInput.value = '';
    }

    // Add user message to chat
    addChatMessage(message, 'user');

    // Show loading indicator
    chatbotState.isLoading = true;
    addTypingIndicator();

    try {
        // Send message to backend
        const response = await fetch('/chatbot/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            throw new Error('Failed to get response');
        }

        const data = await response.json();

        if (data.success) {
            // Remove typing indicator
            removeTypingIndicator();
            
            // Add bot response
            addChatMessage(data.response, 'bot');
        } else {
            removeTypingIndicator();
            addChatMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (error) {
        console.error('Chatbot error:', error);
        removeTypingIndicator();
        addChatMessage('Sorry, I\'m having trouble connecting. Please try again.', 'bot');
    } finally {
        chatbotState.isLoading = false;
    }
}

function addChatMessage(message, role) {
    const chatbotMessages = document.getElementById('chatbotMessages');
    
    if (!chatbotMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbot-message ${role}-message`;
    
    // Create message content (handle formatting for bot messages)
    if (role === 'bot') {
        messageDiv.innerHTML = formatBotMessage(message);
    } else {
        messageDiv.textContent = message;
    }

    chatbotMessages.appendChild(messageDiv);

    // Scroll to bottom
    setTimeout(() => {
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }, 0);
}

function formatBotMessage(message) {
    // Replace newlines with <br>
    let formatted = message.replace(/\n/g, '<br>');
    
    // Convert bold text (text between ** **) to <strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert bullet points to list items
    if (formatted.includes('•') || formatted.includes('-')) {
        formatted = formatted.replace(/^•\s+(.+)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/^-\s+(.+)$/gm, '<li>$1</li>');
    }

    // Wrap <li> in <ul>
    if (formatted.includes('<li>')) {
        formatted = '<ul style="margin: 0; padding-left: 20px;">' + 
                   formatted.replace(/<li>.*?<\/li>/gs, match => match) + 
                   '</ul>';
    }

    return formatted;
}

function addTypingIndicator() {
    const chatbotMessages = document.getElementById('chatbotMessages');
    
    if (!chatbotMessages) return;

    const typingDiv = document.createElement('div');
    typingDiv.className = 'chatbot-message bot-message';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = '<div class="loading-indicator">' +
                         '<div class="typing-dot"></div>' +
                         '<div class="typing-dot"></div>' +
                         '<div class="typing-dot"></div>' +
                         '</div>';

    chatbotMessages.appendChild(typingDiv);

    // Scroll to bottom
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

async function clearChatbot() {
    const chatbotMessages = document.getElementById('chatbotMessages');
    
    if (!chatbotMessages) return;

    // Ask for confirmation
    const confirmed = await Swal.fire({
        title: 'Clear Chat?',
        text: 'This will delete all conversation history.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#667eea',
        cancelButtonColor: '#ccc',
        confirmButtonText: 'Clear'
    });

    if (confirmed.isConfirmed) {
        try {
            const response = await fetch('/chatbot/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                // Clear messages
                chatbotMessages.innerHTML = '<div class="chatbot-message bot-message">' +
                    '<p>Hello! 👋 I\'m your Hospital Assistant. How can I help you today?</p>' +
                    '</div>';
            }
        } catch (error) {
            console.error('Error clearing chat:', error);
        }
    }
}

// Keyboard shortcut to focus chatbot (Ctrl+Shift+H)
document.addEventListener('keydown', function(event) {
    if (event.ctrlKey && event.shiftKey && event.key === 'H') {
        event.preventDefault();
        toggleChatbot();
    }
});
