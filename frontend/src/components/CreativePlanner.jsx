import { useState } from 'react'
import { Book, Beaker, Infinity, Star, Flag, Plus, Check, Calendar, Clock, Target } from 'lucide-react'

export default function CreativePlanner() {
  const [activeTab, setActiveTab] = useState('day')
  const [tasks, setTasks] = useState([
    { id: 1, text: 'Complete Physics Chapter 5', subject: 'physics', completed: false, priority: 'high' },
    { id: 2, text: 'Solve 20 Chemistry problems', subject: 'chemistry', completed: true, priority: 'medium' },
    { id: 3, text: 'Math integration practice', subject: 'math', completed: false, priority: 'high' },
    { id: 4, text: 'Review mock test errors', subject: 'general', completed: false, priority: 'low' },
    { id: 5, text: 'Attend doubt clearing session', subject: 'general', completed: false, priority: 'medium' },
  ])
  const [newTask, setNewTask] = useState('')
  const [showAddForm, setShowAddForm] = useState(false)

  const toggleTask = (id) => {
    setTasks(tasks.map(task => 
      task.id === id ? { ...task, completed: !task.completed } : task
    ))
  }

  const addTask = () => {
    if (newTask.trim()) {
      const newTaskObj = {
        id: Date.now(),
        text: newTask,
        subject: 'general',
        completed: false,
        priority: 'medium'
      }
      setTasks([newTaskObj, ...tasks])
      setNewTask('')
      setShowAddForm(false)
    }
  }

  const getSubjectIcon = (subject) => {
    switch (subject) {
      case 'physics': return <Book className="w-4 h-4" />
      case 'chemistry': return <Beaker className="w-4 h-4" />
      case 'math': return <Infinity className="w-4 h-4" />
      default: return <Target className="w-4 h-4" />
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'border-coral-500 bg-coral-50'
      case 'medium': return 'border-pink-300 bg-pink-50'
      case 'low': return 'border-yellow-300 bg-yellow-50'
      default: return 'border-slate-300 bg-slate-50'
    }
  }

  const getTabStyle = (tab) => {
    const baseStyle = "px-6 py-3 font-medium transition-all duration-300 relative"
    if (activeTab === tab) {
      return `${baseStyle} text-slate-800`
    }
    return `${baseStyle} text-slate-500 hover:text-slate-700`
  }

  return (
    <div className="w-full min-h-screen bg-[#fcfbe3] p-6">
      {/* Grid Background Pattern */}
      <div className="absolute inset-0 opacity-5 pointer-events-none" style={{
        backgroundImage: `
          linear-gradient(to right, #1e293b 1px, transparent 1px),
          linear-gradient(to bottom, #1e293b 1px, transparent 1px)
        `,
        backgroundSize: '20px 20px'
      }} />

      <div className="relative max-w-7xl mx-auto">
        {/* Header with Title */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-800 mb-2" style={{ fontFamily: 'cursive, sans-serif' }}>
            My Study Planner ✨
          </h1>
          <p className="text-slate-600">Track your JEE preparation journey</p>
        </div>

        {/* Tabbed Navigation - Notebook Divider Style */}
        <div className="flex gap-2 mb-6">
          {['day', 'week', 'month'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={getTabStyle(tab)}
              style={{
                backgroundColor: activeTab === tab ? '#e0e7ff' : 'transparent',
                borderRadius: activeTab === tab ? '8px 8px 0 0' : '8px',
                border: activeTab === tab ? '2px solid #6366f1' : '2px dashed #cbd5e1'
              }}
            >
              <span className="capitalize">{tab}</span>
              {activeTab === tab && (
                <div className="absolute -bottom-1 left-0 right-0 h-1 bg-indigo-500 rounded-b" />
              )}
            </button>
          ))}
        </div>

        {/* Main Planner Layout - Two Pages */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Page - Calendar / Time Blocking */}
          <div className="bg-white rounded-xl border-2 border-slate-700 p-6 shadow-lg" style={{
            borderRadius: '12px 12px 8px 16px',
            boxShadow: '4px 4px 0px 0px rgba(30, 41, 59, 0.1)'
          }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-indigo-500" />
                {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} View
              </h2>
              <div className="text-sm text-slate-500">
                {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
              </div>
            </div>

            {/* Time Blocks */}
            <div className="space-y-3">
              {[
                { time: '6:00 - 8:00', activity: 'Morning Study - Physics', color: 'bg-blue-100 border-blue-300' },
                { time: '8:00 - 10:00', activity: 'Mock Test Analysis', color: 'bg-purple-100 border-purple-300' },
                { time: '10:00 - 12:00', activity: 'Chemistry Practice', color: 'bg-green-100 border-green-300' },
                { time: '2:00 - 4:00', activity: 'Mathematics - Calculus', color: 'bg-yellow-100 border-yellow-300' },
                { time: '4:00 - 6:00', activity: 'Revision & Notes', color: 'bg-pink-100 border-pink-300' },
              ].map((block, index) => (
                <div
                  key={index}
                  className={`p-3 border-2 rounded-lg transition-all duration-300 hover:scale-[1.02] ${block.color}`}
                  style={{ borderRadius: `${8 + index % 3}px ${12 - index % 3}px ${10 - index % 2}px ${14 - index % 4}px` }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Clock className="w-4 h-4 text-slate-600" />
                      <span className="font-medium text-slate-800">{block.time}</span>
                    </div>
                    <span className="text-sm text-slate-600">{block.activity}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Decorative Arrow */}
            <div className="mt-4 flex items-center gap-2 text-slate-400">
              <div className="flex-1 h-px bg-slate-300" />
              <span className="text-xs">Today's Schedule</span>
              <div className="flex-1 h-px bg-slate-300" />
            </div>
          </div>

          {/* Right Page - Tasks & Trackers */}
          <div className="bg-white rounded-xl border-2 border-slate-700 p-6 shadow-lg" style={{
            borderRadius: '16px 12px 12px 8px',
            boxShadow: '4px 4px 0px 0px rgba(30, 41, 59, 0.1)'
          }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                <Target className="w-5 h-5 text-pink-500" />
                Tasks & Goals
              </h2>
              <button
                onClick={() => setShowAddForm(!showAddForm)}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-all"
                style={{
                  border: '2px solid #1e293b',
                  boxShadow: '4px 4px 0px 0px rgba(0,0,0,1)'
                }}
              >
                <Plus className="w-4 h-4" />
                Add Task
              </button>
            </div>

            {/* Add Task Form */}
            {showAddForm && (
              <div className="mb-4 p-4 bg-slate-50 rounded-lg border-2 border-dashed border-slate-300 animate-draw-entry">
                <input
                  type="text"
                  value={newTask}
                  onChange={(e) => setNewTask(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addTask()}
                  placeholder="What's your next task?"
                  className="w-full px-4 py-2 border-2 border-slate-300 rounded-lg focus:outline-none focus:border-indigo-500"
                  style={{ fontFamily: 'cursive, sans-serif' }}
                />
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={addTask}
                    className="px-4 py-1 bg-green-500 text-white rounded-lg hover:bg-green-600 transition"
                  >
                    Add
                  </button>
                  <button
                    onClick={() => setShowAddForm(false)}
                    className="px-4 py-1 bg-slate-300 text-slate-700 rounded-lg hover:bg-slate-400 transition"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Task List */}
            <div className="space-y-3">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className={`p-4 border-2 rounded-lg transition-all duration-300 ${getPriorityColor(task.priority)} ${task.completed ? 'opacity-60' : ''}`}
                  style={{
                    borderRadius: `${8 + task.id % 3}px ${12 - task.id % 3}px ${10 - task.id % 2}px ${14 - task.id % 4}px`,
                    animation: 'drawEntry 0.3s ease-out'
                  }}
                >
                  <div className="flex items-start gap-3">
                    {/* Sketchy Checkbox */}
                    <button
                      onClick={() => toggleTask(task.id)}
                      className={`w-5 h-5 rounded-full border-2 border-dashed flex-shrink-0 flex items-center justify-center transition-all duration-300 ${
                        task.completed ? 'border-green-500 bg-green-500' : 'border-slate-600'
                      }`}
                    >
                      {task.completed && <Check className="w-3 h-3 text-white" />}
                    </button>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {getSubjectIcon(task.subject)}
                        <span
                          className={`font-medium transition-all duration-300 ${
                            task.completed ? 'text-slate-400 line-through' : 'text-slate-800'
                          }`}
                          style={{ fontFamily: 'cursive, sans-serif' }}
                        >
                          {task.text}
                        </span>
                      </div>

                      {/* Pencil Stroke Animation */}
                      {task.completed && (
                        <div className="relative h-0.5 bg-slate-400 mt-1 animate-pencil-stroke" />
                      )}

                      {/* Priority Badge */}
                      {task.priority === 'high' && (
                        <div className="inline-block mt-2 px-2 py-1 bg-coral-500 text-white text-xs rounded-full">
                          ⚡ High Priority
                        </div>
                      )}
                    </div>

                    {/* Decorative Highlight for High Priority */}
                    {task.priority === 'high' && !task.completed && (
                      <div className="absolute right-0 top-0 bottom-0 w-2 bg-coral-400 opacity-50 skew-x-3" />
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Goal Tracker */}
            <div className="mt-6 p-4 bg-lavender-50 rounded-lg border-2 border-lavender-200">
              <h3 className="font-bold text-slate-800 mb-3 flex items-center gap-2">
                <Star className="w-4 h-4 text-yellow-500" />
                Weekly Goal Tracker
              </h3>
              <div className="grid grid-cols-7 gap-2">
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, index) => (
                  <div
                    key={day}
                    className={`text-center p-2 rounded-lg border-2 transition-all ${
                      index < 4 ? 'bg-green-100 border-green-400' : 'bg-slate-100 border-slate-300'
                    }`}
                  >
                    <div className="text-xs text-slate-600">{day}</div>
                    <div className="mt-1">
                      {index < 4 ? <Star className="w-4 h-4 text-yellow-500 mx-auto fill-yellow-500" /> : <div className="w-4 h-4 mx-auto" />}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex items-center gap-2 text-sm text-slate-600">
                <Flag className="w-4 h-4 text-indigo-500" />
                <span>4/7 days completed this week! Keep going! 🎉</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Decorative Elements */}
        <div className="mt-8 flex items-center justify-center gap-4 text-slate-400">
          <div className="flex-1 h-px bg-slate-300" />
          <span className="text-sm" style={{ fontFamily: 'cursive, sans-serif' }}>
            Stay focused, stay motivated! 💪
          </span>
          <div className="flex-1 h-px bg-slate-300" />
        </div>
      </div>

      {/* Custom CSS for Animations */}
      <style jsx>{`
        @keyframes drawEntry {
          from {
            opacity: 0;
            transform: scale(0.95) translateY(-10px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }

        @keyframes pencilStroke {
          from {
            width: 0;
          }
          to {
            width: 100%;
          }
        }

        .animate-draw-entry {
          animation: drawEntry 0.3s ease-out;
        }

        .animate-pencil-stroke {
          animation: pencilStroke 0.4s ease-out;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
          width: 8px;
        }

        ::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>
    </div>
  )
}
