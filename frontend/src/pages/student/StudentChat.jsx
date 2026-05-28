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
  const [usingFallback, setUsingFallback] = useState(false)
  const [ollamaStatus, setOllamaStatus] = useState('unknown') // 'unknown', 'online', 'offline'
  const [threads, setThreads] = useState([
    { id: 1, title: 'Physics Strategy', lastMessage: '2 hours ago' },
    { id: 2, title: 'Managing Anxiety', lastMessage: 'Yesterday' },
    { id: 3, title: 'Time Management', lastMessage: '3 days ago' }
  ])
  const [activeThread, setActiveThread] = useState(1)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Independent Ollama status check - decoupled from message pipeline
  const checkOllamaStatus = useCallback(async () => {
    try {
      console.log('Checking Ollama status...')
      const response = await api.get('/chat/status')
      console.log('Ollama status check response:', response.data)
      if (response.data.ollama_available) {
        setOllamaStatus('online')
        setUsingFallback(false)
        console.log('Ollama is online, model:', response.data.selected_model)
      } else {
        setOllamaStatus('offline')
        setUsingFallback(true)
        console.log('Ollama is offline')
      }
    } catch (err) {
      console.error('Ollama status check failed:', err)
      // Only set to offline if it's a network error
      if (err.code === 'ECONNREFUSED' || err.code === 'ERR_NETWORK') {
        setOllamaStatus('offline')
        setUsingFallback(true)
      }
      // Otherwise keep current status
    }
  }, [])

  // Check Ollama status on mount and every 30 seconds
  useEffect(() => {
    checkOllamaStatus()
    const interval = setInterval(checkOllamaStatus, 30000) // Poll every 30 seconds
    return () => clearInterval(interval)
  }, [checkOllamaStatus])

  const quickActions = [
    'How do I optimize my Chemistry score?',
    'Generate a revision schedule for organic chemistry',
    'Am I tracking towards my target rank?',
    'Tips for managing exam stress',
    'How to improve my Physics problem-solving?'
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
        role: 'student'
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
      // Only set to offline if backend explicitly reports offline status
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
      
      // Only set to offline if it's a legitimate network disconnect error
      if (err.code === 'ECONNREFUSED' || err.code === 'ERR_NETWORK' || 
          (err.response && err.response.status >= 500)) {
        console.log('Network error detected, setting offline mode')
        setOllamaStatus('offline')
        setUsingFallback(true)
      } else {
        console.log('Non-network error, keeping current status')
        // Do NOT toggle the main status variable for non-network errors
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
    
    // Keyword-based offline responses
    if (lowerQuery.includes('chemistry') && (lowerQuery.includes('optimize') || lowerQuery.includes('improve'))) {
      return `To optimize your Chemistry score:\n\n**1. Focus on NCERT First**\n- Master all NCERT concepts and examples\n- 80% of JEE Chemistry comes from NCERT\n\n**2. Organic Chemistry Strategy**\n- Learn reaction mechanisms, don't memorize\n- Practice named reactions daily\n- Use flashcards for functional groups\n\n**3. Physical Chemistry**\n- Master formulas and their applications\n- Practice numerical problems regularly\n- Focus on thermodynamics and equilibrium\n\n**4. Inorganic Chemistry**\n- Create summary tables for trends\n- Memorize exceptions separately\n- Revise daily for 15 minutes\n\nWould you like me to create a specific study plan for any of these areas?`
    }
    
    if (lowerQuery.includes('revision') || lowerQuery.includes('schedule')) {
      return `Here's a revision schedule for organic chemistry:\n\n**Week 1-2: Basics**\n- Day 1-2: IUPAC nomenclature\n- Day 3-4: Isomerism (structural & stereoisomerism)\n- Day 5-6: Electronic effects & reaction intermediates\n- Day 7: Revision & practice\n\n**Week 3-4: Hydrocarbons**\n- Day 8-10: Alkanes, Alkenes, Alkynes\n- Day 11-13: Aromatic hydrocarbons\n- Day 14: Mixed practice\n\n**Week 5-6: Functional Groups**\n- Day 15-17: Haloalkanes & Haloarenes\n- Day 18-20: Alcohols, Phenols, Ethers\n- Day 21: Revision\n\n**Week 7-8: Advanced Topics**\n- Day 22-24: Aldehydes, Ketones, Carboxylic acids\n- Day 25-27: Amines & Diazonium salts\n- Day 28: Full revision\n\n**Daily Routine:**\n- 30 mins: Theory revision\n- 30 mins: Problem solving\n- 15 mins: Quick recap\n\nShall I adjust this based on your current preparation level?`
    }
    
    if (lowerQuery.includes('rank') || lowerQuery.includes('target') || lowerQuery.includes('tracking')) {
      return `Based on your current performance metrics, here's an analysis of your rank trajectory:\n\n**Current Status Analysis:**\n- Your mock test average shows steady improvement\n- Subject-wise performance indicates strong Math foundation\n- Physics needs focused attention on numerical problems\n\n**To Reach Your Target Rank:**\n\n**1. Immediate Actions (Next 2 weeks)**\n- Identify weak topics through mock analysis\n- Dedicate 2 hours daily to weak areas\n- Solve 20+ problems per weak topic\n\n**2. Medium-term Strategy (Next 2 months)**\n- Complete all previous year JEE questions\n- Join test series for regular practice\n- Focus on accuracy over speed initially\n\n**3. Long-term Goals**\n- Maintain consistency in daily study hours\n- Regular revision of completed topics\n- Stay positive and manage stress\n\n**Recommendation:** Use the [Prediction Engine](/student/predict) to simulate different scenarios and see how improving specific metrics affects your rank.\n\nWould you like a detailed subject-wise improvement plan?`
    }
    
    if (lowerQuery.includes('stress') || lowerQuery.includes('anxiety') || lowerQuery.includes('pressure')) {
      return `Managing exam stress is crucial for optimal performance. Here are proven strategies:\n\n**1. Physical Well-being**\n- Get 7-8 hours of quality sleep\n- Exercise for 30 mins daily (even light walks)\n- Stay hydrated and eat balanced meals\n\n**2. Mental Techniques**\n- Practice deep breathing (4-7-8 technique)\n- Try meditation for 10 mins daily\n- Break study into 25-min focused sessions (Pomodoro)\n\n**3. Study Management**\n- Set realistic daily goals\n- Celebrate small achievements\n- Take regular breaks to avoid burnout\n- Maintain a study journal to track progress\n\n**4. Social Support**\n- Talk to friends/family about your feelings\n- Join study groups for motivation\n- Don't compare yourself with others\n\n**5. Exam Day Preparation**\n- Practice mock tests in exam conditions\n- Develop a pre-exam routine\n- Focus on the process, not just results\n\nRemember: Some stress is normal and can actually improve performance. The key is managing it effectively.\n\nWould you like specific techniques for any of these areas?`
    }
    
    if (lowerQuery.includes('physics') && (lowerQuery.includes('problem') || lowerQuery.includes('improve'))) {
      return `To improve your Physics problem-solving skills:\n\n**1. Foundation Building**\n- Master all formulas and their derivations\n- Understand the physical meaning behind equations\n- Practice dimensional analysis\n\n**2. Problem-Solving Strategy**\n- Read the problem carefully twice\n- Draw diagrams whenever possible\n- Identify given quantities and what's asked\n- Choose the right approach (formula vs concept)\n- Solve step-by-step, showing all work\n\n**3. Topic-wise Focus**\n\n**Mechanics:**\n- Free body diagrams are essential\n- Practice conservation laws problems\n- Master projectile motion\n\n**Electrodynamics:**\n- Understand circuit diagrams\n- Practice Gauss's law applications\n- Focus on electromagnetic induction\n\n**Optics:**\n- Ray diagrams for all cases\n- Practice numerical problems\n- Understand wave vs ray optics\n\n**4. Daily Practice Routine**\n- Solve 10-15 problems daily\n- Start with easy, move to medium\n- Analyze mistakes in mock tests\n- Maintain a formula notebook\n\n**5. Resources**\n- HC Verma for concepts\n- DC Pandey for practice\n- Previous year JEE problems\n\nWould you like a specific study plan for any Physics topic?`
    }
    
    // Default fallback response
    return `I understand you're asking about "${query}". While I'm currently running in offline mode, I can still provide some guidance:\n\n**General Study Tips:**\n- Consistency is more important than intensity\n- Focus on understanding concepts over memorization\n- Regular revision is key for long-term retention\n- Take care of your physical and mental health\n\n**For Specific Help:**\n- Try asking about: Chemistry optimization, revision schedules, rank tracking, stress management, or Physics problem-solving\n- I can provide detailed strategies for these topics\n\n**Note:** For more personalized advice, please connect with your faculty counselor or use the [Prediction Engine](/student/predict) to analyze your performance metrics.\n\nIs there anything specific about JEE preparation I can help you with?`
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

  // Empty state for student view
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
                <div className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">AI Academic Counselor</h3>
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
                  <div className="w-16 h-16 bg-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Bot className="w-8 h-8 text-indigo-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 mb-2">AI Academic Counselor</h2>
                  <p className="text-slate-500">Your personal guide for JEE preparation, stress management, and academic success</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Capabilities */}
                  <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
                    <div className="flex items-center gap-2 mb-3">
                      <Zap className="w-5 h-5 text-indigo-600" />
                      <h3 className="font-semibold text-slate-900">Capabilities</h3>
                    </div>
                    <ul className="space-y-2 text-sm text-slate-600">
                      <li className="flex items-start gap-2">
                        <span className="text-indigo-500 mt-0.5">•</span>
                        Analyze performance trends
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-indigo-500 mt-0.5">•</span>
                        Create study schedules
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-indigo-500 mt-0.5">•</span>
                        Provide stress management tips
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-indigo-500 mt-0.5">•</span>
                        Subject-specific guidance
                      </li>
                    </ul>
                  </div>

                  {/* Examples */}
                  <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
                    <div className="flex items-center gap-2 mb-3">
                      <BookOpen className="w-5 h-5 text-indigo-600" />
                      <h3 className="font-semibold text-slate-900">Examples</h3>
                    </div>
                    <ul className="space-y-2 text-sm text-slate-600">
                      <li className="flex items-start gap-2">
                        <span className="text-indigo-500 mt-0.5">•</span>
                        Organic chemistry schedule
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-indigo-500 mt-0.5">•</span>
                        Physics problem-solving
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-indigo-500 mt-0.5">•</span>
                        Rank trajectory analysis
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-indigo-500 mt-0.5">•</span>
                        Exam anxiety management
                      </li>
                    </ul>
                  </div>

                  {/* System Limitations */}
                  <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
                    <div className="flex items-center gap-2 mb-3">
                      <AlertTriangle className="w-5 h-5 text-amber-600" />
                      <h3 className="font-semibold text-slate-900">System Limitations</h3>
                    </div>
                    <ul className="space-y-2 text-sm text-slate-600">
                      <li className="flex items-start gap-2">
                        <span className="text-amber-500 mt-0.5">•</span>
                        Running on localized mock data
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-amber-500 mt-0.5">•</span>
                        Responses may vary
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-amber-500 mt-0.5">•</span>
                        Connect faculty for personalized help
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-amber-500 mt-0.5">•</span>
                        Use Prediction Engine for analysis
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
                    className="whitespace-nowrap text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-full transition-colors"
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
                  placeholder="Ask me anything about your JEE preparation..."
                  className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none transition-all text-sm"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white px-4 py-3 rounded-xl transition-colors flex items-center gap-2"
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

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Chat Header */}
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">AI Academic Counselor</h3>
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
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-50/80 text-slate-900 border border-slate-200'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {message.role === 'assistant' && (
                      <div className="w-6 h-6 bg-indigo-600 rounded-full flex items-center justify-center shrink-0 mt-0.5">
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
                            li: ({ children }) => <li className="flex items-start gap-2"><span className="text-indigo-500 mt-1.5">•</span><span className="leading-relaxed">{children}</span></li>,
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
                        <User className="w-3.5 h-3.5 text-indigo-600" />
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
                  className="whitespace-nowrap text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-full transition-colors"
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
                placeholder="Ask me anything about your JEE preparation..."
                className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none transition-all text-sm"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white px-4 py-3 rounded-xl transition-colors flex items-center gap-2"
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
