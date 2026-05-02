import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from './App'

beforeEach(() => {
  global.fetch = vi.fn((url: string) => {
    if (url.includes('/api/ready')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'ready' }),
      } as Response)
    }
    return Promise.reject(new Error('Not mocked'))
  })
})

describe('App', () => {
  it('renders the greeting message', async () => {
    render(<App />)
    await waitFor(() => {
      expect(
        screen.getByText(/Guten Tag! Ich bin Ihr AOK Wissensportal-Assistent/)
      ).toBeInTheDocument()
    })
  })

  it('shows the header', () => {
    render(<App />)
    expect(screen.getByText('AOK Wissensportal')).toBeInTheDocument()
    expect(screen.getByText('Sachsen-Anhalt')).toBeInTheDocument()
  })

  it('shows a text input and send button', async () => {
    render(<App />)
    await waitFor(() => {
      const input = screen.getByPlaceholderText('Ihre Frage an die AOK...')
      expect(input).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'Senden' })).toBeInTheDocument()
  })
})
