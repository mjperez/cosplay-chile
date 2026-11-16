import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

afterEach(() => {
  cleanup()
  localStorage.clear()
  vi.unstubAllGlobals()
})

// jsdom no implementa scrollTo ni matchMedia
window.scrollTo = () => {}
window.matchMedia = window.matchMedia || ((q) => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {} }))
