import { auth } from './firebase'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''

export const addBookmark = async (lat, lon, type, name) => {
  if (!auth.currentUser) {
    throw new Error('User not authenticated')
  }

  if (!BACKEND_URL) {
    throw new Error('Backend URL not configured')
  }

  const idToken = await auth.currentUser.getIdToken()

  const response = await fetch(`${BACKEND_URL}/api/v1/user/bookmarks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${idToken}`,
    },
    body: JSON.stringify({
      lat,
      lon,
      type,
      name,
    }),
  })

  if (!response.ok) {
    throw new Error(`Failed to save bookmark: ${response.status}`)
  }

  return await response.json()
}

export const getBookmarks = async () => {
  if (!auth.currentUser) {
    throw new Error('User not authenticated')
  }

  if (!BACKEND_URL) {
    throw new Error('Backend URL not configured')
  }

  const idToken = await auth.currentUser.getIdToken()

  const response = await fetch(`${BACKEND_URL}/api/v1/user/bookmarks`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${idToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to get bookmarks: ${response.status}`)
  }

  return await response.json()
}

export const deleteBookmark = async (bookmark_id) => {
  if (!auth.currentUser) {
    throw new Error('User not authenticated')
  }

  if (!BACKEND_URL) {
    throw new Error('Backend URL not configured')
  }

  const idToken = await auth.currentUser.getIdToken()

  const response = await fetch(`${BACKEND_URL}/api/v1/user/bookmarks/${bookmark_id}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${idToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to get bookmarks: ${response.status}`)
  }

  return await response.json()
}

export const getBookmarkCount = async () => {
  if (!auth.currentUser) {
    throw new Error('User not authenticated')
  }

  if (!BACKEND_URL) {
    throw new Error('Backend URL not configured')
  }

  const idToken = await auth.currentUser.getIdToken()

  const response = await fetch(`${BACKEND_URL}/api/v1/user/bookmarks/count`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${idToken}`,
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to get bookmark count: ${response.status}`)
  }

  const data = await response.json()
  return data.count
}
