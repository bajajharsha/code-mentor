// Initialize chat app
class ChatApp {
    constructor() {
        this.email = null;
        this.isLoading = false;
        this.initializeEventListeners();

        // Try to restore email from sessionStorage
        this.restoreEmail();

        vscode.postMessage({ command: 'checkSession' });
    }

    initializeEventListeners() {
        // Add enter key support for inputs
        document.getElementById("userInput")?.addEventListener("keypress", (event) => {
            if (event.key === "Enter") {
                this.sendMessage();
            }
        });

        document.getElementById("password")?.addEventListener("keypress", (event) => {
            if (event.key === "Enter") {
                const isLogin = document.getElementById("authTitle").textContent === "Sign in to Code Mentor";
                this.authenticate(isLogin ? "login" : "register");
            }
        });

        // Listen for messages from the extension
        window.addEventListener('message', event => {
            const message = event.data;
            console.log("Message received from extension ==============", message);

            switch (message.command) {
                case 'authResult':
                    this.handleAuthResult(message);
                    break;
                case 'sessionRestored':
                    this.handleSessionRestored(message);
                    break;
                case 'answerResult':
                    console.log("Answer result ==============", message);
                    // setTimeout(() => this.addAssistantMessage(message.answer), 300);
                    setTimeout(() => this.addAssistantMessage(message.answer), 300);
                    // this.addAssistantMessage(message.data);
                    // this.addAssistantMessage(message);
                    break;
            }
        });
    }

    toggleAuth() {
        const authTitle = document.getElementById("authTitle");
        const authButton = document.getElementById("authButton");
        const switchText = document.querySelector(".switch");

        const isLogin = authTitle.textContent === "Sign in to Code Mentor";
        authTitle.textContent = isLogin ? "Create account" : "Sign in to Code Mentor";
        authButton.textContent = isLogin ? "Sign up" : "Sign in";
        switchText.textContent = isLogin ? "Already have an account? Sign in" : "Don't have an account? Sign up";

        authButton.onclick = () => this.authenticate(isLogin ? "register" : "login");
    }

    showError(message, inputId) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;

        // Remove any existing error message
        const existingError = document.querySelector(`#${inputId} + .error-message`);
        if (existingError) {
            existingError.remove();
        }

        // Insert error message after the input
        const input = document.getElementById(inputId);
        input.parentNode.insertBefore(errorDiv, input.nextSibling);

        // Remove error after 3 seconds
        setTimeout(() => errorDiv.remove(), 3000);
    }

    authenticate(action) {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();

        // Clear previous error messages
        document.querySelectorAll('.error-message').forEach(el => el.remove());

        // Validate email
        if (!email) {
            this.showError("Please enter your email", "email");
            return;
        }

        // Basic email format validation
        if (!email.includes('@') || !email.includes('.')) {
            this.showError("Please enter a valid email address", "email");
            return;
        }

        // Validate password
        if (!password) {
            this.showError("Please enter your password", "password");
            return;
        }

        if (password.length < 6) {
            this.showError("Password must be at least 6 characters", "password");
            return;
        }

        // Show loading state
        const authButton = document.getElementById("authButton");
        const originalText = authButton.textContent;
        authButton.disabled = true;
        authButton.innerHTML = '<span class="spinner"></span> Please wait...';

        this.email = email;
        vscode.postMessage({
            command: action,
            email,
            password
        });

        setTimeout(() => {
            const firstFlag = true;
            vscode.postMessage({
                command: 'indexCodebase',
                email,
                firstFlag
            });
        }, 3000);

        // Reset button after 10 seconds (failsafe)
        setTimeout(() => {
            authButton.disabled = false;
            authButton.textContent = originalText;
        }, 10000);
    }

    handleAuthResult(message) {
        // Reset auth button state
        const authButton = document.getElementById("authButton");
        authButton.disabled = false;
        authButton.textContent = authButton.textContent.includes("Sign in") ? "Sign in" : "Sign up";

        if (message.success) {
            // Save email when authentication is successful
            const emailInput = document.getElementById("email");
            this.saveEmail(emailInput.value);

            this.showChat();
            setTimeout(() => this.addAssistantMessage("Hello! How can I help with your code today?"), 300);
        } else {
            const errorMessage = message.error || "Authentication failed. Please try again.";
            this.showError(errorMessage, "password");
        }
    }

    handleSessionRestored(message) {
        console.log("Session restored message:", message);
        if (message.success) {
            // Restore email from session storage
            this.restoreEmail();

            this.showChat();
            setTimeout(() => this.addAssistantMessage("Hello! How can I help with your code today?"), 300);
        } else {
            if (message.error) {
                this.showAuth();
                this.showError(message.error, "email");
            }
        }
    }

    showChat() {
        document.getElementById("authContainer").classList.add("hidden");
        document.getElementById("chatContainer").classList.remove("hidden");
    }

    showAuth() {
        document.getElementById("authContainer").classList.remove("hidden");
        document.getElementById("chatContainer").classList.add("hidden");
    }

    sendMessage() {
        const inputField = document.getElementById("userInput");
        const message = inputField.value.trim();
        if (!message) { return; }

        // Show loading state
        const sendButton = document.querySelector('.send-button');
        sendButton.disabled = true;
        sendButton.innerHTML = '<span class="spinner"></span>';

        this.addUserMessage(message);
        inputField.value = "";

        // Add thinking message
        this.addThinkingMessage();

        vscode.postMessage({
            command: 'getActiveFileDetails',
            text: message,
            email: this.email
        });

        // Reset button after 30 seconds (failsafe)
        setTimeout(() => {
            sendButton.disabled = false;
            sendButton.textContent = 'Send';
        }, 30000);
    }

    addThinkingMessage() {
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'message assistant-message thinking-message';
        thinkingDiv.innerHTML = '<span class="spinner"></span> Thinking...';
        document.getElementById('messages').appendChild(thinkingDiv);
        document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        return thinkingDiv;
    }

    addUserMessage(text) {
        this.addMessage(text, 'user-message');
    }

    addAssistantMessage(message) {
        // Remove thinking message if it exists
        const thinkingMessage = document.querySelector('.thinking-message');
        if (thinkingMessage) {
            thinkingMessage.remove();
        }

        // Reset send button state
        const sendButton = document.querySelector('.send-button');
        sendButton.disabled = false;
        sendButton.textContent = 'Send';

        // Create a new message element
        const messageElement = document.createElement('div');
        messageElement.className = 'message assistant-message';

        // >openmat the message content to handle code blocks
        const formattedContent = this.formatMessageWithCodeBlocks(message);

        // Set the inner HTML of the message element
        messageElement.innerHTML = formattedContent;

        // Add the message to the messages container
        document.getElementById('messages').appendChild(messageElement);

        // Scroll to the bottom of the messages container
        document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
    }

    formatMessageWithCodeBlocks(text) {
        // Regular expression to match code blocks (text between triple backticks)
        // This regex captures the optional language identifier after the first triple backticks
        const codeBlockRegex = /```([\w-]*)\n([\s\S]*?)\n```/g;

        // Replace code blocks with formatted HTML
        let formattedText = text.replace(codeBlockRegex, (match, language, code) => {
            return `<pre class="code-block${language ? ' language-' + language : ''}"><code>${this.escapeHtml(code)}</code></pre>`;
        });

        // Replace line breaks with <br> tags for regular text
        formattedText = formattedText.replace(/\n/g, '<br>');

        return formattedText;
    }

    // Helper function to escape HTML special characters
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // addAssistantMessage(data) {
    //     // const response = data.response;
    //     console.log("Assistant message ==============", data);

    //     const response = data;
    //     this.addMessage(response, 'assistant-message');
    // }

    addMessage(text, className) {
        const messagesDiv = document.getElementById("messages");
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${className}`;
        messageDiv.textContent = text;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    logout() {
        vscode.postMessage({ command: 'logout' });
        // Clear email on logout
        this.email = null;
        sessionStorage.removeItem('userEmail');
        this.showAuth();
        document.getElementById("messages").innerHTML = "";
    }

    // Add method to save email
    saveEmail(email) {
        this.email = email;
        // Store in sessionStorage for persistence
        sessionStorage.setItem('userEmail', email);
    }

    // Add method to restore email
    restoreEmail() {
        const storedEmail = sessionStorage.getItem('userEmail');
        if (storedEmail) {
            this.email = storedEmail;
        }
    }
}

// Make functions globally available
window.chatApp = new ChatApp();
window.toggleAuth = () => window.chatApp.toggleAuth();
window.authenticate = (action) => window.chatApp.authenticate(action);
window.sendMessage = () => window.chatApp.sendMessage();
window.logout = () => window.chatApp.logout();