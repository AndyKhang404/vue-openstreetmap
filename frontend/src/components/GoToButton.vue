<template>
  <button @click="handleGoTo" class="goto-button" title="Go to this location">
    <svg
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
      <line x1="5" y1="12" x2="19" y2="12"></line>
      <polyline points="12 5 19 12 12 19"></polyline>
    </svg>
  </button>
</template>

<script setup>
const props = defineProps({
  lat: {
    type: Number,
    required: true,
  },
  lon: {
    type: Number,
    required: true,
  },
  name: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['goto'])

const handleGoTo = () => {
  emit('goto', { lat: props.lat, lon: props.lon, name: props.name })
}
</script>

<style scoped>
.goto-button {
  background: white;
  border: 1px solid #e1e4e8;
  border-radius: 4px;
  padding: 0.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #0366d6;
}

.goto-button:hover {
  background: #f0f7ff;
  border-color: #0366d6;
}
</style>
