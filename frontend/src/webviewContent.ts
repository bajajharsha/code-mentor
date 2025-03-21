export function getWebviewContent() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Code Mentor</title>
  <style>
    body {
      margin: 0;
      padding: 10px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--vscode-editor-background);
      color: var(--vscode-foreground);
      font-size: 13px;
      height: 100vh;
      box-sizing: border-box;
      overflow: hidden;
    }
    
    .container {
      display: flex;
      flex-direction: column;
      height: 100%;
      width: 100%;
      align-items: center;
    }
    
    .auth-form {
      width: 90%;
      max-width: 280px;
      margin: 20px auto;
    }
    
    .hidden { 
      display: none; 
    }
    
    h2, h3 {
      margin-top: 0;
      margin-bottom: 16px;
      color: var(--vscode-foreground);
      font-weight: 500;
      text-align: center;
    }
    
    .input-group {
      position: relative;
      margin-bottom: 16px;
      width: 100%;
    }
    
    .input-group label {
      display: block;
      margin-bottom: 6px;
      font-size: 12px;
      color: var(--vscode-descriptionForeground);
    }
    
    input {
      width: 100%;
      padding: 8px 10px;
      border-radius: 4px;
      border: 1px solid var(--vscode-input-border);
      background: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      font-size: 13px;
      box-sizing: border-box;
    }
    
    input:focus {
      outline: 1px solid var(--vscode-focusBorder);
      border-color: var(--vscode-focusBorder);
    }
    
    button {
      width: 100%;
      padding: 8px;
      margin-top: 8px;
      background: var(--vscode-button-background);
      border: none;
      border-radius: 4px;
      color: var(--vscode-button-foreground);
      cursor: pointer;
      font-size: 13px;
      transition: background-color 0.2s;
    }
    
    button:hover {
      background: var(--vscode-button-hoverBackground);
    }
    
    .switch {
      color: var(--vscode-textLink-foreground);
      cursor: pointer;
      margin-top: 16px;
      display: inline-block;
      text-align: center;
      width: 100%;
      font-size: 12px;
    }
    
    .switch:hover {
      color: var(--vscode-textLink-activeForeground);
      text-decoration: underline;
    }
    
    #messages {
      flex: 1;
      overflow-y: auto;
      background: var(--vscode-editor-background);
      border: 1px solid var(--vscode-widget-border);
      border-radius: 4px;
      margin-bottom: 8px;
      padding: 8px;
      width: 100%;
    }
    
    .message {
      padding: 8px 12px;
      border-radius: 4px;
      margin-bottom: 8px;
      word-wrap: break-word;
      max-width: 85%;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    .user-message {
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      margin-left: auto;
      border-radius: 12px 12px 0 12px;
    }
    
    .assistant-message {
      background: var(--vscode-editor-inactiveSelectionBackground);
      color: var(--vscode-foreground);
      margin-right: auto;
      border-radius: 12px 12px 12px 0;
    }
    
    .chat-container {
      width: 100%;
      display: flex;
      flex-direction: column;
      height: 100%;
    }
    
    .input-area {
      display: flex;
      margin-top: 8px;
      padding: 6px;
      background: var(--vscode-input-background);
      border-radius: 4px;
      border: 1px solid var(--vscode-input-border);
    }
    
    #userInput {
      flex: 1;
      margin-right: 8px;
      margin-top: 0;
      border: none;
      background: transparent;
      padding: 4px 8px;
    }
    
    #userInput:focus {
      outline: none;
      border: none;
    }
    
    .send-button {
      width: auto;
      margin: 0;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 12px;
    }
    
    .logout-button {
      background: transparent;
      border: 1px solid var(--vscode-errorForeground);
      color: var(--vscode-errorForeground);
      margin-top: 12px;
      width: auto;
      align-self: center;
      font-size: 12px;
    }
    
    .logout-button:hover {
      background: rgba(255, 0, 0, 0.1);
    }
    
    .brand {
      font-size: 11px;
      color: var(--vscode-descriptionForeground);
      margin-top: 16px;
      text-align: center;
    }
    
    .logo {
      margin: 20px auto 16px;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border-radius: 50%;
      font-size: 20px;
      font-weight: bold;
    }
  </style>
</head>
<body>

  <!-- Login / Signup Page -->
  <div id="authContainer" class="container">
    <div class="logo">CM</div>
    <h2 id="authTitle">Sign in to Code Mentor</h2>
    <div class="auth-form">
      <div class="input-group">
        <label for="email">Email</label>
        <input type="email" id="email" placeholder="your@email.com" required />
      </div>
      <div class="input-group">
        <label for="password">Password</label>
        <input type="password" id="password" placeholder="Your password" required />
      </div>
      <button id="authButton" onclick="authenticate('login')">Sign in</button>
      <p class="switch" onclick="toggleAuth()">Don't have an account? Sign up</p>
      <p class="brand">Code Mentor v1.0</p>
    </div>
  </div>

  <!-- Chat Interface (Hidden Initially) -->
  <div id="chatContainer" class="container hidden">
    <div class="chat-container">
      <h3>Code Mentor</h3>
      <div id="messages"></div>
      <div class="input-area">
        <input type="text" id="userInput" placeholder="Ask a question..." />
        <button class="send-button" onclick="sendMessage()">Send</button>
      </div>
      <button class="logout-button" onclick="logout()">Sign out</button>
    </div>
  </div>

  <script>
    const vscode = acquireVsCodeApi();
    // Check if user is already logged in
    if (localStorage.getItem("authenticated")) {
    // if (true) {
      document.getElementById("authContainer").classList.add("hidden");
      document.getElementById("chatContainer").classList.remove("hidden");
      // Add welcome message
      setTimeout(() => addAssistantMessage("Hello! How can I help with your code today?"), 300);
    }

    function toggleAuth() {
      const authTitle = document.getElementById("authTitle");
      const authButton = document.getElementById("authButton");
      const switchText = document.querySelector(".switch");

      const isLogin = authTitle.textContent === "Sign in to Code Mentor";
      authTitle.textContent = isLogin ? "Create account" : "Sign in to Code Mentor";
      authButton.textContent = isLogin ? "Sign up" : "Sign in";
      switchText.textContent = isLogin ? "Already have an account? Sign in" : "Don't have an account? Sign up";

      authButton.onclick = () => authenticate(isLogin ? "register" : "login");
    }

    // function toggleAuth() {
    //   const isLogin = document.getElementById("authTitle").textContent === "Sign in to Code Mentor";
    //   document.getElementById("authTitle").textContent = isLogin ? "Create account" : "Sign in to Code Mentor";
    //   document.querySelector("button").textContent = isLogin ? "Sign up" : "Sign in";
    //   document.querySelector(".switch").textContent = isLogin ? "Already have an account? Sign in" : "Don't have an account? Sign up";
    // }

    // function authenticate() {
    //   const email = document.getElementById("email").value;
    //   console.log("Email =========: ", email);
    //   const password = document.getElementById("password").value;
    //   if (email && password) {
    //     // Send to extension instead of using localStorage
    //     vscode.postMessage({
    //       command: 'register',
    //       email,
    //       password
    //     });
    //   } else {
    //     alert("Please enter both email and password");
    //   }
    // }

    function authenticate(action) {
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;

      if (email && password) {
        vscode.postMessage({
          command: action,  // 'login' or 'register'
          email,
          password
        });
      } else {
        alert("Please enter both email and password");
      }
    }

    function addUserMessage(text) {
      const messagesDiv = document.getElementById("messages");
      const messageDiv = document.createElement("div");
      messageDiv.className = "message user-message";
      messageDiv.textContent = text;
      messagesDiv.appendChild(messageDiv);
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    function addAssistantMessage(text) {
      const messagesDiv = document.getElementById("messages");
      const messageDiv = document.createElement("div");
      messageDiv.className = "message assistant-message";
      messageDiv.textContent = text;
      messagesDiv.appendChild(messageDiv);
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    function sendMessage() {
      const inputField = document.getElementById("userInput");
      const message = inputField.value.trim();
      if (!message) return;
      
      addUserMessage(message);
      inputField.value = "";
      
      // Simulate response
      setTimeout(() => {
        // Example responses based on keywords
        if (message.toLowerCase().includes("hello") || message.toLowerCase().includes("hi")) {
          addAssistantMessage("Hello! How can I help with your code today?");
        } else if (message.toLowerCase().includes("typescript") || message.toLowerCase().includes("ts")) {
          addAssistantMessage("TypeScript is a strongly typed programming language that builds on JavaScript. I can help you with TypeScript questions!");
        } else if (message.toLowerCase().includes("vscode") || message.toLowerCase().includes("extension")) {
          addAssistantMessage("VS Code extensions are powerful tools that can enhance your development experience. What would you like to know about them?");
        } else {
          addAssistantMessage("I'm analyzing your question. I'll need more information to provide a helpful response. Could you provide more details or code examples?");
        }
      }, 1000);
    }

    function logout() {
      // localStorage.removeItem("authenticated");
      vscode.postMessage({ command: 'logout' });
      document.getElementById("authContainer").classList.remove("hidden");
      document.getElementById("chatContainer").classList.add("hidden");
      document.getElementById("messages").innerHTML = "";
    }

    // Add enter key support for inputs
    document.getElementById("userInput").addEventListener("keypress", function(event) {
      if (event.key === "Enter") {
        sendMessage();
      }
    });

    document.getElementById("password").addEventListener("keypress", function(event) {
      if (event.key === "Enter") {
        authenticate(action);
      }
    });

    window.addEventListener('message', event => {
    const message = event.data;
  
    switch (message.command) {
      case 'authResult':
        if (message.success) {
          document.getElementById("authContainer").classList.add("hidden");
          document.getElementById("chatContainer").classList.remove("hidden");
          setTimeout(() => addAssistantMessage("Hello! How can I help with your code today?"), 300);
        } else {
          alert("Authentication failed: " + message.error);
        }
        break;

      case 'sessionRestored':
        if (message.success) {
          document.getElementById("authContainer").classList.add("hidden");
          document.getElementById("chatContainer").classList.remove("hidden");
          setTimeout(() => addAssistantMessage("Hello! How can I help with your code today?"), 300);
        } else {
          //show message user logged out
          alert("Authentication failed: " + message.error);
        }
        break;
        

      case 'answerResult':
        addAssistantMessage(message.answer);
        break;
    }
  });
  </script>
</body>
</html>`;
}