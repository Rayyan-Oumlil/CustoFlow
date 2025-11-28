/**
 * Simple in-memory cache with TTL (Time To Live)
 * Used to cache API responses and reduce unnecessary requests
 */

interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number // Time to live in milliseconds
}

class Cache {
  private cache = new Map<string, CacheEntry<any>>()
  private maxSize = 100 // Maximum number of entries

  /**
   * Get data from cache if it exists and is not expired
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key)
    if (!entry) return null

    const now = Date.now()
    if (now - entry.timestamp > entry.ttl) {
      // Entry expired, remove it
      this.cache.delete(key)
      return null
    }

    return entry.data as T
  }

  /**
   * Store data in cache with TTL
   */
  set<T>(key: string, data: T, ttl: number = 60000): void {
    // If cache is full, remove oldest entry
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value
      if (firstKey) {
        this.cache.delete(firstKey)
      }
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    })
  }

  /**
   * Remove specific entry from cache
   */
  delete(key: string): void {
    this.cache.delete(key)
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear()
  }

  /**
   * Invalidate cache entries matching a pattern
   */
  invalidate(pattern: string | RegExp): void {
    const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key)
      }
    }
  }

  /**
   * Get cache statistics
   */
  getStats() {
    const now = Date.now()
    let expired = 0
    let active = 0

    for (const entry of this.cache.values()) {
      if (now - entry.timestamp > entry.ttl) {
        expired++
      } else {
        active++
      }
    }

    return {
      total: this.cache.size,
      active,
      expired,
      maxSize: this.maxSize,
    }
  }
}

// Export singleton instance
export const cache = new Cache()

// Cache keys constants
export const CACHE_KEYS = {
  sessions: (customerId: string) => `sessions:${customerId}`,
  messages: (userId: string, sessionId: string) => `messages:${userId}:${sessionId}`,
  orders: (customerId: string) => `orders:${customerId}`,
  tickets: () => 'tickets:all',
  analytics: () => 'analytics:main',
  analyticsDaily: () => 'analytics:daily',
} as const

