<template>
  <!-- If user is signed in -->
  <div v-if="user" class="account-content">
    <div class="user-profile">
      <img
        :src="user.photoURL || '/assets/avatar-placeholder.png'"
        :alt="user.displayName || 'User avatar'"
        class="user-avatar"
        @error="handleImageError"
      />
      <div>
        <p>
          Signed in as
          <strong>{{ user.displayName || user.email || 'Unknown' }}</strong>
        </p>
        <p>
          Email verified: <strong>{{ user.emailVerified }}</strong>
        </p>
        <p>
          UID: <code>{{ user.uid }}</code>
        </p>
      </div>
    </div>
    <div style="margin-top: 1rem">
      <button class="button-primary" @click="handleSignOut" :disabled="isProcessing">
        Sign out
      </button>
    </div>
    <div class="divider"></div>
    <h3 style="padding-top: 1rem">Bookmarks ({{ bookmarkCount }} / 20)</h3>

    <div v-if="isLoadingBookmarks" style="padding: 1rem; text-align: center">
      Loading bookmarks...
    </div>

    <div
      v-else-if="bookmarks.length === 0"
      style="padding: 1rem; text-align: center; color: #6a737d"
    >
      No bookmarks yet
    </div>

    <div v-else class="bookmarks-list">
      <div v-for="bookmark in bookmarks" :key="bookmark.id" class="bookmark-item">
        <div>
          <h4>{{ bookmark.name }}</h4>
          <span class="bookmark-type">type: {{ bookmark.type }}</span>
        </div>
        <div class="bookmark-actions">
          <GoToButton
            :lat="bookmark.lat"
            :lon="bookmark.lon"
            :name="bookmark.name"
            @goto="handleGotoBookmark"
          />
          <DeleteBookmarkButton :bookmark-id="bookmark.id" @deleted="handleDeleteBookmark" />
        </div>
      </div>
    </div>
  </div>

  <!-- If not signed in -->
  <div v-else class="account-content">
    <div class="auth-tabs" role="tablist">
      <button
        :class="{ active: mode === 'login' }"
        @click="mode = 'login'"
        type="button"
        :aria-pressed="mode === 'login'"
      >
        Login
      </button>
      <button
        :class="{ active: mode === 'register' }"
        @click="mode = 'register'"
        type="button"
        :aria-pressed="mode === 'register'"
      >
        Create account
      </button>

      <!-- Added Forgot password tab -->
      <button
        :class="{ active: mode === 'forgot' }"
        @click="mode = 'forgot'"
        type="button"
        :aria-pressed="mode === 'forgot'"
      >
        Forgot password
      </button>
    </div>

    <!-- Show login/register form when not in 'forgot' -->
    <form v-if="mode !== 'forgot'" @submit.prevent="handleSubmit" class="auth-form">
      <label>
        Email
        <input v-model="email" type="email" required autocomplete="email" />
      </label>

      <label>
        Password
        <input
          v-model="password"
          type="password"
          required
          minlength="12"
          :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
        />
      </label>

      <div v-if="errorMessage" class="error">
        {{ errorMessage }}
      </div>

      <div class="form-actions">
        <button class="button-primary" type="submit" :disabled="isProcessing">
          {{ mode === 'login' ? 'Sign in' : 'Create account' }}
        </button>
        <span v-if="isProcessing" aria-live="polite">Processing…</span>
      </div>
    </form>

    <!-- Password reset form -->
    <form v-else @submit.prevent="handlePasswordReset" class="auth-form">
      <label>
        Email
        <input v-model="forgotEmail" type="email" required autocomplete="email" />
      </label>

      <div v-if="resetError" class="error">
        {{ resetError }}
      </div>
      <div v-if="resetMessage" style="color: #0a7; padding: 0.5rem; border-radius: 6px">
        {{ resetMessage }}
      </div>

      <div class="form-actions">
        <button class="button-primary" type="submit" :disabled="isProcessing">
          Send password reset email
        </button>
        <span v-if="isProcessing" aria-live="polite">Processing…</span>
      </div>
    </form>

    <div class="divider">
      <small>Or</small>
    </div>

    <button class="button-primary" @click="handleGoogle" :disabled="isProcessing">
      Continue with Google
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { auth } from '@/firebase'
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
  sendEmailVerification,
  onAuthStateChanged,
  sendPasswordResetEmail,
} from 'firebase/auth'
import { getBookmarks } from '@/backend'
import DeleteBookmarkButton from './DeleteBookmarkButton.vue'
import GoToButton from './GoToButton.vue'

const emit = defineEmits(['success', 'goto-bookmark'])

const email = ref('')
const password = ref('')
const mode = ref('login')
const isProcessing = ref(false)
const errorMessage = ref('')
const user = ref(null)
const bookmarkCount = ref(0)
const bookmarks = ref([])
const isLoadingBookmarks = ref(false)
const forgotEmail = ref('')
const resetMessage = ref('')
const resetError = ref('')

let unsub = null

// Helper functions for localStorage caching
const BOOKMARKS_CACHE_KEY = 'bookmarks_cache'
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

function getCachedBookmarks() {
  try {
    const cached = localStorage.getItem(`${BOOKMARKS_CACHE_KEY}`)
    if (!cached) return null

    const { bookmarks, timestamp } = JSON.parse(cached)
    const isStale = Date.now() - timestamp > CACHE_DURATION

    return isStale ? null : { bookmarks }
  } catch (err) {
    console.error('Failed to load cached bookmarks', err)
    return null
  }
}

function setCachedBookmarks(data) {
  try {
    const cacheData = {
      bookmarks: data.bookmarks,
      timestamp: Date.now(),
    }
    localStorage.setItem(`${BOOKMARKS_CACHE_KEY}`, JSON.stringify(cacheData))
  } catch (err) {
    console.error('Failed to cache bookmarks', err)
  }
}

function clearCachedBookmarks() {
  try {
    localStorage.removeItem(`${BOOKMARKS_CACHE_KEY}`)
  } catch (err) {
    console.error('Failed to clear cached bookmarks', err)
  }
}

onMounted(() => {
  unsub = onAuthStateChanged(auth, async (u) => {
    user.value = u
      ? {
          uid: u.uid,
          email: u.email,
          displayName: u.displayName,
          photoURL: u.photoURL,
          emailVerified: u.emailVerified,
        }
      : null

    if (u) {
      // Load cached bookmarks first
      const cached = getCachedBookmarks()
      if (cached) {
        bookmarks.value = Array.isArray(cached.bookmarks) ? cached.bookmarks : []
        bookmarkCount.value = bookmarks.value.length
        // Don't fetch if cache is fresh
        return
      }
      // Only fetch if no valid cache
      await fetchBookmarks()
    } else {
      bookmarks.value = []
      bookmarkCount.value = 0
    }
  })
})

onBeforeUnmount(() => {
  if (typeof unsub === 'function') unsub()
})

async function handleSubmit() {
  errorMessage.value = ''
  isProcessing.value = true
  try {
    if (mode.value === 'login') {
      await signInWithEmailAndPassword(auth, email.value, password.value)
    } else {
      const userCredential = await createUserWithEmailAndPassword(auth, email.value, password.value)
      try {
        await sendEmailVerification(userCredential.user)
      } catch (err) {
        console.warn('Failed to send verification email', err)
      }
    }
    emit('success')
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
    emit('success')
  } catch (err) {
    errorMessage.value = (err && err.message) || 'Google sign-in failed'
  } finally {
    isProcessing.value = false
  }
}

async function handleSignOut() {
  isProcessing.value = true
  try {
    if (auth.currentUser) {
      clearCachedBookmarks()
    }
    await signOut(auth)
  } catch (err) {
    console.error('Sign out failed', err)
  } finally {
    isProcessing.value = false
  }
}

async function fetchBookmarks() {
  if (!auth.currentUser) return

  isLoadingBookmarks.value = true
  try {
    const data = await getBookmarks()
    bookmarks.value = Array.isArray(data.bookmarks) ? data.bookmarks : []
    bookmarkCount.value = bookmarks.value.length

    // Cache the bookmarks
    setCachedBookmarks(data)
  } catch (err) {
    console.error('Failed to fetch bookmarks', err)
    bookmarks.value = []
    bookmarkCount.value = 0
  } finally {
    isLoadingBookmarks.value = false
  }
}

async function handleDeleteBookmark() {
  // Refresh bookmarks after deletion
  await fetchBookmarks()
}

function handleImageError(event) {
  event.target.src = '/assets/avatar-placeholder.png'
}

function handleGotoBookmark(location) {
  emit('goto-bookmark', location)
}

async function handlePasswordReset() {
  resetError.value = ''
  resetMessage.value = ''
  if (!forgotEmail.value) {
    resetError.value = 'Please enter your email address.'
    return
  }
  isProcessing.value = true
  try {
    await sendPasswordResetEmail(auth, forgotEmail.value)
    resetMessage.value = 'Password reset email sent. Check your inbox.'
  } catch (err) {
    resetError.value = (err && err.message) || 'Failed to send password reset email.'
  } finally {
    isProcessing.value = false
  }
}
</script>

<style scoped>
.account-content {
  padding: 0;
}

.auth-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.auth-tabs button {
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: #fff;
  cursor: pointer;
  transition: all 0.2s;
}

.auth-tabs button:hover {
  background: #f6f8fa;
}

.auth-tabs button.active {
  background: var(--primary);
  color: var(--on-primary);
  border-color: var(--border);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.auth-form label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-weight: 500;
}

.auth-form input {
  width: 100%;
  padding: 0.5rem;
  box-sizing: border-box;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  font-size: 1rem;
}

.auth-form input:focus {
  outline: none;
  border-color: var(--border);
  box-shadow: 0 0 0 3px rgba(3, 102, 214, 0.1);
}

.error {
  color: #b00020;
  font-size: 0.875rem;
  padding: 0.5rem;
  background: #ffebee;
  border-radius: 6px;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.divider {
  margin: 1.5rem 0;
  text-align: center;
  position: relative;
}

.divider::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  width: 100%;
  height: 1px;
  background: #e1e4e8;
  z-index: 0;
}

.divider small {
  position: relative;
  background: #fff;
  padding: 0 0.5rem;
  z-index: 1;
  color: #6a737d;
}

.button-primary {
  background: var(--primary);
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: background 0.2s;
}

.button-primary:hover:not(:disabled) {
  background: var(--primary-alt);
}

.button-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.bookmarks-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
}

.bookmark-item {
  background: #f6f8fa;
  border: 1px solid #e1e4e8;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.bookmark-item h4 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  font-weight: 600;
}

.bookmark-type {
  font-size: 0.875rem;
  color: #6a737d;
}

.user-profile {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 1rem;
}

.user-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e1e4e8;
}

.bookmark-actions {
  display: flex;
  gap: 0.5rem;
}
</style>
