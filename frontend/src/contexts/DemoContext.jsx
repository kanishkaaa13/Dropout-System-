import { createContext, useContext, useState, useEffect } from 'react'

const DemoContext = createContext(null)

export function DemoProvider({ children }) {
  const [isDemoMode, setIsDemoMode] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem('demo_mode')
    if (stored) {
      setIsDemoMode(stored === 'true')
    }
  }, [])

  const toggleDemoMode = (enabled) => {
    setIsDemoMode(enabled)
    localStorage.setItem('demo_mode', enabled.toString())
  }

  return (
    <DemoContext.Provider value={{ isDemoMode, toggleDemoMode }}>
      {children}
    </DemoContext.Provider>
  )
}

export const useDemo = () => {
  const ctx = useContext(DemoContext)
  if (!ctx) throw new Error('useDemo must be used within DemoProvider')
  return ctx
}
