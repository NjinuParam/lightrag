import './style.css'

const CONFIG = {
  runtimeUrl: 'http://localhost:5300/api/portal/chat'
};

function createChatWidget() {
  const app = document.querySelector<HTMLDivElement>('#app');
  if (!app) return;

  app.innerHTML = `
    <div id="weaver-widget">
      <div id="weaver-header">
        <span>Weaver Support</span>
        <span style="font-size: 10px; opacity: 0.8;">Powered by Weaver.ai</span>
      </div>
      <div id="weaver-messages">
        <div class="message agent-message">Hello! I'm your Weaver Agent. How can I assist you with your tools today?</div>
      </div>
      <div id="weaver-input-container">
        <input type="text" id="weaver-input" placeholder="Type a message...">
        <button id="weaver-send">Send</button>
      </div>
    </div>
  `;

  // Get Tenant Key from Script Tag (Simulated for dev mode, in prod it reads document.currentScript)
  // For this dev environment, we'll look for a meta tag or just use a default test key if running standalone
  // In a real embed, we would read: document.currentScript.getAttribute('data-tenant-key')
  let tenantKey = 'test-public-key-456';
  const scriptTag = document.querySelector('script[data-tenant-key]');
  if (scriptTag) {
    tenantKey = scriptTag.getAttribute('data-tenant-key') || tenantKey;
  }

  const messagesContainer = document.getElementById('weaver-messages')!;
  const inputField = document.getElementById('weaver-input') as HTMLInputElement;
  const sendButton = document.getElementById('weaver-send') as HTMLButtonElement;

  function appendMessage(text: string, isUser: boolean) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isUser ? 'user-message' : 'agent-message'}`;
    msgDiv.textContent = text;
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  async function sendMessage() {
    const text = inputField.value.trim();
    if (!text) return;

    appendMessage(text, true);
    inputField.value = '';
    inputField.disabled = true;
    sendButton.disabled = true;

    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing';
    typingDiv.textContent = 'Agent is thinking...';
    messagesContainer.appendChild(typingDiv);

    try {
      const response = await fetch(CONFIG.runtimeUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          publicKey: tenantKey,
          message: text
        })
      });

      const data = await response.json();
      messagesContainer.removeChild(typingDiv);

      if (data.error) {
        appendMessage('Error: ' + data.error, false);
      } else {
        appendMessage(data.Message || data.message, false); // Handle PascalCase from PortalChatResponse or camelCase
      }
    } catch (err) {
      if (messagesContainer.contains(typingDiv)) {
        messagesContainer.removeChild(typingDiv);
      }
      appendMessage('Failed to connect to Weaver Runtime.', false);
      console.error(err);
    } finally {
      inputField.disabled = false;
      sendButton.disabled = false;
      inputField.focus();
    }
  }

  sendButton.addEventListener('click', sendMessage);
  inputField.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });
}

createChatWidget();
