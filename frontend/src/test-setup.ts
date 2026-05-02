import '@testing-library/jest-dom/vitest'
import { vi } from 'vitest'

// jsdom doesn't implement scrollIntoView
Element.prototype.scrollIntoView = vi.fn()
