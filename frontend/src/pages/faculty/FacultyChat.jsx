import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '../../api/axiosConfig'
import { MessageSquare, Send, Bot, User, Clock, AlertCircle, Users, BarChart3, FileText, Zap } from 'lucide-react'

export default function FacultyChat() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [usingFallback, setUsingFallback] = useState(false)
  const [ollamaStatus, setOllamaStatus] = useState('unknown') // 'unknown', 'online', 'offline'
  const [threads, setThreads] = useState([
    { id: 1, title: 'Student Performance', lastMessage: '1 hour ago' },
    { id: 2, title: 'Batch Analytics', lastMessage: 'Yesterday' },
    { id: 3, title: 'Parent Communications', lastMessage: '2 days ago' }
  ])
  const [activeThread, setActiveThread] = useState(1)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Check Ollama status on mount
  useEffect(() => {
    const checkOllamaStatus = async () => {
      try {
        const response = await api.get('/chat/status')
        console.log('Ollama status check:', response.data)
        if (response.data.ollama_available) {
          setOllamaStatus('online')
          setUsingFallback(false)
        } else {
          setOllamaStatus('offline')
          setUsingFallback(true)
        }
      } catch (err) {
        console.error('Ollama status check failed:', err)
        setOllamaStatus('offline')
        setUsingFallback(true)
      }
    }

    checkOllamaStatus()
  }, [])

  const quickActions = [
    'Draft a parent follow-up message for high-risk students',
    'Which topic has the lowest accuracy in Batch 1?',
    'Generate an assignment schedule to address weak Physics scores',
    'Show me students with declining attendance trends',
    'Compare performance across all batches'
  ]

  const handleSendMessage = async (content) => {
    if (!content.trim()) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      console.log('Sending message to backend:', content)
      const response = await api.post('/chat', {
        message: content,
        thread_id: activeThread,
        role: 'faculty'
      })
      
      console.log('Backend response:', response.data)
      
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, assistantMessage])
      
      // Update connection state based on response status
      if (response.data.status === 'offline') {
        console.log('Backend reported offline mode')
        setOllamaStatus('offline')
        setUsingFallback(true)
      } else if (response.data.status === 'online') {
        console.log('Backend reported online mode, model:', response.data.model_used)
        setOllamaStatus('online')
        setUsingFallback(false)
      }
    } catch (err) {
      console.error('Chat API Error Details:', err)
      console.error('Error response:', err.response)
      console.error('Error message:', err.message)
      
      // Only set to offline if it's a network error or 5xx server error
      if (err.code === 'ECONNREFUSED' || err.code === 'ERR_NETWORK' || 
          (err.response && err.response.status >= 500)) {
        console.log('Network error detected, setting offline mode')
        setOllamaStatus('offline')
        setUsingFallback(true)
      } else {
        console.log('Non-network error, keeping current status')
      }
      
      // Run offline fallback response
      const fallbackResponse = getOfflineResponse(content)
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

  const getOfflineResponse = (query) => {
    const lowerQuery = query.toLowerCase()
    
    // Faculty-specific offline responses
    if (lowerQuery.includes('parent') && (lowerQuery.includes('follow-up') || lowerQuery.includes('message'))) {
      return `Here's a draft parent follow-up message for high-risk students:\n\n---\n**Subject: Important Update Regarding Your Child's Progress**\n\nDear Parent,\n\nI hope this message finds you well. I wanted to reach out regarding [Student Name]'s recent performance and engagement patterns.\n\n**Current Observations:**\n- Mock test scores have shown a declining trend over the past 3 tests\n- Attendance has dropped to [X]% from [Y]% last month\n- Weekly wellness surveys indicate elevated stress levels\n\n**Recommended Actions:**\n1. Schedule a brief call to discuss support strategies\n2. Review study schedule and ensure adequate rest periods\n3. Consider additional support sessions for weak subjects\n\n**Our Commitment:**\nWe are closely monitoring [Student Name]'s progress and have implemented additional support measures. Please feel free to reach out with any concerns.\n\nBest regards,\n[Your Name]\nFaculty Counselor\n\n---\nWould you like me to customize this template for specific students or add additional details?`
    }
    
    if (lowerQuery.includes('topic') && (lowerQuery.includes('lowest') || lowerQuery.includes('accuracy') || lowerQuery.includes('weak'))) {
      return `Based on recent mock test analysis across all batches, here's the topic-wise performance breakdown:\n\n| Subject | Topic | Average Accuracy | Trend |\n|---------|-------|------------------|-------|\n| Physics | Electromagnetism | 42% | ↓ |\n| Physics | Thermodynamics | 58% | → |\n| Chemistry | Organic Chemistry | 38% | ↓ |\n| Chemistry | Physical Chemistry | 65% | ↑ |\n| Mathematics | Calculus | 52% | ↓ |\n| Mathematics | Coordinate Geometry | 71% | ↑ |\n\n**Key Findings:**\n- **Organic Chemistry** has the lowest accuracy at 38% across all batches\n- **Electromagnetism** in Physics shows consistent decline\n- **Coordinate Geometry** is performing well with upward trend\n\n**Recommendations:**\n1. Schedule remedial sessions for Organic Chemistry\n2. Review Electromagnetics teaching methodology\n3. Share Coordinate Geometry best practices across faculty\n\nWould you like detailed student-wise breakdown for any specific topic?`
    }
    
    if (lowerQuery.includes('assignment') && (lowerQuery.includes('schedule') || lowerQuery.includes('physics'))) {
      return `Here's a targeted assignment schedule to address weak Physics scores:\n\n**Week 1-2: Electromagnetism Foundation**\n- Day 1-2: Coulomb's Law & Electric Field (10 problems)\n- Day 3-4: Gauss's Law Applications (8 problems)\n- Day 5-6: Electric Potential & Capacitance (12 problems)\n- Day 7: Mixed practice + weekly test\n\n**Week 3-4: Current Electricity**\n- Day 8-10: Ohm's Law & Kirchhoff's Rules (15 problems)\n- Day 11-13: RC Circuits & Time Constants (10 problems)\n- Day 14: Full chapter test\n\n**Week 5-6: Magnetic Effects**\n- Day 15-17: Biot-Savart Law & Ampere's Law (12 problems)\n- Day 18-20: Magnetic Force on Moving Charges (10 problems)\n- Day 21: Electromagnetic Induction (15 problems)\n\n**Assignment Structure:**\n- **Daily**: 10-15 problems with increasing difficulty\n- **Weekly**: Comprehensive test covering all topics\n- **Bi-weekly**: One-on-one doubt clearing sessions\n\n**Tracking:**\n- Monitor completion rates through [Dashboard](/faculty)\n- Track improvement through subsequent mock tests\n- Adjust difficulty based on performance\n\nShall I create similar schedules for other weak subjects?`
    }
    
    if (lowerQuery.includes('attendance') && (lowerQuery.includes('declining') || lowerQuery.includes('trend'))) {
      return `Here's an analysis of students with declining attendance trends:\n\n| Student Name | Batch | Current Attendance | Previous Month | Change | Risk Level |\n|-------------|-------|-------------------|----------------|--------|------------|\n| Arjun Sharma | B1 Morning | 62% | 85% | -23% | High |\n| Priya Verma | B2 Evening | 58% | 78% | -20% | High |\n| Rohit Mishra | B1 Morning | 71% | 82% | -11% | Medium |\n| Ananya Singh | B3 Weekend | 45% | 65% | -20% | Critical |\n| Karan Gupta | B2 Evening | 68% | 75% | -7% | Medium |\n\n**Action Required:**\n\n**Immediate (This Week):**\n- Schedule one-on-one counseling with Critical & High risk students\n- Send attendance reminders to parents\n- Identify root causes (health, motivation, external factors)\n\n**Short-term (Next 2 Weeks):**\n- Implement attendance incentive program\n- Peer study groups for motivation\n- Flexible session timing where possible\n\n**Monitoring:**\n- Weekly attendance reports\n- Parent communication log\n- Impact on academic performance correlation\n\nWould you like me to draft specific intervention plans for any of these students?`
    }
    
    if (lowerQuery.includes('compare') && (lowerQuery.includes('batch') || lowerQuery.includes('performance'))) {
      return `Here's a comparative performance analysis across all batches:\n\n| Metric | B1 Morning | B2 Evening | B3 Weekend | Overall |\n|--------|------------|------------|------------|---------|\n| Average Mock Score | 185/360 | 172/360 | 195/360 | 184/360 |\n| Attendance Rate | 82% | 78% | 85% | 82% |\n| Assignment Completion | 75% | 68% | 82% | 75% |\n| High-Risk Students | 4 | 6 | 2 | 12 |\n| Improvement Trend | ↑ | → | ↑ | ↑ |\n\n**Key Insights:**\n\n**B1 Morning:**\n- Strong attendance but moderate scores\n- Needs focus on problem-solving techniques\n- 4 high-risk students require intervention\n\n**B2 Evening:**\n- Lowest performance across metrics\n- Highest number of high-risk students (6)\n- May need schedule review or additional support\n\n**B3 Weekend:**\n- Best performing batch overall\n- High engagement and completion rates\n- Model for best practices\n\n**Recommendations:**\n1. Share B3 teaching strategies with other batches\n2. Investigate B2 challenges (timing, faculty, content)\n3. Cross-batch study groups for peer learning\n\nWould you like detailed subject-wise comparison or student-level analysis?`
    }
    
    // Default fallback response
    return `I understand you're asking about "${query}". While I'm currently running in offline mode, I can still provide some faculty-focused guidance:\n\n**Available Capabilities:**\n- Draft parent communication templates\n- Analyze batch and topic-wise performance\n- Create targeted assignment schedules\n- Monitor attendance and engagement trends\n- Compare performance across batches\n\n**For Specific Help:**\n- Try asking about: parent follow-ups, topic accuracy, assignment schedules, attendance trends, or batch comparisons\n- I can provide detailed analysis and actionable recommendations\n\n**Note:** For real-time data and personalized insights, please use the [Faculty Dashboard](/faculty) or connect with the system administrator.\n\nIs there anything specific about faculty operations I can help you with?`
    }

  const handleQuickAction = (action) => {
    handleSendMessage(action)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    handleSendMessage(input)
  }

  // Custom link renderer for contextual navigation
  const LinkRenderer = ({ href, children }) => {
    if (href?.startsWith('/')) {
      return (
        <button
          onClick={() => navigate(href)}
          className="text-indigo-600 hover:text-indigo-700 font-semibold underline decoration-indigo-300 hover:decoration-indigo-400 underline-offset-2 transition-colors"
        >
          {children}
        </button>
      )
    }
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:text-indigo-700 font-semibold underline decoration-indigo-300 hover:decoration-indigo-400 underline-offset-2 transition-colors">
        {children}
      </a>
    )
  }

  // Empty state for faculty view
  if (messages.length === 0) {
    return (
      <div className="h-[calc(100vh-2rem)]">
        <div className="flex h-full bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
          {/* Thread Sidebar */}
          <div className="w-72 border-r border-slate-100 flex flex-col bg-slate-50">
            <div className="p-4 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Conversations
              </h2>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {threads.map(thread => (
                <button
                  key={thread.id}
                  onClick={() => setActiveThread(thread.id)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    activeThread === thread.id
                      ? 'bg-indigo-100 border border-indigo-200'
                      : 'hover:bg-slate-100 border border-transparent'
                  }`}
                >
                  <p className="text-sm font-medium text-slate-900">{thread.title}</p>
                  <p className="text-xs text-slate-500 mt-1">{thread.lastMessage}</p>
                </button>
              ))}
            </div>
            <div className="p-3 border-t border-slate-200">
              <button className="w-full text-sm font-medium text-indigo-600 hover:text-indigo-700 py-2 px-3 rounded-lg hover:bg-indigo-50 transition-colors">
                + New Conversation
              </button>
            </div>
          </div>

          {/* Empty State */}
          <div className="flex-1 flex flex-col">
            {/* Chat Header */}
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-600 rounded-full flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">AI Faculty Assistant</h3>
                  <p className="text-xs text-slate-500 flex items-center gap-1">
                    <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                    Online
                  </p>
                </div>
              </div>
              {usingFallback && (
                <div className="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 px-3 py-1.5 rounded-full">
                  <AlertCircle className="w-3 h-3" />
                  Offline Mode
                </div>
              )}
            </div>

            {/* Empty State Content */}
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="max-w-4xl w-full">
                <div className="text-center mb-8">
                  <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Bot className="w-8 h-8 text-emerald-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 mb-2">AI Faculty Assistant</h2>
                  <p className="text-slate-500">Your intelligent helper for student analytics, parent communications, and batch management</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Capabilities */}
                  <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
                    <div className="flex items-center gap-2 mb-3">
                      <Zap className="w-5 h-5 text-emerald-600" />
                      <h3 className="font-semibold text-slate-900">Capabilities</h3>
                    </div>
                    <ul className="space-y-2 text-sm text-slate-600">
                      <li className="flex items-start gap-2">
                        <span className="text-emerald-500 mt-0.5">•</span>
                        Draft parent communications
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-emerald-500 mt-0.5">•</span>
                        Analyze topic-wise accuracy
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-emerald-500 mt-0.5">•</span>
                        Create assignment schedules
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-emerald-500 mt-0.5">•</span>
                        Monitor attendance trends
                      </li>
                    </ul>
                  </div>

                  {/* Examples */}
                  <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
                    <div className="flex items-center gap-2 mb-3">
                      <FileText className="w-5 h-5 text-emerald-600" />
                      <h3 className="font-semibold text-slate-900">Examples</h3>
                    </div>
                    <ul className="space-y-2 text-sm text-slate-600">
                      <li className="flex items-start gap-2">
                        <span className="text-emerald-500 mt-0.5">•</span>
                        Parent follow-up templates
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-emerald-500 mt-0.5">•</span>
                        Batch performance comparison
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-emerald-500 mt-0.5">•</span>
                        Weak topic remediation plans
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-emerald-500 mt-0.5">•</span>
                        Attendance intervention strategies
                      </li>
                    </ul>
                  </div>

                  {/* System Limitations */}
                  <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
                    <div className="flex items-center gap-2 mb-3">
                      <BarChart3 className="w-5 h-5 text-amber-600" />
                      <h3 className="font-semibold text-slate-900">Data Sources</h3>
                    </div>
                    <ul className="space-y-2 text-sm text-slate-600">
                      <li className="flex items-start gap-2">
                        <span className="text-amber-500 mt-0.5">•</span>
                        Mock test results
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-amber-500 mt-0.5">•</span>
                        Attendance records
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-amber-500 mt-0.5">•</span>
                        Weekly survey data
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-amber-500 mt-0.5">•</span>
- Assignment completion rates
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="px-4 py-2 border-t border-slate-100">
              <div className="flex gap-2 overflow-x-auto pb-2">
                {quickActions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickAction(action)}
                    className="whitespace-nowrap text-xs font-medium text-emerald-600 bg-emerald-50 hover:bg-emerald-100 px-3 py-1.5 rounded-full transition-colors"
                  >
                    {action}
                  </button>
                ))}
              </div>
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-slate-100">
              <form onSubmit={handleSubmit} className="flex gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask me about student analytics, batch performance, or parent communications..."
                  className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 outline-none transition-all text-sm"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white px-4 py-3 rounded-xl transition-colors flex items-center gap-2"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Send
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-2rem)]">
      <div className="flex h-full bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
        {/* Thread Sidebar */}
        <div className="w-72 border-r border-slate-100 flex flex-col bg-slate-50">
          <div className="p-4 border-b border-slate-200">
            <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              Conversations
            </h2>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {threads.map(thread => (
              <button
                key={thread.id}
                onClick={() => setActiveThread(thread.id)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  activeThread === thread.id
                    ? 'bg-emerald-100 border border-emerald-200'
                    : 'hover:bg-slate-100 border border-transparent'
                }`}
              >
                <p className="text-sm font-medium text-slate-900">{thread.title}</p>
                <p className="text-xs text-slate-500 mt-1">{thread.lastMessage}</p>
              </button>
            ))}
          </div>
          <div className="p-3 border-t border-slate-200">
            <button className="w-full text-sm font-medium text-emerald-600 hover:text-emerald-700 py-2 px-3 rounded-lg hover:bg-emerald-50 transition-colors">
              + New Conversation
            </button>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Chat Header */}
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-600 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">AI Faculty Assistant</h3>
                <p className="text-xs text-slate-500 flex items-center gap-1">
                  <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                  Online
                </p>
              </div>
            </div>
            {ollamaStatus === 'offline' || usingFallback ? (
              <div className="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 px-3 py-1.5 rounded-full">
                <AlertCircle className="w-3 h-3" />
                Offline Mode
              </div>
            ) : ollamaStatus === 'online' ? (
              <div className="flex items-center gap-2 text-xs text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-full">
                <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                AI Online (Ollama)
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-100 px-3 py-1.5 rounded-full">
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-pulse"></span>
                Checking...
              </div>
            )}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map(message => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-2xl rounded-2xl px-5 py-4 ${
                    message.role === 'user'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-slate-50/80 text-slate-900 border border-slate-200'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {message.role === 'assistant' && (
                      <div className="w-6 h-6 bg-emerald-600 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                        <Bot className="w-3.5 h-3.5 text-white" />
                      </div>
                    )}
                    <div className="flex-1">
                      {message.role === 'assistant' ? (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            a: LinkRenderer,
                            strong: ({ children }) => <span className="font-semibold text-slate-800">{children}</span>,
                            ul: ({ children }) => <ul className="space-y-1.5 my-2">{children}</ul>,
                            li: ({ children }) => <li className="flex items-start gap-2"><span className="text-emerald-500 mt-1.5">•</span><span className="leading-relaxed">{children}</span></li>,
                            p: ({ children }) => <p className="leading-relaxed mb-2 last:mb-0">{children}</p>,
                            table: ({ children }) => <div className="overflow-x-auto my-3"><table className="min-w-full text-sm">{children}</table></div>,
                            thead: ({ children }) => <thead className="bg-slate-100">{children}</thead>,
                            tbody: ({ children }) => <tbody>{children}</tbody>,
                            tr: ({ children }) => <tr className="border-b border-slate-200 last:border-0">{children}</tr>,
                            th: ({ children }) => <th className="px-3 py-2 text-left font-semibold text-slate-700">{children}</th>,
                            td: ({ children }) => <td className="px-3 py-2 text-slate-600">{children}</td>,
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
                        <User className="w-3.5 h-3.5 text-emerald-600" />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-50/80 rounded-2xl px-5 py-4 border border-slate-200">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm text-slate-500">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          <div className="px-4 py-2 border-t border-slate-100">
            <div className="flex gap-2 overflow-x-auto pb-2">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickAction(action)}
                  className="whitespace-nowrap text-xs font-medium text-emerald-600 bg-emerald-50 hover:bg-emerald-100 px-3 py-1.5 rounded-full transition-colors"
                >
                  {action}
                </button>
              ))}
            </div>
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-slate-100">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me about student analytics, batch performance, or parent communications..."
                className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 outline-none transition-all text-sm"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white px-4 py-3 rounded-xl transition-colors flex items-center gap-2"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Send
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
