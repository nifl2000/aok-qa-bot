import { useState, useRef, useEffect } from 'react'
import './App.css'

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
  score: number;
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
  const chatEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const handleSearch = async () => {
    if (!input.trim()) return

    const userQuery = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userQuery }])
    setLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userQuery, top_k: 3 })
      })

      if (!response.ok) throw new Error('API Fehler')

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
      setMessages(prev => [...prev, { role: 'bot', content: 'Entschuldigung, es gab ein technisches Problem bei der Suche.' }])
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
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Ihre Frage an die AOK..."
          disabled={loading}
        />
        <button onClick={handleSearch} disabled={loading || !input.trim()}>
          Senden
        </button>
      </div>
    </div>
  )
}

export default App
