import { useState, useRef, useEffect } from 'react'
import { Send, MessageSquare, AlertCircle, Loader2 } from 'lucide-react'
import api from '../api/axiosConfig'

export default function StudentChatPanel({ studentData, shapFeatures }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isOnline, setIsOnline] = useState(null)
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)

  // Initialize chat with system context when component mounts
  useEffect(() => {
    initializeChat()
    checkOllamaStatus()
  }, [studentData, shapFeatures])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const checkOllamaStatus = async () => {
    try {
      const response = await api.get('/chat/status')
      setIsOnline(response.data.ollama_available)
    } catch (err) {
      setIsOnline(false)
    }
  }

  const initializeChat = () => {
    if (!studentData) return

    const systemContext = {
      risk_score: studentData.risk_score || 0,
      risk_level: studentData.risk_level || 'Unknown',
      shap_features: shapFeatures || []
    }

    // Add initial system message (not displayed in UI)
    const initialMessages = [
      {
        role: 'system',
        content: `You are a student counselor assistant. The student has a dropout risk score of ${systemContext.risk_score}%. Their risk level is ${systemContext.risk_level}. Their high-risk features are: ${systemContext.shap_features.join(', ')}. Answer questions about why this student is at risk and suggest interventions.`
      }
    ]

    setMessages(initialMessages)
  }

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setError(null)

    // Add user message to conversation
    const newMessages = [...messages, { role: 'user', content: userMessage }]
    setMessages(newMessages)
    setIsLoading(true)

    try {
      const systemContext = {
        risk_score: studentData?.risk_score || 0,
        risk_level: studentData?.risk_level || 'Unknown',
        shap_features: shapFeatures || []
      }

      const response = await api.post('/chat', {
        message: userMessage,
        messages: newMessages,
        role: 'student',
        system_context: systemContext
      })

      // Add assistant response
      setMessages([...newMessages, { role: 'assistant', content: response.data.response }])
      
      // Update online status
      setIsOnline(response.data.using_ollama)
    } catch (err) {
      setError('Failed to get AI response. Please try again.')
      console.error('Chat error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  if (!studentData) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        Select a student to start chatting
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-gray-900">AI Counselor Assistant</h3>
        </div>
        <div className="flex items-center gap-2">
          {isOnline === null ? (
            <div className="flex items-center gap-1 text-gray-400 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" />
              Checking...
            </div>
          ) : isOnline ? (
            <span className="flex items-center gap-1 text-green-600 text-sm">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              Online
            </span>
          ) : (
            <span className="flex items-center gap-1 text-yellow-600 text-sm">
              <AlertCircle className="w-4 h-4" />
              Offline
            </span>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 1 && (
          <div className="text-center text-gray-500 text-sm py-8">
            <MessageSquare className="w-12 h-12 mx-auto mb-2 text-gray-300" />
            <p>Ask me about this student's risk factors and intervention strategies</p>
          </div>
        )}

        {messages.slice(1).map((msg, index) => (
          <div
            key={index}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <div className="flex items-center gap-2 text-gray-600 text-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
                Thinking...
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="flex justify-center">
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-2">
              <div className="flex items-center gap-2 text-red-600 text-sm">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about this student's risk factors..."
            className="flex-1 resize-none border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || isLoading}
            className="bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        {!isOnline && isOnline !== null && (
          <p className="text-xs text-yellow-600 mt-2">
            AI assistant is using offline mode. Start Ollama for full AI capabilities.
          </p>
        )}
      </div>
    </div>
  )
}
