<template>
  <div id="content">
    <header>
      <h1 style="font-size: 1.75rem">Vue OSM viewer</h1>
      <p v-if="foundLocations.length === 0 && !isSearching">Click on the map or search here</p>
      <form id="search-box" @submit.prevent="onSearch">
        <input
          id="search-input"
          v-model="searchQuery"
          type="search"
          placeholder="Search address or place"
          aria-label="Search address"
        />
        <button class="button-shadow" type="submit" :disabled="isSearching">
          <svg
            class="icon-primary"
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
          >
            <path
              d="M23.822 20.88l-6.353-6.354c.93-1.465 1.467-3.2 1.467-5.059.001-5.219-4.247-9.467-9.468-9.467s-9.468 4.248-9.468 9.468c0 5.221 4.247 9.469 9.468 9.469 1.768 0 3.421-.487 4.839-1.333l6.396 6.396 3.119-3.12zm-20.294-11.412c0-3.273 2.665-5.938 5.939-5.938 3.275 0 5.94 2.664 5.94 5.938 0 3.275-2.665 5.939-5.94 5.939-3.274 0-5.939-2.664-5.939-5.939z"
            />
          </svg>
        </button>
      </form>
    </header>

    <section id="location">
      <h2>Location</h2>
      <div>
        <span v-if="foundLocations.length === 0 && !isSearching">No locations found</span>
        <LoaderComponent v-if="foundLocations.length === 0 && isSearching" />
        <div
          style="
            background: #f6f8fa;
            border: 1px solid #e1e4e8;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            display: flex;
            align-items: center;
          "
          v-for="foundLocation in foundLocations"
          :key="
            foundLocation.place_id ||
            foundLocation.id ||
            foundLocation.lat + '-' + foundLocation.lon
          "
        >
          <WeatherIcon
            v-if="!!weather.id && weather.id !== 0"
            :icon_id="weather.id"
            :night="weather.night"
            :description="weather.description"
            :temp="weather.temp"
          />
          <h3 class="clamp-row" style="padding-left: 1rem">
            {{ foundLocation.display_name || 'Selected location' }}
          </h3>
          <BookmarkButton
            :lat="foundLocation.lat"
            :lon="foundLocation.lon"
            :type="'place'"
            :name="foundLocation.display_name"
          />
        </div>
      </div>
    </section>

    <section id="poi">
      <h2>Points of interest</h2>
      <div>
        <span v-if="foundPOIs.length === 0 && !isSearching">No POIs found</span>
        <LoaderComponent v-if="foundPOIs.length === 0 && isSearching" />
        <div
          class="poi-items"
          style="
            background: #f6f8fa;
            border: 1px solid #e1e4e8;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: space-between;
          "
          v-for="foundPOI in foundPOIs"
          :key="foundPOI.id"
        >
          <div>
            <h3>{{ foundPOI.name }}</h3>
            <span>type: {{ foundPOI.type }}</span
            ><br />
          </div>
          <BookmarkButton
            :lat="foundPOI.lat"
            :lon="foundPOI.lon"
            :type="foundPOI.type"
            :name="foundPOI.name"
          />
        </div>
      </div>
    </section>
  </div>

  <!-- Map: listen for select event emitted when user clicks -->
  <MapComponent
    id="map"
    :locations="foundLocations"
    :pois="foundPOIs"
    @select-location="onMapSelect"
  />

  <PopupComponent v-model:visible="translatorPopupVisible" title="Translator">
    <TranslatorComponent />
  </PopupComponent>

  <button
    id="translator-toggle"
    class="button-shadow"
    @click="translatorPopupVisible = true"
    title="Open translator"
    aria-label="Open translator"
  >
    <svg
      class="icon-primary"
      xmlns="http://www.w3.org/2000/svg"
      width="2rem"
      height="2rem"
      viewBox="0 0 24 24"
    >
      <path
        d="M8.722 5.843l.125-.562-1.02-.199-.101.464c-.345-.05-.712-.057-1.083-.019.009-.249.023-.494.045-.728h1.141v-.966h-1.004c.049-.246.092-.394.134-.533l-.997-.3c-.072.245-.134.484-.195.833h-1.138v.966h1.014c-.027.312-.043.637-.048.964-1.119.411-1.595 1.195-1.595 1.905 0 .84.663 1.578 1.709 1.482 1.301-.118 2.169-1.1 2.679-2.308.525.303.746.814.548 1.286-.185.436-.725.852-1.757.831v1.041c1.146.018 2.272-.417 2.715-1.469.431-1.028-.062-2.151-1.172-2.688zm-1.342.71c-.162.36-.375.717-.648.998-.041-.3-.07-.628-.086-.978.249-.032.499-.038.734-.02zm-1.758.336c.028.44.078.844.148 1.205-.927.169-.963-.744-.148-1.205zm2.378 6.111c0-.342.035-.677.102-1h-5.102c-.552 0-1-.449-1-1v-8c0-.551.448-1 1-1h8c.552 0 1 .449 1 1v5.101c.323-.066.657-.101 1-.101h1v-5c0-1.657-1.343-3-3-3h-8c-1.656 0-3 1.343-3 3v8c0 1.657 1.344 3 3 3h5v-1zm13-3h-8c-1.657 0-3 1.343-3 3v8c0 1.657 1.343 3 3 3h8c1.657 0 3-1.343 3-3v-8c0-1.657-1.343-3-3-3zm-1.865 11l-.66-1.846h-3l-.663 1.846h-1.66l3.041-8h1.602l3.053 8h-1.713zm-2.153-6.137l1.051 3.018h-2.103l1.052-3.018z"
      />
    </svg>
  </button>

  <button
    id="login-toggle"
    class="button-shadow"
    @click="loginPopupVisible = true"
    title="Account"
    aria-label="Open account popup"
  >
    <svg
      class="icon-primary"
      xmlns="http://www.w3.org/2000/svg"
      width="2rem"
      height="2rem"
      viewBox="0 0 24 24"
    >
      <path
        d="M12 12c2.7 0 4.9-2.2 4.9-4.9S14.7 2.2 12 2.2 7.1 4.4 7.1 7.1 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.9V22h19.2v-2.7c0-3.3-6.4-4.9-9.6-4.9z"
      />
    </svg>
  </button>

  <PopupComponent v-model:visible="loginPopupVisible" title="Account">
    <AccountComponent @success="loginPopupVisible = false" />
  </PopupComponent>
</template>

<script setup>
import LoaderComponent from '@/components/LoaderComponent.vue'
import MapComponent from '@/components/MapComponent.vue'
import WeatherIcon from '@/components/WeatherIcon.vue'
import PopupComponent from '@/components/PopupComponent.vue'
import TranslatorComponent from '@/components/TranslatorComponent.vue'
import AccountComponent from '@/components/AccountComponent.vue'
import BookmarkButton from '@/components/BookmarkButton.vue'
import { ref } from 'vue'

const isSearching = ref(false)
const foundLocations = ref([])
const foundPOIs = ref([])
const weather = ref({ id: 0, night: false, description: '', temp: null })

const translatorPopupVisible = ref(false)
const loginPopupVisible = ref(false)

// search input model
const searchQuery = ref('')

// NOTE: Provide your OpenWeather API key here (or load from env)
// Vite: use import.meta.env and prefix env var with VITE_
const OPENWEATHER_API_KEY = import.meta.env.VITE_OPENWEATHER_API_KEY || ''

/* NEW: fetch current weather and determine day/night */
const fetchWeather = async (lat, lon) => {
  if (!OPENWEATHER_API_KEY) {
    console.warn('OpenWeather API key not set; skipping weather fetch')
    return
  }

  try {
    const url = `https://api.openweathermap.org/data/2.5/weather?lat=${encodeURIComponent(
      lat,
    )}&lon=${encodeURIComponent(lon)}&appid=${OPENWEATHER_API_KEY}&units=metric`
    const res = await fetch(url, { signal: AbortSignal.timeout(10000) })
    if (!res || !res.ok) {
      console.error('OpenWeather API error', res?.status)
      return
    }
    const data = await res.json()
    const w = (data.weather && data.weather[0]) || {}
    const dt = data.dt // current time (unix)
    const sunrise = data.sys?.sunrise
    const sunset = data.sys?.sunset
    const isDay =
      typeof dt === 'number' && typeof sunrise === 'number' && typeof sunset === 'number'
        ? dt >= sunrise && dt < sunset
        : true
    weather.value = {
      id: w.id || 0,
      night: !isDay,
      description: w.description || '',
      temp: typeof data.main?.temp === 'number' ? data.main.temp : null,
    }
  } catch (err) {
    console.error('fetchWeather failed', err)
  }
}

// implement onSearch to use Nominatim, set single found location, then fetch POIs
const onSearch = async () => {
  if (isSearching.value) return
  const q = String(searchQuery.value || '').trim()
  if (!q) return

  isSearching.value = true
  // reset weather including temp
  weather.value = { id: 0, night: false, description: '', temp: null }
  foundLocations.value = []
  foundPOIs.value = []

  try {
    const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(
      q,
    )}&format=json&addressdetails=1&limit=5`
    const res = await fetch(url, {
      headers: {
        'Accept-Language': 'en',
      },
      signal: AbortSignal.timeout(10000),
    })
    if (!res || !res.ok) {
      console.error('Nominatim error', res.status)
      return
    }
    const data = await res.json()
    const results = Array.isArray(data)
      ? data.filter((r) => r.lat !== undefined && r.lon !== undefined)
      : []
    if (results.length > 0) {
      const first = results[0]
      foundLocations.value = [
        {
          lat: Number(first.lat),
          lon: Number(first.lon),
          display_name: first.display_name,
          place_id: first.place_id,
          type: String(first.type) || 'place',
          class: first.class,
        },
      ]
      // optional: clear the input after successful search
      searchQuery.value = ''
      await fetchWeather(first.lat, first.lon)
      await searchPOIs(first.lat, first.lon)
    } else {
      console.info('No results from Nominatim')
    }
  } catch (err) {
    console.error('Search failed', err)
  } finally {
    isSearching.value = false
  }
}

// When user clicks on the map, set a single foundLocation and fetch POIs
const onMapSelect = async ({ lat, lon }) => {
  if (isSearching.value) return
  isSearching.value = true
  // reset weather including temp
  weather.value = { id: 0, night: false, description: '', temp: null }
  foundPOIs.value = []
  // temporary selected location
  foundLocations.value = [{ lat, lon, display_name: 'Selected location' }]

  // optional: reverse geocode to get a nicer display name
  try {
    const revUrl = `https://nominatim.openstreetmap.org/reverse?lat=${encodeURIComponent(
      lat,
    )}&lon=${encodeURIComponent(lon)}&format=json`
    const revRes = await fetch(revUrl)
    if (revRes.ok) {
      const revData = await revRes.json()
      if (revData?.display_name) {
        foundLocations.value = [
          { lat, lon, display_name: revData.display_name, type: revData.type },
        ]
      }
    }
  } catch (e) {
    // ignore reverse-geocode errors, keep placeholder display_name
    console.log('Cannot reverse-geocode location', e)
  }

  await fetchWeather(lat, lon)
  await searchPOIs(lat, lon)
  isSearching.value = false
}

// Haversine distance
const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const toRad = (deg) => (deg * Math.PI) / 180
  const R = 6371e3 // Earth radius in meters
  const p1 = toRad(lat1)
  const p2 = toRad(lat2)
  const dp = toRad(lat2 - lat1)
  const dl = toRad(lon2 - lon1)
  const a =
    Math.sin(dp / 2) * Math.sin(dp / 2) +
    Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

const searchPOIs = async (latitude, longitude) => {
  if (latitude == null || longitude == null) return
  foundPOIs.value = []
  // Search for nearby POIs using Overpass API
  const radius = 3000 // Search within 3km
  const overpassQuery = `
        [out:json];
        (
          nwr["tourism"](around:${radius},${latitude},${longitude});
        );
        out body 50;
      `

  let overpassResponse = await fetch('https://overpass-api.de/api/interpreter', {
    method: 'POST',
    body: overpassQuery,
    signal: AbortSignal.timeout(10000),
  })
  if (!overpassResponse.ok) {
    console.error('Overpass API error', overpassResponse.status)
    return
  }
  const overpassData = await overpassResponse.json()

  // Process and sort POIs by distance
  const poisWithDistance = (overpassData.elements || [])
    .filter(
      (element) =>
        (element.tags?.name || element.tags?.amenity || element.tags?.shop) &&
        element.lat !== undefined &&
        element.lon !== undefined,
    )
    .map((element, index) => ({
      id: element.id || index,
      name: element.tags?.name || element.tags?.amenity || element.tags?.shop || 'Unknown',
      type:
        element.tags?.amenity ||
        element.tags?.shop ||
        element.tags?.tourism ||
        element.tags?.leisure ||
        'place',
      lat: element.lat,
      lon: element.lon,
      distance: calculateDistance(latitude, longitude, element.lat, element.lon),
    }))
    .sort((a, b) => a.distance - b.distance)
    .slice(0, 5)

  foundPOIs.value = poisWithDistance
}
</script>

<style scoped></style>
