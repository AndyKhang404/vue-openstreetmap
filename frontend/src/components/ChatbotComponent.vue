<template>
  <div class="chatbot-container">
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <p>Ask me anything about places, travel, or locations!</p>
      </div>
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        :class="['message', msg.role === 'user' ? 'user-message' : 'assistant-message']"
      >
        <div class="message-content">
          <div v-if="msg.role === 'user'" class="text-content">{{ msg.content }}</div>
          <div v-else class="markdown-content" v-html="renderMarkdown(msg.content)"></div>
        </div>
      </div>
      <div v-if="isLoading" class="message assistant-message">
        <div class="message-content loading">
          <span class="loading-dots">●●●</span>
        </div>
      </div>
    </div>

    <form class="chat-input-form" @submit.prevent="sendMessage">
      <input
        v-model="inputMessage"
        type="text"
        placeholder="Ask a simple question..."
        :disabled="isLoading"
        class="chat-input"
        maxlength="5000"
      />
      <button type="submit" :disabled="isLoading || !inputMessage.trim()" class="send-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
      </button>
    </form>

    <div v-if="errorMessage" class="error-banner">{{ errorMessage }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, onUnmounted } from 'vue'
import { marked } from 'marked'
import { sendChatMessage } from '../backend'
import { auth } from '@/firebase'
import { onAuthStateChanged } from 'firebase/auth'

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const messagesContainer = ref(null)

const STORAGE_KEY = 'chatbot_history'

let unsub = null

// Load chat history from localStorage
onMounted(() => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      messages.value = JSON.parse(saved)
    }
  } catch (e) {
    console.error('Failed to load chat history', e)
  }

  // Subscribe to auth changes to clear chat history on logout
  unsub = onAuthStateChanged(auth, (user) => {
    if (!user) {
      try {
        localStorage.removeItem(STORAGE_KEY)
      } catch (e) {
        console.error('Failed to remove chat history', e)
      }
      messages.value = []
    }
  })
})

// Unsubscribe on unmount
onUnmounted(() => {
  if (typeof unsub === 'function') unsub()
})

// Save chat history to localStorage whenever it changes
watch(
  messages,
  (newMessages) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newMessages))
    } catch (e) {
      console.error('Failed to save chat history', e)
    }
  },
  { deep: true },
)

// Scroll to bottom when new messages appear
watch(messages, async () => {
  await nextTick()
  scrollToBottom()
})

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const renderMarkdown = (content) => {
  try {
    return marked.parse(content || '')
  } catch {
    return content || ''
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''
  errorMessage.value = ''

  // Add user message to chat
  messages.value.push({
    role: 'user',
    content: userMessage,
  })

  isLoading.value = true

  try {
    // Only send the current user question (not the full history)
    const response = await sendChatMessage([
      {
        role: 'user',
        content: userMessage,
      },
    ])

    // Extract assistant response
    const assistantMessage = response.choices?.[0]?.message?.content || 'No response received.'

    messages.value.push({
      role: 'assistant',
      content: assistantMessage,
    })
  } catch (error) {
    console.error('Chat error:', error)
    errorMessage.value =
      error.message || 'Failed to send message. Please try again or check rate limits.'

    // Remove the user message if request failed
    messages.value.pop()
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.chatbot-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 1rem;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 0;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  text-align: center;
}

.message {
  display: flex;
  gap: 0.5rem;
}

.user-message {
  justify-content: flex-end;
}

.assistant-message {
  justify-content: flex-start;
}

.message-content {
  max-width: 80%;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  word-wrap: break-word;
}

.user-message .message-content {
  background: var(--primary);
  color: var(--on-primary);
}

.assistant-message .message-content {
  background: #f6f8fa;
  border: 1px solid #e1e4e8;
}

.text-content {
  white-space: pre-wrap;
}

.markdown-content :deep(p) {
  margin: 0.5rem 0;
}

.markdown-content :deep(p:first-child) {
  margin-top: 0;
}

.markdown-content :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.markdown-content :deep(code) {
  background: #f0f0f0;
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background: #f6f8fa;
  padding: 0.75rem;
  border-radius: 6px;
  overflow-x: auto;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-dots {
  animation: blink 1.4s infinite;
}

@keyframes blink {
  0%,
  100% {
    opacity: 0.3;
  }
  50% {
    opacity: 1;
  }
}

.chat-input-form {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.chat-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  font-size: 1rem;
}

.chat-input:focus {
  outline: none;
  border-color: var(--border);
}

.chat-input:disabled {
  background: #f6f8fa;
  cursor: not-allowed;
}

.send-button {
  padding: 0.75rem 1rem;
  background: var(--primary);
  color: var(--on-primary);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-button:hover:not(:disabled) {
  background: var(--primary-alt);
}

.send-button:disabled {
  background: var(--color-pigeon-post-200);
  cursor: not-allowed;
}

.send-button svg {
  fill: currentColor;
}

.error-banner {
  padding: 0.75rem;
  background: #fff3cd;
  border: 1px solid #ffecb5;
  border-radius: 6px;
  color: #856404;
  font-size: 0.9rem;
}
</style>
