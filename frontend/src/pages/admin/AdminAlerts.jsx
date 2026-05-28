import { useState } from 'react'
import { AlertTriangle, CheckCircle, Filter, Search, MoreVertical } from 'lucide-react'

export default function AdminAlerts() {
  const [filter, setFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  // Mock alerts data
  const alerts = [
    { id: 1, studentName: 'Rahul Sharma', riskLevel: 'Critical', triggerReason: 'Attendance below 60%', batch: 'Batch A', date: '2026-05-28', resolved: false },
    { id: 2, studentName: 'Priya Patel', riskLevel: 'High', triggerReason: 'Mock test score dropped 20%', batch: 'Batch B', date: '2026-05-27', resolved: false },
    { id: 3, studentName: 'Amit Kumar', riskLevel: 'High', triggerReason: 'Assignment completion < 50%', batch: 'Batch A', date: '2026-05-27', resolved: false },
    { id: 4, studentName: 'Sneha Gupta', riskLevel: 'Medium', triggerReason: 'Stress level elevated', batch: 'Batch C', date: '2026-05-26', resolved: false },
    { id: 5, studentName: 'Vikram Singh', riskLevel: 'Critical', triggerReason: 'Burnout score high', batch: 'Batch B', date: '2026-05-26', resolved: true },
    { id: 6, studentName: 'Neha Verma', riskLevel: 'Medium', triggerReason: 'Study hours decreased', batch: 'Batch A', date: '2026-05-25', resolved: false },
    { id: 7, studentName: 'Rajesh Kumar', riskLevel: 'Low', triggerReason: 'Peer pressure reported', batch: 'Batch C', date: '2026-05-25', resolved: false },
    { id: 8, studentName: 'Anjali Singh', riskLevel: 'High', triggerReason: 'Test attempt rate low', batch: 'Batch B', date: '2026-05-24', resolved: true },
  ]

  const filteredAlerts = alerts.filter(alert => {
    const matchesFilter = filter === 'all' || alert.riskLevel.toLowerCase() === filter
    const matchesSearch = alert.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         alert.batch.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesFilter && matchesSearch && !alert.resolved
  })

  const getRiskBadgeColor = (level) => {
    switch (level.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-700'
      case 'high': return 'bg-orange-100 text-orange-700'
      case 'medium': return 'bg-yellow-100 text-yellow-700'
      case 'low': return 'bg-green-100 text-green-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const handleMarkResolved = (id) => {
    console.log('Mark alert as resolved:', id)
    // In real app, this would call an API
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Student Alerts</h1>
            <p className="text-gray-500 mt-1">Monitor and manage at-risk students</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search students..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B5CE7] focus:border-transparent"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm p-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-600">Filter by risk level:</span>
          <div className="flex gap-2">
            {['all', 'critical', 'high', 'medium', 'low'].map((level) => (
              <button
                key={level}
                onClick={() => setFilter(level)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  filter === level
                    ? 'bg-[#6B5CE7] text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="bg-white rounded-xl shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-4">
                  Student
                </th>
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-4">
                  Risk Level
                </th>
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-4">
                  Trigger Reason
                </th>
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-4">
                  Batch
                </th>
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-4">
                  Date
                </th>
                <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-4">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.map((alert, index) => (
                <tr key={alert.id} className={index % 2 === 0 ? 'bg-white' : 'bg-[#F8F9FC]'}>
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">{alert.studentName}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRiskBadgeColor(alert.riskLevel)}`}>
                      {alert.riskLevel}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-600">{alert.triggerReason}</td>
                  <td className="px-6 py-4 text-gray-600">{alert.batch}</td>
                  <td className="px-6 py-4 text-gray-600">{alert.date}</td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => handleMarkResolved(alert.id)}
                      className="flex items-center gap-2 px-3 py-1.5 bg-[#6B5CE7] text-white rounded-lg text-sm font-medium hover:bg-[#5A4BD1] transition-colors"
                    >
                      <CheckCircle className="w-4 h-4" />
                      Mark Resolved
                    </button>
                  </td>
                </tr>
              ))}
              {filteredAlerts.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>No alerts found matching your filters</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
