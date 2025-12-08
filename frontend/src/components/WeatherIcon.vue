<template>
  <div
    style="
      display: flex;
      flex-direction: column;
      align-items: center;
      border-right: 1px solid var(--border);
      padding: 0.75rem 0.75rem 0.75rem 0;
    "
  >
    <abbr :title="props.description">
      <i :class="'wi ' + icon"></i>
    </abbr>
    <div v-if="hasTemp" class="weather-temp" aria-hidden="false">{{ formattedTemp }}</div>
  </div>
</template>

<script setup>
const props = defineProps({
  icon_id: {
    type: Number,
    default: () => 800,
  },
  night: {
    type: Boolean,
    default: () => false,
  },
  description: {
    type: String,
    default: () => 'No description',
  },
  temp: {
    type: Number,
    default: () => null,
  },
})

import { computed } from 'vue'

const icon = computed(() => {
  const id = Number(props.icon_id)
  const isNight = !!props.night
  let code = ''

  if (!isNight) {
    // day
    if (id === 800)
      code = 'wi-day-sunny' // clear
    else if (id === 801)
      code = 'wi-day-sunny-overcast' // few clouds
    else if (id === 802)
      code = 'wi-day-cloudy' // scattered clouds
    else if (id === 803 || id === 804)
      code = 'wi-cloudy' // broken/overcast
    else if (id >= 200 && id < 300)
      code = 'wi-day-thunderstorm' // thunderstorm
    else if (id >= 300 && id < 400)
      code = 'wi-day-sprinkle' // drizzle
    else if (id >= 500 && id < 600)
      code = 'wi-day-rain' // rain
    else if (id >= 600 && id < 700)
      code = 'wi-day-snow' // snow
    else if (id === 701 || id === 741)
      code = 'wi-day-fog' // mist/fog
    else if (id === 711)
      code = 'wi-smoke' // smoke
    else if (id === 721)
      code = 'wi-day-haze' // haze
    else if (id === 731 || id === 761 || id === 762)
      code = 'wi-dust' // dust
    else if (id === 751)
      code = 'wi-sandstorm' // sand
    else code = 'wi-day-sunny'
  } else {
    // night
    if (id === 800)
      code = 'wi-night-clear' // clear
    else if (id === 801)
      code = 'wi-night-alt-partly-cloudy' // few clouds
    else if (id === 802)
      code = 'wi-night-alt-cloudy' // scattered clouds
    else if (id === 803 || id === 804)
      code = 'wi-cloudy' // broken/overcast
    else if (id >= 200 && id < 300)
      code = 'wi-night-alt-thunderstorm' // thunderstorm
    else if (id >= 300 && id < 400)
      code = 'wi-night-sprinkle' // drizzle
    else if (id >= 500 && id < 600)
      code = 'wi-night-alt-rain' // rain
    else if (id >= 600 && id < 700)
      code = 'wi-night-alt-snow' // snow
    else if (id === 701 || id === 741)
      code = 'wi-night-fog' // mist/fog
    else if (id === 711)
      code = 'wi-smoke' // smoke
    else if (id === 721)
      code = 'wi-day-haze' // haze
    else if (id === 731 || id === 761 || id === 762)
      code = 'wi-dust' // dust
    else if (id === 751)
      code = 'wi-sandstorm' // sand
    else code = 'wi-night-clear'
  }

  return code
})

const hasTemp = computed(
  () => props.temp !== null && props.temp !== undefined && !Number.isNaN(props.temp),
)
const formattedTemp = computed(() => {
  if (!hasTemp.value) return ''
  // Round to nearest integer and show Celsius symbol
  return `${Math.round(props.temp)}°C`
})
</script>

<style scoped>
.weather-temp {
  font-size: 0.9rem;
  margin-top: 0.25rem;
  color: #333;
}
</style>
