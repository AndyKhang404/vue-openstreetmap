<template>
  <div id="content">
    <header>
      <h1 style="font-size: 1.75rem">vue-openstreetmap</h1>
      <p v-if="foundLocations.length === 0 && !isSearching">Click on the map or search here</p>
      <form id="search-box" @submit.prevent="onSearch">
        <input
          id="search-input"
          v-model="searchQuery"
          type="search"
          placeholder="Search address or place"
          aria-label="Search address"
        />
        <button type="submit" :disabled="isSearching">
          {{ isSearching ? 'Searching...' : 'Search' }}
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
          />
          <h3 class="clamp-row" style="padding-left: 1rem">
            {{ foundLocation.display_name || foundLocation.name || 'Selected location' }}
          </h3>
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
          "
          v-for="foundPOI in foundPOIs"
          :key="foundPOI.id"
        >
          <h3>{{ foundPOI.name }}</h3>
          <span>type: {{ foundPOI.type }}</span
          ><br />
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
</template>

<script setup>
import LoaderComponent from './components/LoaderComponent.vue'
import MapComponent from './components/MapComponent.vue'
import WeatherIcon from './components/WeatherIcon.vue'
import { ref } from 'vue'

const userAgent = 'vue-openstreetmap/1.0 (Contact: andykhang404@gmail.com)'

const isSearching = ref(false)
const foundLocations = ref([])
const foundPOIs = ref([])
const weather = ref({ id: 0, night: false, description: '' })

// search input model
const searchQuery = ref('')

// NOTE: Provide your OpenWeather API key here (or load from env)
// Vite: use import.meta.env and prefix env var with VITE_
const OPENWEATHER_API_KEY = import.meta.env.VITE_OPENWEATHER_API_KEY || ''

// fetch request with timeout
const fetchTimeout = async (fetchURL, fetchObj, timeout) => {
  if (Object.hasOwn(fetchObj, 'signal')) {
    console.warn('Fetch object has another signal! Abort fetchTimeout...')
    return { ok: false, status: 'Object has multiple signals' }
  }
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  const fetchOptions = {
    ...fetchObj, // Spread existing options
    signal: controller.signal, // Add the AbortController's signal
  }

  let response
  try {
    response = await fetch(fetchURL, fetchOptions)
    return response
  } catch (err) {
    if (err.name === 'AbortError') {
      console.error('Request timed out')
    } else {
      console.error('Request failed', err)
    }
    return response
  } finally {
    clearTimeout(timeoutId)
  }
}

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
    const res = await fetchTimeout(url, {}, 10000)
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
  weather.value.id = 0
  foundLocations.value = []
  foundPOIs.value = []

  try {
    const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(
      q,
    )}&format=json&addressdetails=1&limit=5`
    const res = await fetchTimeout(
      url,
      {
        headers: {
          'User-Agent': userAgent,
          'Accept-Language': 'en',
        },
      },
      10000,
    )
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
  weather.value.id = 0
  foundPOIs.value = []
  // temporary selected location
  foundLocations.value = [{ lat, lon, display_name: 'Selected location' }]

  // optional: reverse geocode to get a nicer display name
  try {
    const revUrl = `https://nominatim.openstreetmap.org/reverse?lat=${encodeURIComponent(
      lat,
    )}&lon=${encodeURIComponent(lon)}&format=json`
    const revRes = await fetch(revUrl, { headers: { 'User-Agent': userAgent } })
    if (revRes.ok) {
      const revData = await revRes.json()
      if (revData?.display_name) {
        foundLocations.value = [{ lat, lon, display_name: revData.display_name }]
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

  let overpassResponse = await fetchTimeout(
    'https://overpass-api.de/api/interpreter',
    {
      method: 'POST',
      body: overpassQuery,
      headers: {
        'User-Agent': userAgent,
      },
    },
    10000,
  )
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
