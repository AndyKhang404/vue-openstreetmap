<template>
  <div class="translator">
    <textarea v-model="text" placeholder="Enter text to translate" rows="5"></textarea>

    <div class="controls">
      <label>
        To:
        <select v-model="target">
          <option v-for="(name, code) in languages" :key="code" :value="code">
            {{ name }}
          </option>
        </select>
      </label>

      <button @click="doTranslate" :disabled="loading || !text">
        {{ loading ? 'Translating...' : 'Translate' }}
      </button>

      <button @click="swap" title="Set target to detected source">Swap → Detected</button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="translation" class="result">
      <h4>Translation</h4>
      <p class="translated">{{ translation }}</p>
      <small>Detected source: {{ detected || '—' }}</small>
      <div class="result-actions">
        <button @click="copy">{{ copied ? 'Copied' : 'Copy' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const text = ref('')
const target = ref('vi') // default target (adjust as you like)
const translation = ref('')
const detected = ref('')
const loading = ref(false)
const error = ref('')
const copied = ref(false)

// minimal language list (expand as needed)
const languages = {
  en: 'English (English)',
  vi: 'Vietnamese (Tiếng Việt)',
  es: 'Spanish (Español)',
  fr: 'French (Français)',
  de: 'German (Deutsch)',
  'zh-CN': 'Chinese (Simplified) (简体中文)',
  'zh-TW': 'Chinese (Traditional) (繁體中文)',
  ja: 'Japanese (日本語)',
  ko: 'Korean (한국어)',
}

async function doTranslate() {
  if (!text.value) return
  loading.value = true
  error.value = ''
  translation.value = ''
  detected.value = ''

  try {
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=${encodeURIComponent(target.value)}&dt=t&q=${encodeURIComponent(text.value)}`
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Network error: ${res.status}`)
    const data = await res.json()

    // data[0] is an array of translated chunks; data[2] is detected source language (string)
    if (Array.isArray(data) && Array.isArray(data[0])) {
      translation.value =
        data[0].map((chunk) => (Array.isArray(chunk) ? chunk[0] : '')).join('') || ''
      detected.value = data[2] || ''
    } else {
      throw new Error('Unexpected response format from translate API')
    }
  } catch (e) {
    error.value = e.message || 'Translation failed'
  } finally {
    loading.value = false
  }
}

function copy() {
  if (!translation.value) return
  navigator.clipboard
    ?.writeText(translation.value)
    .then(() => {
      copied.value = true
      setTimeout(() => (copied.value = false), 1500)
    })
    .catch(() => {
      // ignore clipboard failures
    })
}

function swap() {
  // set target to detected source if available and swap text with current translation
  if (!detected.value) return
  const prevTarget = target.value
  target.value = detected.value
  // place the previous translation into the input so user can translate back if desired
  if (translation.value) {
    text.value = translation.value
    translation.value = ''
    detected.value = prevTarget // after swap, previous target becomes detected-ish placeholder
  }
}
</script>

<style scoped>
textarea {
  width: 100%;
  box-sizing: border-box;
  margin-bottom: 8px;
  font-size: 14px;
}
.controls {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
button {
  padding: 6px 10px;
  cursor: pointer;
}
.result {
  margin-top: 8px;
}
.error {
  color: #b00020;
  margin-top: 8px;
}
.translated {
  white-space: pre-wrap;
  background: #f9f9f9;
  padding: 8px;
  border-radius: 4px;
}
</style>
