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
        <!-- header with title and close button -->
        <header class="popup-header" v-if="title || true">
          <h3 class="popup-title" v-if="title">{{ title }}</h3>
          <button
            class="popup-close-button"
            type="button"
            @click="visible = false"
            aria-label="Close popup"
          >
            ×
          </button>
        </header>

        <slot />
      </div>
    </div>
  </transition>
</template>

<script setup>
import { onMounted, onBeforeUnmount, watch, ref } from 'vue'

// replace defineProps usage with object form to add title and defaults
const props = defineProps({
  closeOnOverlay: { type: Boolean, default: true },
  title: { type: String, default: '' },
})

const visible = defineModel('visible', { type: Boolean, required: true, default: false })

const panel = ref(null)

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
      // focus panel when opened
      requestAnimationFrame(() => panel.value?.focus())
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  },
)

onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
</script>

<style scoped>
/* Overlay darkens the page so background content appears at ~30% visibility */
.popup-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7); /* ~70% black -> background visible ~30% */
  z-index: 9999;
  /* ensure overlay sits above content */
}

/* Popup panel sizing: choose the smaller of 80vw and 600px; on very small screens use full screen */
.popup-panel {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  outline: none;
  width: 80vw;
  height: 80vh;
  max-width: 100%;
  max-height: 100%;
  overflow: auto;
}

.popup-panel > * {
  padding: 1rem;
}

/* header with title and close button */
.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.popup-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
}

.popup-close-button {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  padding: 0.125rem 0.35rem;
  border-radius: 6px;
}
.popup-close-button:hover {
  background: rgba(0, 0, 0, 0.05);
}
.popup-header > .popup-close-button:only-child {
  margin-left: auto;
}

/* ensure header spacing works on very small screens */
@media (max-width: 480px) {
  .popup-header {
    padding: 0.5rem;
  }
  .popup-close-button {
    font-size: 1.25rem;
  }
}

/* Simple fade/scale transition */
/* .popup-fade-enter-active,
.popup-fade-leave-active {
  transition:
    opacity 180ms ease,
    transform 180ms ease;
}
.popup-fade-enter-from,
.popup-fade-leave-to {
  opacity: 0;
  transform: scale(0.98);
} */
</style>
