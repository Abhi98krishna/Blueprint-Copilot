import { useEffect, useMemo, useRef, useState } from 'react'
import ResponseQualityLab from './ResponseQualityLab'

type MessageType = 'user' | 'ai' | 'system'

type Evidence = {
  title: string
  file_path: string
  line_range: string
}

type Message = {
  id: number
  type: MessageType
  content: string
  timestamp: string
  evidence?: Evidence[]
}

type ApiResponse = {
  session_id: string
  reply?: string
  draft_snapshot?: Record<string, unknown>
  step?: string
  evidence?: Evidence[]
}

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8001'

const ICONS: React.ReactNode[] = [
  (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 2.5 20 7v10l-8 4.5L4 17V7z" fill="#22A5F7" />
      <path d="M12 6.3 7.2 9v6l4.8 2.7 4.8-2.7V9z" fill="#ffffff" />
    </svg>
  ),
  (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="10" fill="#22A5F7" />
      <path d="M8 8h8v8H8z" fill="#ffffff" />
    </svg>
  ),
  (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="4" y="4" width="16" height="16" rx="6" fill="#22A5F7" />
      <path d="M8 12h8" stroke="#ffffff" strokeWidth="2" />
      <path d="M12 8v8" stroke="#ffffff" strokeWidth="2" />
    </svg>
  ),
]

const formatTimestamp = (date = new Date()) =>
  date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

const formatText = (text: string) =>
  text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br />')

const createMessage = (type: MessageType, content: string, evidence?: Evidence[]): Message => ({
  id: Date.now() + Math.floor(Math.random() * 1000),
  type,
  content,
  timestamp: formatTimestamp(),
  evidence,
})

export default function ChatPanel() {
  const icon = useMemo(() => ICONS[Math.floor(Math.random() * ICONS.length)], [])
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [error, setError] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [draftSnapshot, setDraftSnapshot] = useState<Record<string, unknown> | null>(null)
  const [step, setStep] = useState<string>('')
  const [isComplete, setIsComplete] = useState(false)
  const chatEndRef = useRef<HTMLDivElement | null>(null)
  const [labOpen, setLabOpen] = useState(false)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  useEffect(() => {
    const createSession = async () => {
      try {
        const response = await fetch(`${API_BASE}/session`, { method: 'POST' })
        const payload = (await response.json()) as ApiResponse
        setSessionId(payload.session_id)
        if (payload.reply) {
          setMessages([createMessage('ai', payload.reply, payload.evidence)])
        }
        if (payload.draft_snapshot) {
          setDraftSnapshot(payload.draft_snapshot)
        }
        if (payload.step) {
          setStep(payload.step)
          setIsComplete(payload.step === 'complete')
        }
      } catch (err) {
        setError('Unable to start a session. Please check the API server.')
      }
    }

    createSession()
  }, [])

  const handleSend = async () => {
    const trimmed = inputValue.trim()
    if (!trimmed) {
      setError('Please enter a message.')
      return
    }
    if (trimmed.length > 500) {
      setError('Message is too long (max 500 characters).')
      return
    }
    if (!sessionId) {
      setError('Session not ready yet.')
      return
    }

    setError('')
    setMessages((prev) => [...prev, createMessage('user', trimmed)])
    setInputValue('')
    setIsTyping(true)

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message: trimmed }),
      })
      const payload = (await response.json()) as ApiResponse
      if (payload.reply) {
        setMessages((prev) => [...prev, createMessage('ai', payload.reply, payload.evidence)])
      }
      if (payload.draft_snapshot) {
        setDraftSnapshot(payload.draft_snapshot)
      }
      if (payload.step) {
        setStep(payload.step)
        setIsComplete(payload.step === 'complete')
      }
    } catch (err) {
      setError('Failed to reach the API. Please try again.')
    } finally {
      setIsTyping(false)
    }
  }

  const handleReset = async () => {
    if (!sessionId) return
    setIsTyping(true)
    try {
      const response = await fetch(`${API_BASE}/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      })
      const payload = (await response.json()) as ApiResponse
      setMessages(payload.reply ? [createMessage('ai', payload.reply, payload.evidence)] : [])
      setDraftSnapshot(payload.draft_snapshot ?? null)
      setStep(payload.step ?? '')
      setIsComplete(payload.step === 'complete')
    } catch (err) {
      setError('Failed to reset the session.')
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <>
      <div className="chat-shell" role="application" aria-label="Blueprint copilot">
        <header className="chat-header" role="banner">
          <div className="chat-header-left">
            <div className="chat-icon" aria-hidden="true">
              {icon}
            </div>
            <div className="chat-title">
              <p className="chat-title-main">Copilot</p>
              <span className="chat-title-sub">Blueprint Assistant</span>
            </div>
          </div>
          <div className="chat-badges">
            <span className="badge" aria-label="Conversation mode">
              Guide
            </span>
            <span className="badge" aria-label="Status">
              {isComplete ? 'Ready' : 'Active'}
            </span>
          </div>
        </header>

      <main className="chat-body" role="log" aria-live="polite">
        {messages.map((message) => (
          <div key={message.id} className={`message-row ${message.type}`}>
            {message.type !== 'user' && (
              <div className="message-avatar" aria-hidden="true">
                <div className="message-avatar-inner">
                  {message.type === 'system' ? (
                    <span className="system-icon" aria-hidden="true">
                      ℹ️
                    </span>
                  ) : (
                    icon
                  )}
                </div>
              </div>
            )}
            <div className="message-content">
              <div
                className={`message-bubble ${message.type}`}
                dangerouslySetInnerHTML={{ __html: formatText(message.content) }}
              />
              <span className="message-timestamp">{message.timestamp}</span>
              {message.evidence && message.evidence.length > 0 && (
                <details className="evidence-details">
                  <summary className="evidence-summary">Evidence</summary>
                  <div className="evidence-list" role="list">
                    {message.evidence.map((item, index) => (
                      <div key={`${item.file_path}-${index}`} className="evidence-item" role="listitem">
                        <span className="evidence-title">{item.title}</span>
                        <span className="evidence-path">
                          {item.file_path}:{item.line_range}
                        </span>
                      </div>
                    ))}
                  </div>
                </details>
              )}
              {message.type === 'ai' && (
                <button
                  type="button"
                  className="compare-button"
                  onClick={() => setLabOpen(true)}
                  disabled={!messages.some((msg) => msg.type === 'user')}
                >
                  Compare responses
                </button>
              )}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="message-row ai">
            <div className="message-avatar" aria-hidden="true">
              <div className="message-avatar-inner">{icon}</div>
            </div>
            <div className="message-content">
              <div className="message-bubble ai">
                <span className="typing">Thinking...</span>
              </div>
            </div>
          </div>
        )}
        {isComplete && draftSnapshot && (
          <div className="summary-card" role="region" aria-label="Draft summary">
            <h3>Draft summary</h3>
            <pre>{JSON.stringify(draftSnapshot, null, 2)}</pre>
            <p>You can keep refining this draft.</p>
          </div>
        )}
        <div ref={chatEndRef} />
      </main>

        <footer className="chat-footer" role="contentinfo">
          {isComplete ? (
            <button type="button" className="reset-button" onClick={handleReset} aria-label="Start new task">
              ← Start New Task
            </button>
          ) : (
            <div className="input-row">
              <input
                type="text"
                placeholder="Ask me anything about blueprints..."
                value={inputValue}
                onChange={(event) => setInputValue(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    handleSend()
                  }
                }}
                disabled={isTyping || !sessionId}
                aria-label="Message input"
              />
              <button
                type="button"
                className="send-button"
                onClick={handleSend}
                disabled={isTyping || !sessionId}
                aria-label="Send message"
              >
                ➤
              </button>
            </div>
          )}
          {error && (
            <span className="input-error" role="alert">
              {error}
            </span>
          )}
          {step && !isComplete && (
            <span className="step-label" aria-label="Current step">
              Step: {step}
            </span>
          )}
        </footer>
      </div>
      <ResponseQualityLab
        open={labOpen}
        onClose={() => setLabOpen(false)}
        sessionId={sessionId}
        lastUserMessage={
          [...messages].reverse().find((msg) => msg.type === 'user')?.content ?? null
        }
      />
    </>
  )
}
