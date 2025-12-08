<template>
  <transition name="popup-fade">
    <div
      v-if="visible"
      class="popup-overlay"
      @click.self="onOverlayClick"
      role="dialog"
      aria-modal="true"
    >
      <div class="popup-panel" ref="panel" tabindex="-1">
        <header class="popup-header">
          <h3 class="popup-title">{{ title || 'Account' }}</h3>
          <button
            class="popup-close-button"
            type="button"
            @click="visible = false"
            aria-label="Close popup"
          >
            ×
          </button>
        </header>

        <div class="popup-content">
          <!-- If user is signed in -->
          <div v-if="user">
            <p>
              Signed in as
              <strong>{{ user.displayName || user.email || 'Unknown' }}</strong>
            </p>
            <p>
              UID: <code>{{ user.uid }}</code>
            </p>
            <div style="margin-top: 1rem">
              <button class="button-shadow" @click="handleSignOut" :disabled="isProcessing">
                Sign out
              </button>
            </div>
          </div>

          <!-- If not signed in -->
          <div v-else>
            <div
              class="auth-tabs"
              role="tablist"
              style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem"
            >
              <button
                :class="{ active: mode === 'login' }"
                @click="mode = 'login'"
                type="button"
                aria-pressed="mode === 'login'"
              >
                Login
              </button>
              <button
                :class="{ active: mode === 'register' }"
                @click="mode = 'register'"
                type="button"
                aria-pressed="mode === 'register'"
              >
                Create account
              </button>
            </div>

            <form @submit.prevent="handleSubmit" class="auth-form">
              <label style="display: block; margin-bottom: 0.5rem">
                Email
                <input v-model="email" type="email" required autocomplete="email" />
              </label>

              <label style="display: block; margin-bottom: 0.5rem">
                Password
                <input
                  v-model="password"
                  type="password"
                  required
                  minlength="6"
                  autocomplete="current-password"
                />
              </label>

              <div v-if="errorMessage" class="error" style="color: #b00020; margin-bottom: 0.5rem">
                {{ errorMessage }}
              </div>

              <div style="display: flex; gap: 0.5rem; align-items: center">
                <button class="button-shadow" type="submit" :disabled="isProcessing">
                  {{ mode === 'login' ? 'Sign in' : 'Create account' }}
                </button>
                <span v-if="isProcessing" aria-live="polite">Processing…</span>
              </div>
            </form>

            <div style="margin: 1rem 0; text-align: center">
              <small>Or</small>
            </div>

            <div style="display: flex; gap: 0.5rem; flex-direction: column">
              <button class="button-shadow" @click="handleGoogle" :disabled="isProcessing">
                Continue with Google
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { auth } from '../firebase.js'
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
} from 'firebase/auth'

// props and v-model binding (visible)
const props = defineProps({
  closeOnOverlay: { type: Boolean, default: true },
  title: { type: String, default: 'Account' },
})
const visible = defineModel('visible', { type: Boolean, required: true, default: false })

const panel = ref(null)
const email = ref('')
const password = ref('')
const mode = ref('login') // 'login' | 'register'
const isProcessing = ref(false)
const errorMessage = ref('')
const user = ref(null)

function onOverlayClick() {
  if (props.closeOnOverlay) visible.value = false
}

function onKey(e) {
  if (e.key === 'Escape' && visible.value) visible.value = false
}

watch(
  () => visible.value,
  (val) => {
    if (val) {
      requestAnimationFrame(() => panel.value?.focus())
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
      // reset minimal fields when closed
      errorMessage.value = ''
      isProcessing.value = false
    }
  },
)

onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})

// Track auth state
let unsub = null
onMounted(() => {
  unsub = onAuthStateChanged(auth, (u) => {
    user.value = u ? { uid: u.uid, email: u.email, displayName: u.displayName } : null
  })
})
onBeforeUnmount(() => {
  if (typeof unsub === 'function') unsub()
})

// Auth handlers
async function handleSubmit() {
  errorMessage.value = ''
  isProcessing.value = true
  try {
    if (mode.value === 'login') {
      await signInWithEmailAndPassword(auth, email.value, password.value)
      // success -> close popup
      visible.value = false
    } else {
      // register
      await createUserWithEmailAndPassword(auth, email.value, password.value)
      visible.value = false
    }
  } catch (err) {
    errorMessage.value = (err && err.message) || 'Authentication failed'
  } finally {
    isProcessing.value = false
  }
}

async function handleGoogle() {
  errorMessage.value = ''
  isProcessing.value = true
  try {
    const provider = new GoogleAuthProvider()
    await signInWithPopup(auth, provider)
    visible.value = false
  } catch (err) {
    errorMessage.value = (err && err.message) || 'Google sign-in failed'
  } finally {
    isProcessing.value = false
  }
}

async function handleSignOut() {
  isProcessing.value = true
  try {
    await signOut(auth)
    // keep popup open (or optionally close)
  } catch (err) {
    console.error('Sign out failed', err)
  } finally {
    isProcessing.value = false
  }
}
</script>

<style scoped>
/* minimal styles to align with PopupComponent */
.popup-content {
  padding: 1rem;
}
.auth-tabs button {
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #fff;
  cursor: pointer;
}
.auth-tabs button.active {
  background: #0366d6;
  color: #fff;
}
.auth-form input {
  width: 100%;
  padding: 0.5rem;
  margin-top: 0.25rem;
  box-sizing: border-box;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
}
.button-shadow {
  background: #0366d6;
  color: #fff;
  border: none;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
}
.button-shadow:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
