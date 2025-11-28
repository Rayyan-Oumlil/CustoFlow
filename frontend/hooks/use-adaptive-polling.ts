/**
 * Adaptive polling hook that adjusts polling interval based on activity
 * - Fast polling when user is active (typing, interacting)
 * - Slow polling when user is inactive
 * - Pauses when tab is hidden
 */

import { useEffect, useRef, useState } from 'react'

interface UseAdaptivePollingOptions {
  /** Fast polling interval (when active) in ms */
  fastInterval?: number
  /** Slow polling interval (when inactive) in ms */
  slowInterval?: number
  /** Initial state (active or inactive) */
  initialActive?: boolean
  /** Callback function to execute on each poll */
  onPoll: () => void | Promise<void>
  /** Whether polling is enabled */
  enabled?: boolean
}

export function useAdaptivePolling({
  fastInterval = 2000, // 2 seconds when active
  slowInterval = 30000, // 30 seconds when inactive
  initialActive = false,
  onPoll,
  enabled = true,
}: UseAdaptivePollingOptions) {
  const [isActive, setIsActive] = useState(initialActive)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const lastActivityRef = useRef<number>(Date.now())
  const isTabVisibleRef = useRef<boolean>(true)

  // Track user activity
  useEffect(() => {
    if (!enabled) return

    const handleActivity = () => {
      lastActivityRef.current = Date.now()
      if (!isActive) {
        setIsActive(true)
      }
    }

    // Consider user active if they interact with the page
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
    events.forEach((event) => {
      window.addEventListener(event, handleActivity, { passive: true })
    })

    // Check for inactivity periodically
    const inactivityCheck = setInterval(() => {
      const timeSinceLastActivity = Date.now() - lastActivityRef.current
      // If inactive for 30 seconds, switch to slow polling
      if (timeSinceLastActivity > 30000 && isActive) {
        setIsActive(false)
      }
    }, 5000) // Check every 5 seconds

    return () => {
      events.forEach((event) => {
        window.removeEventListener(event, handleActivity)
      })
      clearInterval(inactivityCheck)
    }
  }, [enabled, isActive])

  // Track tab visibility
  useEffect(() => {
    const handleVisibilityChange = () => {
      isTabVisibleRef.current = !document.hidden
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  // Polling logic
  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    // Clear existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }

    // Don't poll if tab is hidden
    if (!isTabVisibleRef.current) {
      return
    }

    // Determine polling interval based on activity
    const interval = isActive ? fastInterval : slowInterval

    // Execute immediately on mount/change
    onPoll()

    // Set up polling interval
    intervalRef.current = setInterval(() => {
      // Only poll if tab is visible
      if (isTabVisibleRef.current) {
        onPoll()
      }
    }, interval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [enabled, isActive, fastInterval, slowInterval, onPoll])

  return {
    isActive,
    setIsActive,
  }
}

