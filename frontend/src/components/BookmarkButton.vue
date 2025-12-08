<template>
  <button
    @click="handleBookmark"
    :disabled="isLoading"
    class="bookmark-button"
    :class="{ success: showSuccess }"
    title="Bookmark this location"
  >
    <svg
      v-if="!isLoading && !showSuccess"
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
    >
      <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
    </svg>
    <svg
      v-if="!isLoading && showSuccess"
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
    <span v-else-if="isLoading" class="loader-small"></span>
  </button>
</template>

<script setup>
import { ref } from 'vue'
import { auth } from '../firebase'
import { addBookmark } from '../helper'

const props = defineProps({
  lat: {
    type: Number,
    required: true,
  },
  lon: {
    type: Number,
    required: true,
  },
  type: {
    type: String,
    required: true,
  },
  name: {
    type: String,
    required: true,
  },
})

const isLoading = ref(false)
const showSuccess = ref(false)

const handleBookmark = async () => {
  if (!auth.currentUser) {
    alert('Please login to bookmark locations')
    return
  }

  isLoading.value = true

  try {
    const data = await addBookmark(props.lat, props.lon, props.type, props.name)

    showSuccess.value = true
    setTimeout(() => {
      showSuccess.value = false
    }, 1500)

    console.log('Bookmark saved successfully')
    console.log(data)
  } catch (error) {
    console.error('Error saving bookmark:', error)

    // Check if error is about bookmark limit
    if (error.message.includes('Maximum bookmark limit') || error.message.includes('400')) {
      alert(
        'You have reached the maximum limit of 20 bookmarks. Please delete some bookmarks before adding new ones.',
      )
    } else {
      alert('Failed to save bookmark. Please try again.')
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.bookmark-button {
  background: white;
  border: 1px solid #e1e4e8;
  border-radius: 4px;
  padding: 0.5rem;
  margin-left: auto;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.bookmark-button:hover:not(:disabled) {
  background: #f6f8fa;
  border-color: #0366d6;
}

.bookmark-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.bookmark-button.success {
  color: #28a745;
  border-color: #28a745;
  background: #f0fff4;
}

.loader-small {
  width: 16px;
  height: 16px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #0366d6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
