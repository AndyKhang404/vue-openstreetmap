<template>
  <div class="map-container">
    <!-- emit 'select' with { lat, lon } when user clicks the map -->
    <l-map
      ref="map"
      v-model:zoom="zoom"
      :center="center"
      :use-global-leaflet="false"
      @click="onMapClick"
    >
      <l-tile-layer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        layer-type="base"
        name="OpenStreetMap"
      ></l-tile-layer>

      <!-- Locations: red markers -->
      <l-circle-marker
        v-for="(loc, idx) in normalizedLocations"
        :key="'loc-' + (loc.id ?? idx)"
        :lat-lng="[loc.lat, loc.lon]"
        :radius="8"
        color="red"
        fill-color="red"
        :fill-opacity="0.2"
      >
        <l-popup>
          <div>
            <strong>{{ loc.name || loc.display_name || 'Location' }}</strong
            ><br />
            <small>{{ loc.lat }}, {{ loc.lon }}</small>
          </div>
        </l-popup>
      </l-circle-marker>

      <!-- POIs: blue markers -->
      <l-circle-marker
        v-for="(poi, idx) in normalizedPOIs"
        :key="'poi-' + (poi.id ?? idx)"
        :lat-lng="[poi.lat, poi.lon]"
        :radius="6"
        color="blue"
        fill-color="blue"
        :fill-opacity="0.2"
      >
        <l-popup>
          <div>
            <strong>{{ poi.name || 'POI' }}</strong
            ><br />
            <small>{{ poi.lat }}, {{ poi.lon }}</small>
          </div>
        </l-popup>
      </l-circle-marker>
    </l-map>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

// 1. Import Leaflet CSS
import 'leaflet/dist/leaflet.css'

// 2. Import Vue-Leaflet components (add circle-marker and popup)
import { LMap, LTileLayer, LCircleMarker, LPopup } from '@vue-leaflet/vue-leaflet'

// Props: two lists
const props = defineProps({
  locations: {
    type: Array,
    default: () => [],
  },
  pois: {
    type: Array,
    default: () => [],
  },
})

// emit 'select-location' when map is clicked
const emit = defineEmits(['select-location'])
const onMapClick = (evt) => {
  const lat = evt?.latlng?.lat
  const lon = evt?.latlng?.lng
  if (lat != null && lon != null) {
    center.value = [lat, lon]
    emit('select-location', { lat, lon })
  }
}

// Map State (Reactive data)
// Default center set to (10.7755254,106.7021047)
const zoom = ref(13)
const center = ref([10.7755254, 106.7021047])
// The `l-map` component has a `ref` named 'map' for direct Leaflet instance access (optional)
const map = ref(null)

// Normalize data (ensure numeric lat/lon and consistent name fields)
const normalizedLocations = computed(() =>
  (props.locations || []).map((l) => ({
    id: l.id ?? l.place_id,
    name: l.display_name ?? l.name,
    lat: Number(l.lat),
    lon: Number(l.lon),
    raw: l,
  })),
)

const normalizedPOIs = computed(() =>
  (props.pois || []).map((p) => ({
    id: p.id,
    name: p.name,
    lat: Number(p.lat),
    lon: Number(p.lon),
    raw: p,
  })),
)

// When locations update, center map on the first location if available
watch(
  () => normalizedLocations.value,
  (newList) => {
    if (newList && newList.length > 0) {
      const first = newList[0]
      if (Number.isFinite(first.lat) && Number.isFinite(first.lon)) {
        center.value = [first.lat, first.lon]
      }
    }
  },
  { immediate: true },
)
</script>
