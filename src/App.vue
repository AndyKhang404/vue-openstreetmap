<template>
  <h1>vue-openstreetmap</h1>
  <p>Search for nearest 5 (at most) points of interest</p>
  <form @submit.prevent="searchLocation">
    <input type="text" name="location-input" id="location-input" required v-model="location" />
    <button type="submit">Search</button>
  </form>
  <LoaderComponent v-if="isSearching" />
  <section style="width: 100%; margin-top: 16px">
    <h2 style="margin: 0 0 8px 0">Locations</h2>
    <div
      style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 12px;
        width: 100%;
      "
    >
      <span v-if="foundLocations.length === 0 && !isSearching">No locations found</span>
      <LoaderComponent v-if="foundLocations.length === 0 && isSearching" />
      <div
        style="background: #f6f8fa; border: 1px solid #e1e4e8; padding: 12px; border-radius: 6px"
        v-for="foundLocation in foundLocations"
        :key="foundLocation.place_id"
      >
        <h3>{{ foundLocation.display_name }}</h3>
        <span>type: {{ foundLocation.class }}</span
        ><br />
        <span>latlon: {{ foundLocation.lat }}, {{ foundLocation.lon }}</span>
      </div>
    </div>
  </section>

  <section style="width: 100%; margin-top: 20px">
    <h2 style="margin: 0 0 8px 0">Points of interest</h2>
    <div
      style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 12px;
        width: 100%;
      "
    >
      <span v-if="foundPOIs.length === 0 && !isSearching">No POIs found</span>
      <LoaderComponent v-if="foundPOIs.length === 0 && isSearching" />
      <div
        style="background: #f6f8fa; border: 1px solid #e1e4e8; padding: 12px; border-radius: 6px"
        v-for="foundPOI in foundPOIs"
        :key="foundPOI.id"
      >
        <h3>{{ foundPOI.name }}</h3>
        <span>type: {{ foundPOI.type }}</span
        ><br />
        <span>latlon: {{ foundPOI.lat }}, {{ foundPOI.lon }}</span>
      </div>
    </div>
  </section>
  <MapComponent class="map" v-if="!isSearching" :locations="foundLocations" :pois="foundPOIs" />
</template>

<script setup>
import LoaderComponent from './components/LoaderComponent.vue'
import MapComponent from './components/MapComponent.vue'
import { ref } from 'vue'
const userAgent = 'vue-openstreetmap/1.0 (Contact: andykhang404@gmail.com)'

const location = ref('')
const isSearching = ref(false)
const foundLocations = ref([])
const foundPOIs = ref([])

const searchLocation = async () => {
  if (isSearching.value) return
  isSearching.value = true
  foundLocations.value = []

  const query = location.value.trim()
  if (!query) return

  location.value = ''
  console.log('Searching for', query)

  // Use Nominatim API to search for address' coordinates
  const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&addressdetails=1`
  const response = await fetch(url, {
    headers: {
      'User-Agent': userAgent,
      'Accept-Language': ['en', 'vi'],
    },
  })

  if (!response.ok) {
    console.error('Nominatim API error', response.status)
    isSearching.value = false
    return
  }

  const data = await response.json()
  foundLocations.value = Array.isArray(data)
    ? data
        .filter((location) => location.lat !== undefined && location.lon !== undefined)
        .slice(0, 5)
    : []

  if (foundLocations.value.length !== 0) {
    await searchPOIs(foundLocations.value[0].lat, foundLocations.value[0].lon)
  }
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
  const radius = 1000 // Search within 3km
  const overpassQuery = `
        [out:json];
        (
          nwr["building"~"religious|public|museum"](around:${radius},${latitude},${longitude});
          nwr["tourism"~"museum|information|attraction|theme_park|gallery|zoo"](around:${radius},${latitude},${longitude});
          nwr["historic"](around:${radius},${latitude},${longitude});
          nwr["leisure"](around:${radius},${latitude},${longitude});
          nwr["amenity"~"restaurant|cafe|bar"](around:${radius},${latitude},${longitude});
        );
        out body 50;
      `

  const overpassResponse = await fetch('https://overpass-api.de/api/interpreter', {
    method: 'POST',
    body: overpassQuery,
    headers: {
      'User-Agent': userAgent,
    },
  })
  if (!overpassResponse.ok) {
    console.error('Overpass API error', overpassResponse.status)
    return
  }
  const overpassData = await overpassResponse.json()

  // Process and sort POIs by distance
  const poisWithDistance = (overpassData.elements || [])
    .filter((element) => element.tags?.name || element.tags?.amenity || element.tags?.shop)
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

<style scoped>
.map {
  padding-top: 10px;
}
</style>
