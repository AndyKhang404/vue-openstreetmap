<template>
  <button @click="handleDelete" :disabled="isLoading" class="delete-button" title="Delete bookmark">
    <svg
      v-if="!isLoading"
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
      <polyline points="3 6 5 6 21 6"></polyline>
      <path
        d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
      ></path>
    </svg>
    <span v-else class="loader-small"></span>
  </button>
</template>

<script setup>
import { ref } from 'vue'
import { auth } from '../firebase'
import { deleteBookmark } from '../helper'

const props = defineProps({
  bookmarkId: {
    type: [String, Number],
    required: true,
  },
})

const emit = defineEmits(['deleted'])

const isLoading = ref(false)

const handleDelete = async () => {
  if (!auth.currentUser) {
    alert('Please login to delete bookmarks')
    return
  }

  if (!confirm('Are you sure you want to delete this bookmark?')) {
    return
  }

  isLoading.value = true

  try {
    await deleteBookmark(props.bookmarkId)
    console.log('Bookmark deleted successfully')
    emit('deleted')
  } catch (error) {
    console.error('Error deleting bookmark:', error)
    alert('Failed to delete bookmark. Please try again.')
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.delete-button {
  background: white;
  border: 1px solid #e1e4e8;
  border-radius: 4px;
  padding: 0.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #d73a49;
}

.delete-button:hover:not(:disabled) {
  background: #ffeef0;
  border-color: #d73a49;
}

.delete-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loader-small {
  width: 16px;
  height: 16px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #d73a49;
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
