import { useState } from 'react'
import { Plus, Check, Clock, Calendar } from 'lucide-react'

export default function CreativePlanner() {
  const [activeTab, setActiveTab] = useState('day')
  const [tasks, setTasks] = useState([
    { id: 1, text: 'Complete Physics Chapter 5', completed: false, priority: 'high' },
    { id: 2, text: 'Solve 20 Chemistry problems', completed: true, priority: 'medium' },
    { id: 3, text: 'Math integration practice', completed: false, priority: 'high' },
    { id: 4, text: 'Review mock test errors', completed: false, priority: 'low' },
    { id: 5, text: 'Attend doubt clearing session', completed: false, priority: 'medium' },
  ])
  const [showAddForm, setShowAddForm] = useState(false)
  const [newTask, setNewTask] = useState('')

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
        completed: false,
        priority: 'medium'
      }
      setTasks([newTaskObj, ...tasks])
      setNewTask('')
      setShowAddForm(false)
    }
  }

  const getPriorityDotColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-500'
      case 'medium': return 'bg-orange-500'
      case 'low': return 'bg-gray-400'
      default: return 'bg-gray-400'
    }
  }

  const timeSlots = [
    { time: '6:00 AM', event: null },
    { time: '7:00 AM', event: null },
    { time: '8:00 AM', event: { subject: 'Physics', title: 'Morning Study - Mechanics' } },
    { time: '9:00 AM', event: { subject: 'Physics', title: 'Morning Study - Mechanics' } },
    { time: '10:00 AM', event: { subject: 'Chemistry', title: 'Organic Chemistry Practice' } },
    { time: '11:00 AM', event: { subject: 'Chemistry', title: 'Organic Chemistry Practice' } },
    { time: '12:00 PM', event: null },
    { time: '1:00 PM', event: null },
    { time: '2:00 PM', event: { subject: 'Mathematics', title: 'Calculus Integration' } },
    { time: '3:00 PM', event: { subject: 'Mathematics', title: 'Calculus Integration' } },
    { time: '4:00 PM', event: { subject: 'Physics', title: 'Mock Test Analysis' } },
    { time: '5:00 PM', event: { subject: 'Chemistry', title: 'Problem Solving' } },
    { time: '6:00 PM', event: null },
    { time: '7:00 PM', event: { subject: 'Mathematics', title: 'Revision & Notes' } },
    { time: '8:00 PM', event: { subject: 'Physics', title: 'Formula Review' } },
    { time: '9:00 PM', event: null },
    { time: '10:00 PM', event: null },
  ]

  const completedDays = 4
  const todayIndex = 3 // Thursday (0-indexed)

  return (
    <div className="w-full min-h-screen bg-white p-8">
      <div className="max-w-[1200px] mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Study Planner</h1>
            <p className="text-gray-500 mt-1">Thursday, 29 May 2025</p>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-4 py-2 bg-[#6B5CE7] text-white rounded-lg hover:bg-[#5A4BD1] transition-colors font-medium text-sm"
          >
            New Task
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 mb-6 bg-white border border-gray-200 rounded-lg p-1 w-fit">
          {['day', 'week', 'month'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-[#6B5CE7] text-white'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[60%_38%] gap-6">
          {/* Left Column - Schedule */}
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Calendar className="w-5 h-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-900">Schedule</h2>
            </div>

            <div className="space-y-2">
              {timeSlots.map((slot, index) => (
                <div
                  key={index}
                  className={`flex items-center gap-3 ${slot.event ? '' : 'border-b border-dashed border-gray-200 pb-2'}`}
                >
                  <div className="w-20 text-xs text-gray-500 font-medium">
                    {slot.time}
                  </div>
                  {slot.event ? (
                    <div className="flex-1 bg-[#F3F0FF] border-l-3 border-[#6B5CE7] rounded-md p-2.5 px-3.5">
                      <div className="font-medium text-gray-900 text-sm">{slot.event.title}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{slot.event.subject}</div>
                    </div>
                  ) : (
                    <div className="flex-1 h-8" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Right Column - Tasks */}
          <div className="space-y-6">
            {/* Tasks Card */}
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Tasks</h2>
                <span className="text-sm text-gray-500">{tasks.length} tasks</span>
              </div>

              <div className="space-y-3">
                {tasks.map((task) => (
                  <div
                    key={task.id}
                    className={`flex items-center gap-3 ${task.completed ? 'opacity-60' : ''}`}
                  >
                    <button
                      onClick={() => toggleTask(task.id)}
                      className={`w-5 h-5 rounded-full border-2 flex-shrink-0 flex items-center justify-center transition-colors ${
                        task.completed
                          ? 'border-green-500 bg-green-500'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      {task.completed && <Check className="w-3 h-3 text-white" />}
                    </button>
                    <span
                      className={`flex-1 text-sm ${task.completed ? 'line-through text-gray-400' : 'text-gray-900'}`}
                    >
                      {task.text}
                    </span>
                    <div className={`w-2 h-2 rounded-full ${getPriorityDotColor(task.priority)}`} />
                  </div>
                ))}
              </div>

              <button
                onClick={() => setShowAddForm(!showAddForm)}
                className="mt-4 w-full px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors"
              >
                Add Task
              </button>

              {showAddForm && (
                <div className="mt-3 flex gap-2">
                  <input
                    type="text"
                    value={newTask}
                    onChange={(e) => setNewTask(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addTask()}
                    placeholder="Enter task..."
                    className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#6B5CE7]"
                  />
                  <button
                    onClick={addTask}
                    className="px-4 py-2 bg-[#6B5CE7] text-white rounded-lg text-sm hover:bg-[#5A4BD1] transition-colors"
                  >
                    Add
                  </button>
                </div>
              )}
            </div>

            {/* Weekly Goal Tracker */}
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Weekly Goal</h2>
              <div className="flex items-center justify-between mb-3">
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, index) => (
                  <div key={day} className="text-center">
                    <div className="text-xs text-gray-500 mb-1">{day}</div>
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        index < completedDays
                          ? 'bg-[#6B5CE7]'
                          : index === todayIndex
                          ? 'border-2 border-[#6B5CE7]'
                          : 'bg-gray-100'
                      }`}
                    >
                      {index < completedDays ? (
                        <Check className="w-4 h-4 text-white" />
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-sm text-gray-500 text-center">
                {completedDays} of 7 days completed
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
