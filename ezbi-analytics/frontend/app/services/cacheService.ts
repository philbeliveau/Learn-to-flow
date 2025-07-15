/**
 * Performance-Optimized Caching Service
 * Performance Engineer Integration: Redis-backed caching with local fallback
 * Reduces API calls and improves dashboard loading times
 */

import { authService } from './authService';

interface CacheConfig {
  ttl: number; // Time to live in seconds
  useLocalStorage: boolean;
  useMemoryCache: boolean;
  useRedisCache: boolean;
}

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  key: string;
}

const DEFAULT_CACHE_CONFIG: CacheConfig = {
  ttl: 300, // 5 minutes
  useLocalStorage: true,
  useMemoryCache: true,
  useRedisCache: true
};

export class CacheService {
  private static instance: CacheService;
  private memoryCache: Map<string, CacheEntry<any>> = new Map();
  private config: CacheConfig;
  private readonly apiBaseUrl: string;

  private constructor(config: CacheConfig = DEFAULT_CACHE_CONFIG) {
    this.config = config;
    this.apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004';
    
    // Clean up expired entries periodically
    setInterval(() => this.cleanupExpiredEntries(), 60000); // Every minute
  }

  public static getInstance(config?: CacheConfig): CacheService {
    if (!CacheService.instance) {
      CacheService.instance = new CacheService(config);
    }
    return CacheService.instance;
  }

  /**
   * Get cached data with fallback hierarchy: Redis -> Memory -> LocalStorage
   */
  public async get<T>(key: string, ttl?: number): Promise<T | null> {
    const effectiveTtl = ttl || this.config.ttl;
    
    try {
      // Try Redis cache first (server-side caching)
      if (this.config.useRedisCache) {
        const redisData = await this.getFromRedis<T>(key);
        if (redisData !== null) {
          // Store in local caches for faster subsequent access
          this.storeInMemoryCache(key, redisData, effectiveTtl);
          this.storeInLocalStorage(key, redisData, effectiveTtl);
          return redisData;
        }
      }

      // Try memory cache
      if (this.config.useMemoryCache) {
        const memoryData = this.getFromMemoryCache<T>(key);
        if (memoryData !== null) {
          return memoryData;
        }
      }

      // Try localStorage
      if (this.config.useLocalStorage) {
        const localData = this.getFromLocalStorage<T>(key);
        if (localData !== null) {
          // Store in memory cache for faster access
          this.storeInMemoryCache(key, localData, effectiveTtl);
          return localData;
        }
      }

      return null;
    } catch (error) {
      console.error('Cache retrieval failed:', error);
      return null;
    }
  }

  /**
   * Store data in all enabled cache layers
   */
  public async set<T>(key: string, data: T, ttl?: number): Promise<void> {
    const effectiveTtl = ttl || this.config.ttl;

    try {
      // Store in Redis cache
      if (this.config.useRedisCache) {
        await this.storeInRedis(key, data, effectiveTtl);
      }

      // Store in memory cache
      if (this.config.useMemoryCache) {
        this.storeInMemoryCache(key, data, effectiveTtl);
      }

      // Store in localStorage
      if (this.config.useLocalStorage) {
        this.storeInLocalStorage(key, data, effectiveTtl);
      }
    } catch (error) {
      console.error('Cache storage failed:', error);
    }
  }

  /**
   * Invalidate cache entry across all layers
   */
  public async invalidate(key: string): Promise<void> {
    try {
      // Remove from Redis
      if (this.config.useRedisCache) {
        await this.removeFromRedis(key);
      }

      // Remove from memory cache
      if (this.config.useMemoryCache) {
        this.memoryCache.delete(key);
      }

      // Remove from localStorage
      if (this.config.useLocalStorage) {
        localStorage.removeItem(`cache_${key}`);
      }
    } catch (error) {
      console.error('Cache invalidation failed:', error);
    }
  }

  /**
   * Clear all cache layers
   */
  public async clear(): Promise<void> {
    try {
      // Clear Redis cache
      if (this.config.useRedisCache) {
        await this.clearRedisCache();
      }

      // Clear memory cache
      if (this.config.useMemoryCache) {
        this.memoryCache.clear();
      }

      // Clear localStorage cache
      if (this.config.useLocalStorage) {
        this.clearLocalStorageCache();
      }
    } catch (error) {
      console.error('Cache clear failed:', error);
    }
  }

  /**
   * Get or set pattern: retrieve from cache or fetch and cache
   */
  public async getOrSet<T>(
    key: string,
    fetchFunction: () => Promise<T>,
    ttl?: number
  ): Promise<T | null> {
    try {
      // Try to get from cache first
      const cachedData = await this.get<T>(key, ttl);
      if (cachedData !== null) {
        return cachedData;
      }

      // Fetch fresh data
      const freshData = await fetchFunction();
      
      // Cache the fresh data
      await this.set(key, freshData, ttl);
      
      return freshData;
    } catch (error) {
      console.error('GetOrSet failed:', error);
      return null;
    }
  }

  /**
   * Batch get multiple keys
   */
  public async getBatch<T>(keys: string[], ttl?: number): Promise<Map<string, T | null>> {
    const results = new Map<string, T | null>();
    
    await Promise.all(
      keys.map(async (key) => {
        const data = await this.get<T>(key, ttl);
        results.set(key, data);
      })
    );
    
    return results;
  }

  /**
   * Batch set multiple keys
   */
  public async setBatch<T>(entries: Map<string, T>, ttl?: number): Promise<void> {
    await Promise.all(
      Array.from(entries.entries()).map(([key, data]) =>
        this.set(key, data, ttl)
      )
    );
  }

  /**
   * Get cache statistics
   */
  public getStats(): {
    memoryCacheSize: number;
    localStorageCacheSize: number;
    memoryHitRate: number;
  } {
    const memoryCacheSize = this.memoryCache.size;
    const localStorageCacheSize = this.getLocalStorageCacheSize();
    
    return {
      memoryCacheSize,
      localStorageCacheSize,
      memoryHitRate: 0 // TODO: Implement hit rate tracking
    };
  }

  // Private methods

  private async getFromRedis<T>(key: string): Promise<T | null> {
    try {
      const headers = await authService.getAuthHeaders();
      const response = await fetch(`${this.apiBaseUrl}/api/v1/cache/${key}`, {
        headers,
        method: 'GET'
      });

      if (!response.ok) {
        return null;
      }

      const data = await response.json();
      return data.success ? data.data : null;
    } catch (error) {
      console.error('Redis cache retrieval failed:', error);
      return null;
    }
  }

  private async storeInRedis<T>(key: string, data: T, ttl: number): Promise<void> {
    try {
      const headers = await authService.getAuthHeaders();
      await fetch(`${this.apiBaseUrl}/api/v1/cache/${key}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ data, ttl })
      });
    } catch (error) {
      console.error('Redis cache storage failed:', error);
    }
  }

  private async removeFromRedis(key: string): Promise<void> {
    try {
      const headers = await authService.getAuthHeaders();
      await fetch(`${this.apiBaseUrl}/api/v1/cache/${key}`, {
        method: 'DELETE',
        headers
      });
    } catch (error) {
      console.error('Redis cache removal failed:', error);
    }
  }

  private async clearRedisCache(): Promise<void> {
    try {
      const headers = await authService.getAuthHeaders();
      await fetch(`${this.apiBaseUrl}/api/v1/cache/clear`, {
        method: 'POST',
        headers
      });
    } catch (error) {
      console.error('Redis cache clear failed:', error);
    }
  }

  private getFromMemoryCache<T>(key: string): T | null {
    const entry = this.memoryCache.get(key);
    if (!entry) {
      return null;
    }

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl * 1000) {
      this.memoryCache.delete(key);
      return null;
    }

    return entry.data;
  }

  private storeInMemoryCache<T>(key: string, data: T, ttl: number): void {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl,
      key
    };
    this.memoryCache.set(key, entry);
  }

  private getFromLocalStorage<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(`cache_${key}`);
      if (!item) {
        return null;
      }

      const entry: CacheEntry<T> = JSON.parse(item);
      const now = Date.now();
      
      if (now - entry.timestamp > entry.ttl * 1000) {
        localStorage.removeItem(`cache_${key}`);
        return null;
      }

      return entry.data;
    } catch (error) {
      console.error('localStorage cache retrieval failed:', error);
      return null;
    }
  }

  private storeInLocalStorage<T>(key: string, data: T, ttl: number): void {
    try {
      const entry: CacheEntry<T> = {
        data,
        timestamp: Date.now(),
        ttl,
        key
      };
      localStorage.setItem(`cache_${key}`, JSON.stringify(entry));
    } catch (error) {
      console.error('localStorage cache storage failed:', error);
    }
  }

  private getLocalStorageCacheSize(): number {
    try {
      let count = 0;
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('cache_')) {
          count++;
        }
      }
      return count;
    } catch (error) {
      return 0;
    }
  }

  private clearLocalStorageCache(): void {
    try {
      const keysToRemove: string[] = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('cache_')) {
          keysToRemove.push(key);
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key));
    } catch (error) {
      console.error('localStorage cache clear failed:', error);
    }
  }

  private cleanupExpiredEntries(): void {
    const now = Date.now();
    for (const [key, entry] of this.memoryCache.entries()) {
      if (now - entry.timestamp > entry.ttl * 1000) {
        this.memoryCache.delete(key);
      }
    }
  }
}

// Export singleton instance
export const cacheService = CacheService.getInstance();

// Export cache keys for consistency
export const CACHE_KEYS = {
  USER_DATA: 'user_data',
  DASHBOARD_KPI: 'dashboard_kpi',
  FINANCIAL_DATA: 'financial_data',
  MANUFACTURING_DATA: 'manufacturing_data',
  CASH_FLOW_PREDICTION: 'cash_flow_prediction',
  ANALYTICS_CHARTS: 'analytics_charts',
  BANKING_TRENDS: 'banking_trends',
  BUSINESS_PLANNING: 'business_planning',
  MODEL_PERFORMANCE: 'model_performance'
};