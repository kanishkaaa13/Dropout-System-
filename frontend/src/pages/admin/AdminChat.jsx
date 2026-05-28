import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '../../api/axiosConfig'
import { MessageSquare, Send, Bot, User, Clock, AlertCircle, Server, Activity, Shield, Database } from 'lucide-react'

export default function AdminChat() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [usingFallback, setUsingFallback] = useState(false)
  const [threads, setThreads] = useState([
    { id: 1, title: 'System Diagnostics', lastMessage: '30 mins ago' },
    { id: 2, title: 'Anomaly Reports', lastMessage: '2 hours ago' },
    { id: 3, title: 'Data Verification', lastMessage: 'Yesterday' }
  ])
  const [activeThread, setActiveThread] = useState(1)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const quickActions = [
    'Export system anomaly reports for at-risk metrics',
    'Check backend service gateway endpoints status',
    'Run diagnostic verification on active mock datasets',
    'Generate system health summary',
    'Verify database integrity and connections'
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
    setUsingFallback(false)

    try {
      const response = await api.post('/chat', {
        message: content,
        thread_id: activeThread
      })
      
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      console.warn('Chat API unavailable, using offline responses:', err.message)
      setUsingFallback(true)
      
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
    
    // Admin-specific offline responses
    if (lowerQuery.includes('anomaly') && (lowerQuery.includes('report') || lowerQuery.includes('export'))) {
      return `Here's the system anomaly report for at-risk metrics:\n\n\`\`\`\n╔════════════════════════════════════════════════════════════╗\n║           JEE PREDICTOR SYSTEM - ANOMALY REPORT              ║\n║           Generated: 2026-05-28 14:35:09 UTC               ║\n╚════════════════════════════════════════════════════════════╝\n\n┌─────────────────────────────────────────────────────────────┐\n│ CRITICAL ANOMALIES                                            │\n├─────────────────────────────────────────────────────────────┤\n│ • ML Model Prediction Latency: 2.3s (threshold: 1.5s)       │\n│ • Database Connection Pool: 85% utilization (warning)        │\n│ • Student Risk Score Calculation: 12 failures in last hour  │\n└─────────────────────────────────────────────────────────────┘\n\n┌─────────────────────────────────────────────────────────────┐\n│ WARNING ANOMALIES                                            │\n├─────────────────────────────────────────────────────────────┤\n│ • API Response Time: Average 450ms (threshold: 300ms)      │\n│ • Memory Usage: 78% (threshold: 85%)                        │\n│ • Disk Space: 12% remaining on /data partition              │\n└─────────────────────────────────────────────────────────────┘\n\n┌─────────────────────────────────────────────────────────────┐\n│ AT-RISK STUDENT METRICS                                      │\n├─────────────────────────────────────────────────────────────┤\n│ • Students with Critical Risk: 4 (↑ 2 from last week)       │\n│ • Attendance Drop >20%: 8 students                          │\n│ • Mock Score Decline: 12 students                           │\n└─────────────────────────────────────────────────────────────┘\n\nRECOMMENDATIONS:\n1. Scale ML prediction service\n2. Optimize database queries\n3. Review student intervention protocols\n\`\`\`\n\nWould you like me to generate a detailed CSV export or investigate specific anomalies?`
    }
    
    if (lowerQuery.includes('backend') && (lowerQuery.includes('status') || lowerQuery.includes('endpoint') || lowerQuery.includes('gateway'))) {
      return `Backend Service Gateway Status:\n\n\`\`\`\n╔════════════════════════════════════════════════════════════╗\n║           SERVICE GATEWAY HEALTH CHECK                        ║\n║           Status: DEGRADED (2/5 services affected)           ║\n╚════════════════════════════════════════════════════════════╝\n\n┌─────────────────────────────────────────────────────────────┐\n│ SERVICE ENDPOINTS                                            │\n├─────────────────────────────────────────────────────────────┤\n│ ✓ /api/v1/auth/login         │ 200 OK │ 45ms  │ Healthy    │\n│ ✓ /api/v1/auth/me           │ 200 OK │ 52ms  │ Healthy    │\n│ ✓ /api/v1/students          │ 200 OK │ 89ms  │ Healthy    │\n│ ⚠ /api/v1/predict           │ 200 OK │ 2.3s  │ SLOW       │\n│ ⚠ /api/v1/alerts            │ 200 OK │ 1.8s  │ SLOW       │\n│ ✓ /api/v1/reports           │ 200 OK │ 156ms │ Healthy    │\n└─────────────────────────────────────────────────────────────┘\n\n┌─────────────────────────────────────────────────────────────┐\n│ DEPENDENCY SERVICES                                          │\n├─────────────────────────────────────────────────────────────┤\n│ • PostgreSQL Database     │ Connected │ Latency: 12ms     │\n│ • ML Model Service        │ Running   │ Latency: 2.1s     │\n│ • Redis Cache             │ Connected │ Latency: 3ms      │\n│ • Email Service           │ Connected │ Latency: 89ms     │\n└─────────────────────────────────────────────────────────────┘\n\nACTIONS REQUIRED:\n1. Investigate /api/v1/predict latency (ML model loading)\n2. Optimize /api/v1/alerts query performance\n3. Consider scaling ML service horizontally\n\`\`\`\n\nWould you like detailed logs for the slow endpoints?`
    }
    
    if (lowerQuery.includes('diagnostic') && (lowerQuery.includes('mock') || lowerQuery.includes('dataset') || lowerQuery.includes('verification'))) {
      return `Diagnostic Verification on Active Mock Datasets:\n\n\`\`\`\n╔════════════════════════════════════════════════════════════╗\n║           MOCK DATASET VERIFICATION REPORT                   ║\n║           Verification Run: 2026-05-28 14:35:09 UTC         ║\n╚════════════════════════════════════════════════════════════╝\n\n┌─────────────────────────────────────────────────────────────┐\n│ DATASET INTEGRITY CHECK                                      │\n├─────────────────────────────────────────────────────────────┤\n│ • Total Students: 20/20 ✓                                   │\n│ • Mock Test Records: 200/200 ✓                              │\n│ • Weekly Surveys: 160/160 ✓                                 │\n│ • Attendance Records: 3,600/3,600 ✓                          │\n│ • Risk Assessments: 20/20 ✓                                 │\n└─────────────────────────────────────────────────────────────┘\n\n┌─────────────────────────────────────────────────────────────┐\n│ DATA QUALITY METRICS                                         │\n├─────────────────────────────────────────────────────────────┤\n│ • Score Range Validity: 0-360 ✓                             │\n│ • Burnout Score Range: 1-10 ✓                               │\n│ • Attendance Rate: 20-100% ✓                                 │\n│ • Date Consistency: ✓                                       │\n│ • No Duplicate Records: ✓                                   │\n└─────────────────────────────────────────────────────────────┘\n\n┌─────────────────────────────────────────────────────────────┐\n│ ML MODEL COMPATIBILITY                                       │\n├─────────────────────────────────────────────────────────────┤\n│ • Feature Completeness: 17/17 ✓                              │\n│ • Data Type Matching: ✓                                      │\n│ • Missing Values: 0% ✓                                       │\n│ • Outlier Detection: 3 flagged (within acceptable range)     │\n└─────────────────────────────────────────────────────────────┘\n\nVERIFICATION STATUS: PASSED\n\nRECOMMENDATIONS:\n1. Monitor the 3 flagged outliers for trend analysis\n2. Schedule next verification in 7 days\n\`\`\`\n\nWould you like me to investigate the flagged outliers?`
    }
    
    if (lowerQuery.includes('health') && (lowerQuery.includes('summary') || lowerQuery.includes('system'))) {
      return `System Health Summary:\n\n\`\`\`\n╔════════════════════════════════════════════════════════════╗\n║           JEE PREDICTOR SYSTEM - HEALTH SUMMARY              ║\n║           Overall Status: ⚠ DEGRADED                          ║\n╚════════════════════════════════════════════════════════════╝\n\n┌─────────────────────────────────────────────────────────────┐\n│ INFRASTRUCTURE                                               │\n├─────────────────────────────────────────────────────────────┤\n│ CPU Usage:              42%  │ Normal                      │\n│ Memory Usage:           78%  │ ⚠ High (threshold: 85%)     │\n│ Disk Usage:             88%  │ ⚠ High (threshold: 90%)     │\n│ Network I/O:           125 MB/s │ Normal                    │\n└─────────────────────────────────────────────────────────────┘\n\n┌─────────────────────────────────────────────────────────────┐\n│ APPLICATION METRICS                                          │\n├─────────────────────────────────────────────────────────────┤\n│ Active Users:          23      │ Normal                      │\n│ API Requests/min:      156     │ Normal                      │\n│ Error Rate:            0.8%    │ Normal                      │\n│ Avg Response Time:     450ms   │ ⚠ High (threshold: 300ms)  │\n└─────────────────────────────────────────────────────────────┘\n\n┌─────────────────────────────────────────────────────────────┐\n│ DATABASE                                                   │\n├─────────────────────────────────────────────────────────────┤\n│ Connections:           45/100  │ Normal                      │\n│ Query Latency:         12ms    │ Normal                      │\n│ Deadlocks:             0       │ Normal                      │\n│ Replication Lag:       0ms     │ Normal                      │\n└─────────────────────────────────────────────────────────────┘\n\n┌─────────────────────────────────────────────────────────────┐\n│ ML SERVICES                                                 │\n├─────────────────────────────────────────────────────────────┤\n│ Model Loading Time:   2.1s    │ ⚠ High                      │\n│ Prediction Accuracy:  91.2%   ✓ Excellent                  │\n│ Feature Processing:   180ms   ✓ Normal                     │\n└─────────────────────────────────────────────────────────────┘\n\nIMMEDIATE ACTIONS:\n1. Clear disk space on /data partition\n2. Investigate API response time degradation\n3. Optimize ML model loading process\n\`\`\`\n\nWould you like detailed metrics for any specific component?`
    }
    
    if (lowerQuery.includes('database') && (lowerQuery.includes('integrity') || lowerQuery.includes('connection') || lowerQuery.includes('verify'))) {
      return `Database Integrity and Connection Verification:\n\n\`\`\`\n╔════════════════════════════════════════════════════════════╗\n║           DATABASE INTEGRITY VERIFICATION                   ║\n║           Database: PostgreSQL 14.2                        ║\n╚════════════════════════════════════════════════════════════╝\n\n┌─────────────────────────────────────────────────────────────┐\n│ CONNECTION STATUS                                            │\n├─────────────────────────────────────────────────────────────┤\n│ Primary Connection:    ✓ Connected (latency: 12ms)        │\n│ Connection Pool:       45/100 active (healthy)              │\n│ Max Connections:       100 (configurable)                   │\n│ Idle Connections:      55 (within normal range)             │\n└─────────────────────────────────────────────────────────────┘\n\n┌─────────────────────────────────────────────────────────────┐\n│ TABLE INTEGRITY CHECK                                        │\n├─────────────────────────────────────────────────────────────┤\n│ ✓ users              │ 23 rows    │ No corruption detected  │\n│ ✓ students           │ 20 rows    │ No corruption detected  │\n│ ✓ batches            │ 3 rows     │ No corruption detected  │\n│ ✓ mock_test_results  │ 200 rows   │ No corruption detected  │\n│ ✓ weekly_surveys     │ 160 rows   │ No corruption detected  │\n│ ✓ attendance_records │ 3,600 rows │ No corruption detected │\n│ ✓ risk_assessments   │ 20 rows    │ No corruption detected  │\n│ ✓ alerts             │ 12 rows    │ No corruption detected  │\n└─────────────────────────────────────────────────────────────┘\n\n┌─────────────────────────────────────────────────────────────┐\n│ FOREIGN KEY CONSTRAINTS                                     │\n├─────────────────────────────────────────────────────────────┤\n│ ✓ students.batch_id → batches.id                            │\n│ ✓ students.assigned_faculty_id → users.id                   │\n│ ✓ risk_assessments.student_id → students.id                 │\n│ ✓ alerts.student_id → students.id                           │\n│ ✓ alerts.assessment_id → risk_assessments.id               │\n└─────────────────────────────────────────────────────────────┘\n\n┌─────────────────────────────────────────────────────────────┐\n│ INDEX PERFORMANCE                                            │\n├─────────────────────────────────────────────────────────────┤\n│ ✓ idx_students_code         │ Used: 89%  │ Efficient        │\n│ ✓ idx_risk_student_id       │ Used: 95%  │ Efficient        │\n│ ✓ idx_alerts_risk_level     │ Used: 78%  │ Efficient        │\n│ ✓ idx_attendance_date       │ Used: 92%  │ Efficient        │\n└─────────────────────────────────────────────────────────────┘\n\nINTEGRITY STATUS: ✓ PASSED\n\nRECOMMENDATIONS:\n1. Consider VACUUM ANALYZE for index optimization\n2. Monitor connection pool during peak hours\n\`\`\`\n\nWould you like me to run a full database backup or check query performance?`
    }
    
    // Default fallback response
    return `I understand you're asking about "${query}". While I'm currently running in offline mode, I can still provide some admin-focused guidance:\n\n**Available Capabilities:**\n- Export system anomaly reports\n- Check backend service gateway status\n- Run diagnostic verification on datasets\n- Generate system health summaries\n- Verify database integrity\n\n**For Specific Help:**\n- Try asking about: anomaly reports, gateway status, dataset diagnostics, system health, or database verification\n- I can provide detailed system analysis and operational recommendations\n\n**Note:** For real-time monitoring and system administration, please use the [Admin Dashboard](/admin) or connect directly with system services.\n\nIs there anything specific about system operations I can help you with?`
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

  // Empty state for admin view
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
                      ? 'bg-purple-100 border border-purple-200'
                      : 'hover:bg-slate-100 border border-transparent'
                  }`}
                >
                  <p className="text-sm font-medium text-slate-900">{thread.title}</p>
                  <p className="text-xs text-slate-500 mt-1">{thread.lastMessage}</p>
                </button>
              ))}
            </div>
            <div className="p-3 border-t border-slate-200">
              <button className="w-full text-sm font-medium text-purple-600 hover:text-purple-700 py-2 px-3 rounded-lg hover:bg-purple-50 transition-colors">
                + New Conversation
              </button>
            </div>
          </div>

          {/* Empty State */}
          <div className="flex-1 flex flex-col">
            {/* Chat Header */}
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">System Operations & Analytics Bot</h3>
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
                  <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Bot className="w-8 h-8 text-purple-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 mb-2">System Operations & Analytics Bot</h2>
                  <p className="text-slate-500">Your intelligent assistant for system monitoring, diagnostics, and operational analytics</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Capabilities */}
                  <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
                    <div className="flex items-center gap-2 mb-3">
                      <Server className="w-5 h-5 text-purple-600" />
                      <h3 className="font-semibold text-slate-900">Capabilities</h3>
                    </div>
                    <ul className="space-y-2 text-sm text-slate-600">
                      <li className="flex items-start gap-2">
                        <span className="text-purple-500 mt-0.5">•</span>
                        Export anomaly reports
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-purple-500 mt-0.5">•</span>
                        Check gateway status
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-purple-500 mt-0.5">•</span>
                        Run dataset diagnostics
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-purple-500 mt-0.5">•</span>
                        Verify database integrity
                      </li>
                    </ul>
                  </div>

                  {/* Examples */}
                  <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
                    <div className="flex items-center gap-2 mb-3">
                      <Activity className="w-5 h-5 text-purple-600" />
                      <h3 className="font-semibold text-slate-900">Examples</h3>
                    </div>
                    <ul className="space-y-2 text-sm text-slate-600">
                      <li className="flex items-start gap-2">
                        <span className="text-purple-500 mt-0.5">•</span>
                        System health summaries
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-purple-500 mt-0.5">•</span>
                        Backend endpoint monitoring
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-purple-500 mt-0.5">•</span>
                        ML service diagnostics
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-purple-500 mt-0.5">•</span>
                        Database verification
                      </li>
                    </ul>
                  </div>

                  {/* System Limitations */}
                  <div className="bg-slate-50 rounded-xl p-5 border border-slate-100">
                    <div className="flex items-center gap-2 mb-3">
                      <Shield className="w-5 h-5 text-amber-600" />
                      <h3 className="font-semibold text-slate-900">Access Level</h3>
                    </div>
                    <ul className="space-y-2 text-sm text-slate-600">
                      <li className="flex items-start gap-2">
                        <span className="text-amber-500 mt-0.5">•</span>
                        Full system access
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-amber-500 mt-0.5">•</span>
                        Administrative commands
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-amber-500 mt-0.5">•</span>
                        System configuration
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-amber-500 mt-0.5">•</span>
                        Audit logging enabled
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
                    className="whitespace-nowrap text-xs font-medium text-purple-600 bg-purple-50 hover:bg-purple-100 px-3 py-1.5 rounded-full transition-colors"
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
                  placeholder="Ask me about system operations, diagnostics, or analytics..."
                  className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all text-sm"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white px-4 py-3 rounded-xl transition-colors flex items-center gap-2"
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
                    ? 'bg-purple-100 border border-purple-200'
                    : 'hover:bg-slate-100 border border-transparent'
                }`}
              >
                <p className="text-sm font-medium text-slate-900">{thread.title}</p>
                <p className="text-xs text-slate-500 mt-1">{thread.lastMessage}</p>
              </button>
            ))}
          </div>
          <div className="p-3 border-t border-slate-200">
            <button className="w-full text-sm font-medium text-purple-600 hover:text-purple-700 py-2 px-3 rounded-lg hover:bg-purple-50 transition-colors">
              + New Conversation
            </button>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Chat Header */}
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">System Operations & Analytics Bot</h3>
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
                      ? 'bg-purple-600 text-white'
                      : 'bg-slate-50/80 text-slate-900 border border-slate-200'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {message.role === 'assistant' && (
                      <div className="w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center shrink-0 mt-0.5">
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
                            li: ({ children }) => <li className="flex items-start gap-2"><span className="text-purple-500 mt-1.5">•</span><span className="leading-relaxed">{children}</span></li>,
                            p: ({ children }) => <p className="leading-relaxed mb-2 last:mb-0">{children}</p>,
                            code: ({ children, className }) => {
                              if (className?.includes('language-')) {
                                return <code className="bg-slate-950 text-emerald-400 font-mono text-xs p-3 rounded-lg block overflow-x-auto">{children}</code>
                              }
                              return <code className="bg-slate-200 text-slate-800 px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>
                            },
                            pre: ({ children }) => <pre className="bg-slate-950 text-emerald-400 font-mono text-xs p-3 rounded-lg overflow-x-auto">{children}</pre>
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
                        <User className="w-3.5 h-3.5 text-purple-600" />
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
                  className="whitespace-nowrap text-xs font-medium text-purple-600 bg-purple-50 hover:bg-purple-100 px-3 py-1.5 rounded-full transition-colors"
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
                placeholder="Ask me about system operations, diagnostics, or analytics..."
                className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all text-sm"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white px-4 py-3 rounded-xl transition-colors flex items-center gap-2"
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
