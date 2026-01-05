import { useEffect, useMemo, useRef, useState } from 'react'

type MessageType = 'user' | 'ai' | 'system'

type Option = {
  id: string
  label: string
  description: string
  recommended?: boolean
  icon?: React.ReactNode
}

type MultiSelectData = {
  options: Option[]
  selected: string[]
  maxSelections: number
}

type Message = {
  id: number
  type: MessageType
  content: string
  timestamp: string
  options?: Option[]
  showOptions?: boolean
  multiSelectData?: MultiSelectData
}

const PROMPTS = [
  'What kind of application is this blueprint for?',
  'List the main components/services (comma-separated).',
  'Any dependencies between components? (comma-separated, e.g. web->db)',
  'What runtime inputs/variables should users provide? (comma-separated)',
  'Any day-2 actions to support? (comma-separated)',
  'Target environment label (e.g., AHV, ESXi, AWS)?',
]

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

const FAQ_OPTIONS: Option[] = [
  {
    id: 'package-service',
    label: "What's the difference between a package and service?",
    description: 'Understand where packages attach and when services run.',
    recommended: true,
  },
  {
    id: 'post-deploy',
    label: 'How do I add post-deployment actions?',
    description: 'Learn where day-2 actions live and how they are wired.',
  },
  {
    id: 'reuse-scripts',
    label: 'Can I reuse a script across blueprints?',
    description: 'Share tasks or artifacts without duplicating scripts.',
  },
  {
    id: 'failure',
    label: 'What happens if my blueprint fails mid-deployment?',
    description: 'Explore error handling and retry strategies.',
  },
  {
    id: 'minimal',
    label: 'What is the structure of a minimal valid blueprint?',
    description: 'Start with the minimal service, package, and profile layout.',
  },
]

const APP_OPTIONS: Option[] = [
  { id: 'lamp', label: 'LAMP Stack', description: 'Apache + MySQL + PHP stack', recommended: true },
  { id: 'nginx', label: 'Nginx + PHP', description: 'Web tier with PHP runtime' },
  { id: 'postgres', label: 'Postgres Service', description: 'Database-only blueprint' },
  { id: 'custom', label: 'Custom App', description: 'Bring your own service mix' },
]

const MULTI_SELECT_OPTIONS: Option[] = [
  { id: 'web', label: 'Web Tier', description: 'Frontend or API layer' },
  { id: 'db', label: 'Database', description: 'Relational or NoSQL data store' },
  { id: 'cache', label: 'Cache', description: 'Redis or Memcached' },
  { id: 'queue', label: 'Queue', description: 'Background job processor' },
  { id: 'search', label: 'Search', description: 'Search index service' },
  { id: 'monitoring', label: 'Monitoring', description: 'Telemetry and alerts' },
]

const formatTimestamp = (date = new Date()) =>
  date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

const formatText = (text: string) =>
  text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br />')

const createMessage = (type: MessageType, content: string): Message => ({
  id: Date.now() + Math.floor(Math.random() * 1000),
  type,
  content,
  timestamp: formatTimestamp(),
})

export default function ChatPanel() {
  const icon = useMemo(() => ICONS[Math.floor(Math.random() * ICONS.length)], [])
  const [messages, setMessages] = useState<Message[]>([
    createMessage('ai', "Guide mode: let's draft a blueprint-like spec."),
    createMessage('ai', PROMPTS[0]),
    { ...createMessage('ai', 'Try one of these common questions:'), options: FAQ_OPTIONS, showOptions: true },
  ])
  const [inputValue, setInputValue] = useState('')
  const [error, setError] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [step, setStep] = useState(0)
  const [isComplete, setIsComplete] = useState(false)
  const chatEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  useEffect(() => {
    if (!isTyping) return
    const timer = setTimeout(() => {
      setMessages((prev) => {
        const updated = [...prev]
        if (step === 0) {
          updated.push({
            ...createMessage('ai', 'Here are a few starting points you can pick from:'),
            options: APP_OPTIONS,
            showOptions: true,
          })
        } else if (step === 1) {
          updated.push({
            ...createMessage('ai', 'Select up to 5 application components to include:'),
            multiSelectData: {
              options: MULTI_SELECT_OPTIONS,
              selected: [],
              maxSelections: 5,
            },
          })
        } else if (step < PROMPTS.length) {
          updated.push(createMessage('ai', `Got it. ${PROMPTS[step]}`))
        }

        if (step >= PROMPTS.length - 1) {
          updated.push({
            ...createMessage('system', 'Blueprint summary ready. Your draft is complete.'),
          })
          setIsComplete(true)
        }
        return updated
      })
      setIsTyping(false)
    }, 1500)

    return () => clearTimeout(timer)
  }, [isTyping, step])

  const handleSend = () => {
    const trimmed = inputValue.trim()
    if (!trimmed) {
      setError('Please enter a message.')
      return
    }
    if (trimmed.length > 500) {
      setError('Message is too long (max 500 characters).')
      return
    }
    setError('')
    setMessages((prev) => [...prev, createMessage('user', trimmed)])
    setInputValue('')
    setIsTyping(true)
    setStep((prev) => Math.min(prev + 1, PROMPTS.length - 1))
  }

  const handleOptionSelect = (option: Option, messageId: number) => {
    setMessages((prev) =>
      prev.map((message) =>
        message.id === messageId ? { ...message, showOptions: false } : message,
      ),
    )
    const content = `${option.label}\n${option.description}`
    setMessages((prev) => [...prev, createMessage('user', content)])
    setIsTyping(true)
    setStep((prev) => Math.min(prev + 1, PROMPTS.length - 1))
  }

  const handleMultiSelect = (messageId: number, optionId: string) => {
    setMessages((prev) =>
      prev.map((message) => {
        if (message.id !== messageId || !message.multiSelectData) return message
        const { selected, maxSelections } = message.multiSelectData
        const isSelected = selected.includes(optionId)
        let nextSelected = selected
        if (isSelected) {
          nextSelected = selected.filter((id) => id !== optionId)
        } else if (selected.length < maxSelections) {
          nextSelected = [...selected, optionId]
        }
        return {
          ...message,
          multiSelectData: {
            ...message.multiSelectData,
            selected: nextSelected,
          },
        }
      }),
    )
  }

  const handleMultiSelectConfirm = (messageId: number) => {
    const message = messages.find((item) => item.id === messageId)
    if (!message?.multiSelectData) return
    if (message.multiSelectData.selected.length === 0) {
      setError('Select at least one component.')
      return
    }
    setError('')
    const labels = message.multiSelectData.options
      .filter((option) => message.multiSelectData?.selected.includes(option.id))
      .map((option) => `${option.label}\n${option.description}`)
      .join('\n\n')
    setMessages((prev) => [...prev, createMessage('user', labels)])
    setIsTyping(true)
    setStep((prev) => Math.min(prev + 1, PROMPTS.length - 1))
  }

  const handleBack = () => {
    if (step === 0 || isTyping) return
    setMessages((prev) => {
      const lastUserIndex = [...prev].reverse().findIndex((msg) => msg.type === 'user')
      if (lastUserIndex === -1) return prev
      const cutIndex = prev.length - lastUserIndex - 1
      return prev.slice(0, cutIndex)
    })
    setStep((prev) => Math.max(prev - 1, 0))
    setIsComplete(false)
    setError('')
  }

  return (
    <div className="chat-shell" role="application" aria-label="Blueprint copilot">
      <header className="chat-header" role="banner">
        <div className="chat-header-left">
          {step > 0 && !isComplete && (
            <button
              type="button"
              className="back-button"
              onClick={handleBack}
              aria-label="Go back"
            >
              ←
            </button>
          )}
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
            Active
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
                    <span className="system-icon" aria-hidden="true">ℹ️</span>
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
              {message.options && message.showOptions && (
                <div className="options-grid" role="group" aria-label="Recommended options">
                  {message.options.map((option) => (
                    <button
                      key={option.id}
                      className={`option-button ${option.recommended ? 'recommended' : ''}`}
                      onClick={() => handleOptionSelect(option, message.id)}
                      type="button"
                      aria-label={option.label}
                    >
                      <div className="option-content">
                        <div className="option-text">
                          <span className="option-label">{option.label}</span>
                          {option.recommended && <span className="option-badge">Recommended</span>}
                          <span className="option-description">{option.description}</span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
              {message.multiSelectData && (
                <div className="multi-select" role="group" aria-label="Multi select">
                  <button
                    type="button"
                    className="multi-select-trigger"
                    aria-expanded="true"
                  >
                    Select applications...
                  </button>
                  <div className="multi-select-menu" role="listbox">
                    {message.multiSelectData.options.map((option) => (
                      <label key={option.id} className="multi-select-item">
                        <input
                          type="checkbox"
                          checked={message.multiSelectData?.selected.includes(option.id)}
                          onChange={() => handleMultiSelect(message.id, option.id)}
                          disabled={
                            !message.multiSelectData?.selected.includes(option.id) &&
                            message.multiSelectData!.selected.length >=
                              message.multiSelectData!.maxSelections
                          }
                          aria-label={option.label}
                        />
                        <span>
                          <strong>{option.label}</strong>
                          <span className="multi-select-desc">{option.description}</span>
                        </span>
                      </label>
                    ))}
                  </div>
                  <button
                    type="button"
                    className="option-button recommended"
                    onClick={() => handleMultiSelectConfirm(message.id)}
                  >
                    Confirm selection
                  </button>
                </div>
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
        {isComplete && (
          <div className="summary-card" role="region" aria-label="Blueprint summary">
            <h3>Blueprint Summary</h3>
            <p>All guide steps are complete. Review your draft and start a new task.</p>
          </div>
        )}
        <div ref={chatEndRef} />
      </main>

      <footer className="chat-footer" role="contentinfo">
        {isComplete ? (
          <button type="button" className="reset-button" aria-label="Start new task">
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
              disabled={isTyping}
              aria-label="Message input"
            />
            <button
              type="button"
              className="send-button"
              onClick={handleSend}
              disabled={isTyping}
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
      </footer>
    </div>
  )
}
