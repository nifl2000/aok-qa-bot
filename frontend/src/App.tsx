import { useState, useRef, useEffect } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_PASSWORD = import.meta.env.VITE_API_PASSWORD || 'aok2026'

interface Answer {
  kanal: string;
  antwort: string;
}

interface FAQResult {
  id: number;
  frage: string;
  hauptthema: string;
  subthema: string;
  answers: Answer[];
}

interface Message {
  role: 'user' | 'bot';
  content: string;
  results?: FAQResult[];
}

function FAQItem({ result }: { result: FAQResult }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="result-card">
      <div className="result-header" onClick={() => setIsExpanded(!isExpanded)}>
        <span className="expand-icon">{isExpanded ? '−' : '+'}</span>
        <div className="topic">{result.hauptthema}</div>
        <h4>{result.frage}</h4>
      </div>
      {isExpanded && (
        <div className="result-content">
          {result.answers.map((ans, idx) => (
            <div key={idx} style={{ marginBottom: '10px' }}>
              <strong>Kanal: {ans.kanal}</strong>
              <div style={{ marginTop: '5px' }}>{ans.antwort}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([
    { role: 'bot', content: 'Guten Tag! Ich bin Ihr AOK Wissensportal-Assistent. Wie kann ich Ihnen heute helfen?' }
  ])
  const [loading, setLoading] = useState(false)
  const [serverReady, setServerReady] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  useEffect(() => {
    fetch(`${API_URL}/api/ready`)
      .then(r => r.json())
      .then(() => setServerReady(true))
      .catch(() => setServerReady(false))
  }, [])

  const handleSearch = async () => {
    if (!input.trim() || !serverReady) return

    const userQuery = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userQuery }])
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/api/v1/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Password': API_PASSWORD },
        body: JSON.stringify({ query: userQuery, top_k: 3 })
      })

      if (!response.ok) {
        if (response.status === 401) throw new Error('Zugriff verweigert')
        if (response.status === 503) throw new Error('Server noch nicht bereit')
        throw new Error('API Fehler')
      }

      const data = await response.json()

      const botMessage: Message = {
        role: 'bot',
        content: data.results.length > 0
          ? `Ich habe folgende Informationen zu "${userQuery}" gefunden:`
          : 'Leider konnte ich zu Ihrer Anfrage keine passenden Informationen finden.',
        results: data.results
      }

      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Unbekannter Fehler'
      setMessages(prev => [...prev, { role: 'bot', content: `Entschuldigung, es gab ein technisches Problem: ${msg}` }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-container">
      <header>
        <h1>AOK Wissensportal</h1>
        <span>Sachsen-Anhalt</span>
      </header>

      <div className="chat-window">
        {!serverReady && (
          <div className="message bot loading">Server startet...</div>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.content}
            {msg.results && msg.results.map(res => (
              <FAQItem key={res.id} result={res} />
            ))}
          </div>
        ))}
        {loading && <div className="message bot loading">Bot schreibt...</div>}
        <div ref={chatEndRef} />
      </div>

      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder={serverReady ? "Ihre Frage an die AOK..." : "Server startet..."}
          disabled={loading || !serverReady}
        />
        <button onClick={handleSearch} disabled={loading || !input.trim() || !serverReady}>
          Senden
        </button>
      </div>
    </div>
  )
}

export default App
