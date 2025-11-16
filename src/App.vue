<template>
  <div id="content">
    <header>
      <h1 style="font-size: 1.75rem">vue-openstreetmap</h1>
      <p v-if="foundLocations.length === 0 && !isSearching">Click on the map or search here</p>
    </header>

    <section id="location">
      <h2>Location</h2>
      <div>
        <span v-if="foundLocations.length === 0 && !isSearching">No locations found</span>
        <LoaderComponent v-if="foundLocations.length === 0 && isSearching" />
        <div
          style="background: #f6f8fa; border: 1px solid #e1e4e8; padding: 12px; border-radius: 6px"
          v-for="foundLocation in foundLocations"
          :key="
            foundLocation.place_id ||
            foundLocation.id ||
            foundLocation.lat + '-' + foundLocation.lon
          "
        >
          <h3 class="clamp-row">
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
          style="background: #f6f8fa; border: 1px solid #e1e4e8; padding: 12px; border-radius: 6px"
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
import { ref } from 'vue'
const userAgent = 'vue-openstreetmap/1.0 (Contact: andykhang404@gmail.com)'

const isSearching = ref(false)
const foundLocations = ref([])
const foundPOIs = ref([])

// When user clicks on the map, set a single foundLocation and fetch POIs
const onMapSelect = async ({ lat, lon }) => {
  if (isSearching.value) return
  isSearching.value = true
  foundPOIs.value = []
  // temporary selected location
  foundLocations.value = [{ lat, lon, display_name: 'Selected location' }]

  // optional: reverse geocode to get a nicer display name
  try {
    const revUrl = `https://nominatim.openstreetmap.org/reverse?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(
      lon,
    )}&format=json`
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

// fetch request with timeout
const fetchTimeout = async (fetchURL, fetchObj, timeout, defaultResponse) => {
  if (Object.hasOwn(fetchObj, 'signal')) {
    console.warn('Fetch object has another signal! Abort fetchTimeout...')
    return defaultResponse
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
  } catch (err) {
    if (err.name === 'AbortError') {
      console.error('Request timed out')
    } else {
      console.error('Request failed', err)
    }
    return defaultResponse
  } finally {
    clearTimeout(timeoutId)
  }
  return response
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
    { ok: false, status: 'Failed' },
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
