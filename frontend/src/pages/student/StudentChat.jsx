import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '../../api/axiosConfig'
import { Send, Bot, User, Clock, AlertCircle, PaperPlane } from 'lucide-react'

export default function StudentChat() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [ollamaStatus, setOllamaStatus] = useState('unknown')
  const [studentData, setStudentData] = useState(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Fetch student data for context
  useEffect(() => {
    const fetchStudentData = async () => {
      try {
        const response = await api.get('/predict/me')
        setStudentData(response.data)
      } catch (err) {
        console.error('Failed to fetch student data:', err)
        // Set mock data if API fails
        setStudentData({
          risk_score: 55,
          subjects: {
            physics: { score: 62 },
            chemistry: { score: 58 },
            mathematics: { score: 71 }
          },
          wellness: {
            stress_level: 7,
            sleep_hours: 5.5
          }
        })
      }
    }
    fetchStudentData()
  }, [])

  // Check Ollama status
  const checkOllamaStatus = useCallback(async () => {
    try {
      const response = await api.get('/chat/status')
      if (response.data.ollama_available) {
        setOllamaStatus('online')
      } else {
        setOllamaStatus('offline')
      }
    } catch (err) {
      setOllamaStatus('offline')
    }
  }, [])

  useEffect(() => {
    checkOllamaStatus()
    const interval = setInterval(checkOllamaStatus, 30000)
    return () => clearInterval(interval)
  }, [checkOllamaStatus])

  const quickActions = [
    'Improve my Chemistry score',
    'Make a revision plan',
    'I\'m feeling burned out',
    'Analyze my mock test'
  ]

  const handleSendMessage = async (content) => {
    if (!content.trim() || loading) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    // Prepare system context with student data
    const systemContext = studentData ? {
      risk_score: studentData.risk_score,
      risk_level: studentData.risk_level,
      subject_scores: studentData.subjects,
      stress_level: studentData.wellness?.stress_level,
      sleep_hours: studentData.wellness?.sleep_hours
    } : null

    try {
      // Use streaming endpoint
      const response = await fetch(`${api.defaults.baseURL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          messages: messages.map(m => ({ role: m.role, content: m.content })),
          role: 'student',
          system_context: systemContext
        })
      })

      if (!response.ok) {
        throw new Error('Failed to connect to chat service')
      }

      // Create assistant message for streaming
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: '',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])

      // Read stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let accumulatedContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.error) {
                accumulatedContent += `[Error: ${data.error}]`
              } else if (data.content) {
                accumulatedContent += data.content
                setMessages(prev => {
                  const updated = [...prev]
                  updated[updated.length - 1].content = accumulatedContent
                  return updated
                })
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }

    } catch (err) {
      console.error('Chat error:', err)
      setOllamaStatus('offline')
      
      // Fallback response
      const fallbackResponse = getFallbackResponse(content)
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: fallbackResponse,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
    } finally {
      setLoading(false)
    }
  }

  const getFallbackResponse = (query) => {
    const lowerQuery = query.toLowerCase()
    
    if (lowerQuery.includes('chemistry') && (lowerQuery.includes('improve') || lowerQuery.includes('optimize'))) {
      return `To improve your Chemistry score:\n\n**1. Focus on NCERT First**\n- Master all NCERT concepts and examples\n- 80% of JEE Chemistry comes from NCERT\n\n**2. Organic Chemistry Strategy**\n- Learn reaction mechanisms, don't memorize\n- Practice named reactions daily\n\nWould you like a specific study plan?`
    }
    
    if (lowerQuery.includes('revision') || lowerQuery.includes('plan')) {
      return `Here's a revision plan:\n\n**Week 1-2: Basics**\n- Focus on weak topics\n- Daily practice problems\n\n**Week 3-4: Advanced**\n- Previous year questions\n- Mock test analysis\n\nShall I customize this for your current level?`
    }
    
    if (lowerQuery.includes('burnout') || lowerQuery.includes('stress')) {
      return `Managing burnout is crucial:\n\n**1. Take breaks**\n- Use Pomodoro technique (25 min study, 5 min break)\n- Get 7-8 hours of sleep\n\n**2. Stay balanced**\n- Light exercise daily\n- Talk to friends/family\n\n**3. Adjust expectations**\n- Set realistic goals\n- Celebrate small wins\n\nYou're doing great - just pace yourself!`
    }
    
    if (lowerQuery.includes('mock') || lowerQuery.includes('analyze')) {
      return `Mock test analysis:\n\n**Key Areas to Review:**\n- Identify weak topics from recent tests\n- Focus on high-weightage chapters\n- Practice time management\n\n**Next Steps:**\n- Solve 20+ problems per weak topic\n- Review mistakes thoroughly\n- Track improvement over time\n\nWould you like subject-specific tips?`
    }
    
    return `I understand you're asking about "${query}". While I'm currently in offline mode, I can help with:\n\n- Chemistry optimization\n- Revision planning\n- Stress management\n- Mock test analysis\n\nTry asking about any of these topics!`
  }

  const handleQuickAction = (action) => {
    handleSendMessage(action)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    handleSendMessage(input)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage(input)
    }
  }

  const LinkRenderer = ({ href, children }) => {
    if (href?.startsWith('/')) {
      return (
        <button
          onClick={() => navigate(href)}
          className="text-[#6B5CE7] hover:text-[#5A4BD1] font-semibold underline"
        >
          {children}
        </button>
      )
    }
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className="text-[#6B5CE7] hover:text-[#5A4BD1] font-semibold underline">
        {children}
      </a>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-[#F8F9FC]">
      {/* Fixed Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#6B5CE7] rounded-full flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">AI Academic Counselor</h1>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${ollamaStatus === 'online' ? 'bg-emerald-500' : ollamaStatus === 'offline' ? 'bg-red-500' : 'bg-gray-400'}`} />
                <span className="text-xs text-gray-500">
                  {ollamaStatus === 'online' ? 'Online' : ollamaStatus === 'offline' ? 'Offline' : 'Connecting...'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Ollama Unreachable Banner */}
      {ollamaStatus === 'offline' && (
        <div className="bg-amber-50 border-b border-amber-200 px-6 py-3 flex-shrink-0">
          <div className="max-w-4xl mx-auto flex items-center gap-2 text-amber-800">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">Start Ollama to enable AI: run <code className="bg-amber-100 px-2 py-0.5 rounded">ollama serve</code> in terminal</span>
          </div>
        </div>
      )}

      {/* Scrollable Message Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 ? (
            /* Empty State with Greeting */
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-[#6B5CE7] rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Bot className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Hi! I'm your JEE prep assistant.
              </h2>
              <p className="text-gray-500 mb-8">What do you need help with today?</p>
              
              {/* Quick Action Chips */}
              <div className="flex flex-wrap justify-center gap-3">
                {quickActions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickAction(action)}
                    className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-colors shadow-sm"
                  >
                    {action}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Messages */
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-2xl rounded-2xl px-5 py-4 ${
                    message.role === 'user'
                      ? 'bg-[#6B5CE7] text-white'
                      : 'bg-white text-gray-900 shadow-sm border border-gray-100'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {message.role === 'assistant' && (
                      <div className="w-6 h-6 bg-[#6B5CE7] rounded-full flex items-center justify-center shrink-0 mt-0.5">
                        <Bot className="w-3.5 h-3.5 text-white" />
                      </div>
                    )}
                    <div className="flex-1">
                      {message.role === 'assistant' ? (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            a: LinkRenderer,
                            strong: ({ children }) => <span className="font-semibold">{children}</span>,
                            ul: ({ children }) => <ul className="space-y-1.5 my-2">{children}</ul>,
                            li: ({ children }) => <li className="flex items-start gap-2"><span className="text-[#6B5CE7] mt-1.5">•</span><span className="leading-relaxed">{children}</span></li>,
                            p: ({ children }) => <p className="leading-relaxed mb-2 last:mb-0">{children}</p>
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <p className="text-sm whitespace-pre-wrap leading-relaxed">
                          {message.content}
                        </p>
                      )}
                      <p className="text-xs mt-3 opacity-60 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                    {message.role === 'user' && (
                      <div className="w-6 h-6 bg-white rounded-full flex items-center justify-center shrink-0 mt-0.5">
                        <User className="w-3.5 h-3.5 text-[#6B5CE7]" />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}

          {/* Typing Indicator */}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white rounded-2xl px-5 py-4 shadow-sm border border-gray-100">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                  <span className="text-sm text-gray-500">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Fixed Bottom Input Bar */}
      <div className="bg-white border-t border-gray-200 px-6 py-4 flex-shrink-0">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              className="flex-1 px-5 py-3 rounded-full border border-gray-200 focus:border-[#6B5CE7] focus:ring-2 focus:ring-[#6B5CE7]/20 outline-none transition-all text-sm"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-[#6B5CE7] hover:bg-[#5A4BD1] disabled:bg-gray-300 text-white w-12 h-12 rounded-full flex items-center justify-center transition-colors flex-shrink-0"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <PaperPlane className="w-5 h-5" />
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
