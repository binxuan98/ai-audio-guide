/**
 * 缓存管理工具
 * 提供内存缓存、本地存储缓存和智能缓存策略
 */

const config = require('./config.js');
const { logger } = require('./logger.js');

class CacheManager {
  constructor() {
    this.memoryCache = new Map();
    this.cacheStats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0
    };
  }

  /**
   * 生成缓存键
   * @param {string} prefix 前缀
   * @param {any} params 参数
   * @returns {string} 缓存键
   */
  generateKey(prefix, params = {}) {
    const paramStr = JSON.stringify(params, Object.keys(params).sort());
    return `${prefix}_${this.hashCode(paramStr)}`;
  }

  /**
   * 简单哈希函数
   * @param {string} str 字符串
   * @returns {string} 哈希值
   */
  hashCode(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // 转换为32位整数
    }
    return Math.abs(hash).toString(36);
  }

  /**
   * 设置内存缓存
   * @param {string} key 缓存键
   * @param {any} value 缓存值
   * @param {number} ttl 过期时间（毫秒）
   */
  setMemory(key, value, ttl = config.CACHE.MEMORY_TTL) {
    const expireTime = Date.now() + ttl;
    this.memoryCache.set(key, {
      value,
      expireTime,
      accessCount: 0,
      lastAccess: Date.now()
    });
    
    this.cacheStats.sets++;
    logger.debug('内存缓存设置', { key, ttl });
    
    // 清理过期缓存
    this.cleanExpiredMemoryCache();
  }

  /**
   * 获取内存缓存
   * @param {string} key 缓存键
   * @returns {any} 缓存值或null
   */
  getMemory(key) {
    const cached = this.memoryCache.get(key);
    
    if (!cached) {
      this.cacheStats.misses++;
      return null;
    }
    
    if (Date.now() > cached.expireTime) {
      this.memoryCache.delete(key);
      this.cacheStats.misses++;
      logger.debug('内存缓存过期', { key });
      return null;
    }
    
    // 更新访问统计
    cached.accessCount++;
    cached.lastAccess = Date.now();
    
    this.cacheStats.hits++;
    logger.debug('内存缓存命中', { key, accessCount: cached.accessCount });
    
    return cached.value;
  }

  /**
   * 设置本地存储缓存
   * @param {string} key 缓存键
   * @param {any} value 缓存值
   * @param {number} ttl 过期时间（毫秒）
   */
  async setStorage(key, value, ttl = config.CACHE.STORAGE_TTL) {
    try {
      const cacheData = {
        value,
        expireTime: Date.now() + ttl,
        createTime: Date.now()
      };
      
      await this.setStorageSync(key, cacheData);
      logger.debug('本地缓存设置', { key, ttl });
    } catch (error) {
      logger.error('设置本地缓存失败', error);
    }
  }

  /**
   * 获取本地存储缓存
   * @param {string} key 缓存键
   * @returns {any} 缓存值或null
   */
  async getStorage(key) {
    try {
      const cached = await this.getStorageSync(key);
      
      if (!cached) {
        return null;
      }
      
      if (Date.now() > cached.expireTime) {
        await this.removeStorage(key);
        logger.debug('本地缓存过期', { key });
        return null;
      }
      
      logger.debug('本地缓存命中', { key });
      return cached.value;
    } catch (error) {
      logger.error('获取本地缓存失败', error);
      return null;
    }
  }

  /**
   * 智能缓存获取
   * 先查内存缓存，再查本地缓存
   * @param {string} key 缓存键
   * @returns {any} 缓存值或null
   */
  async get(key) {
    // 先查内存缓存
    let value = this.getMemory(key);
    if (value !== null) {
      return value;
    }
    
    // 再查本地缓存
    value = await this.getStorage(key);
    if (value !== null) {
      // 将本地缓存提升到内存缓存
      this.setMemory(key, value, config.CACHE.MEMORY_TTL);
      return value;
    }
    
    return null;
  }

  /**
   * 智能缓存设置
   * 同时设置内存缓存和本地缓存
   * @param {string} key 缓存键
   * @param {any} value 缓存值
   * @param {object} options 选项
   */
  async set(key, value, options = {}) {
    const {
      memoryTTL = config.CACHE.MEMORY_TTL,
      storageTTL = config.CACHE.STORAGE_TTL,
      memoryOnly = false,
      storageOnly = false
    } = options;
    
    if (!storageOnly) {
      this.setMemory(key, value, memoryTTL);
    }
    
    if (!memoryOnly) {
      await this.setStorage(key, value, storageTTL);
    }
  }

  /**
   * 删除缓存
   * @param {string} key 缓存键
   */
  async remove(key) {
    this.memoryCache.delete(key);
    await this.removeStorage(key);
    this.cacheStats.deletes++;
    logger.debug('缓存删除', { key });
  }

  /**
   * 清理过期的内存缓存
   */
  cleanExpiredMemoryCache() {
    const now = Date.now();
    const expiredKeys = [];
    
    for (const [key, cached] of this.memoryCache.entries()) {
      if (now > cached.expireTime) {
        expiredKeys.push(key);
      }
    }
    
    expiredKeys.forEach(key => {
      this.memoryCache.delete(key);
    });
    
    if (expiredKeys.length > 0) {
      logger.debug('清理过期内存缓存', { count: expiredKeys.length });
    }
  }

  /**
   * 清理所有缓存
   */
  async clear() {
    this.memoryCache.clear();
    
    try {
      const info = await this.getStorageInfoSync();
      const cacheKeys = info.keys.filter(key => key.startsWith('cache_'));
      
      for (const key of cacheKeys) {
        await this.removeStorage(key);
      }
      
      logger.info('缓存清理完成', { memoryCount: 0, storageCount: cacheKeys.length });
    } catch (error) {
      logger.error('清理本地缓存失败', error);
    }
    
    // 重置统计
    this.cacheStats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0
    };
  }

  /**
   * 获取缓存统计
   * @returns {object} 统计信息
   */
  getStats() {
    const hitRate = this.cacheStats.hits + this.cacheStats.misses > 0 
      ? (this.cacheStats.hits / (this.cacheStats.hits + this.cacheStats.misses) * 100).toFixed(2)
      : 0;
    
    return {
      ...this.cacheStats,
      hitRate: `${hitRate}%`,
      memorySize: this.memoryCache.size
    };
  }

  /**
   * 缓存装饰器
   * @param {string} prefix 缓存前缀
   * @param {object} options 选项
   * @returns {function} 装饰器函数
   */
  cached(prefix, options = {}) {
    return (target, propertyName, descriptor) => {
      const originalMethod = descriptor.value;
      
      descriptor.value = async function(...args) {
        const key = this.generateKey(prefix, args);
        
        // 尝试从缓存获取
        let result = await this.get(key);
        if (result !== null) {
          logger.debug('缓存命中', { method: propertyName, key });
          return result;
        }
        
        // 执行原方法
        result = await originalMethod.apply(this, args);
        
        // 缓存结果
        if (result !== null && result !== undefined) {
          await this.set(key, result, options);
          logger.debug('缓存设置', { method: propertyName, key });
        }
        
        return result;
      }.bind(this);
      
      return descriptor;
    };
  }

  // 微信小程序存储API封装
  setStorageSync(key, data) {
    return new Promise((resolve, reject) => {
      wx.setStorage({
        key: `cache_${key}`,
        data,
        success: resolve,
        fail: reject
      });
    });
  }

  getStorageSync(key) {
    return new Promise((resolve, reject) => {
      wx.getStorage({
        key: `cache_${key}`,
        success: (res) => resolve(res.data),
        fail: () => resolve(null)
      });
    });
  }

  removeStorage(key) {
    return new Promise((resolve, reject) => {
      wx.removeStorage({
        key: `cache_${key}`,
        success: resolve,
        fail: resolve // 删除失败也认为成功
      });
    });
  }

  getStorageInfoSync() {
    return new Promise((resolve, reject) => {
      wx.getStorageInfo({
        success: resolve,
        fail: reject
      });
    });
  }
}

// 特定业务缓存类
class BusinessCache {
  static getCacheManager() {
    if (!this._cacheManager) {
      this._cacheManager = new CacheManager();
    }
    return this._cacheManager;
  }
  /**
   * 缓存用户位置
   * @param {object} location 位置信息
   */
  static async cacheUserLocation(location) {
    const key = 'user_location';
    const manager = this.getCacheManager();
    await manager.set(key, location, {
      memoryTTL: 5 * 60 * 1000, // 5分钟
      storageTTL: 30 * 60 * 1000 // 30分钟
    });
  }

  /**
   * 获取缓存的用户位置
   * @returns {object|null} 位置信息
   */
  static async getCachedUserLocation() {
    const manager = this.getCacheManager();
    return await manager.get('user_location');
  }

  /**
   * 缓存讲解风格
   * @param {array} styles 风格列表
   */
  static async cacheGuideStyles(styles) {
    const key = 'guide_styles';
    const manager = this.getCacheManager();
    await manager.set(key, styles, {
      memoryTTL: 60 * 60 * 1000, // 1小时
      storageTTL: 24 * 60 * 60 * 1000 // 24小时
    });
  }

  /**
   * 获取缓存的讲解风格
   * @returns {array|null} 风格列表
   */
  static async getCachedGuideStyles() {
    const manager = this.getCacheManager();
    return await manager.get('guide_styles');
  }

  /**
   * 缓存周边景点
   * @param {object} location 位置
   * @param {array} spots 景点列表
   */
  static async cacheNearbySpots(location, spots) {
    const manager = this.getCacheManager();
    const key = manager.generateKey('nearby_spots', {
      lat: Math.round(location.latitude * 1000) / 1000, // 精确到3位小数
      lng: Math.round(location.longitude * 1000) / 1000
    });
    
    await manager.set(key, spots, {
      memoryTTL: 10 * 60 * 1000, // 10分钟
      storageTTL: 60 * 60 * 1000 // 1小时
    });
  }

  /**
   * 获取缓存的周边景点
   * @param {object} location 位置
   * @returns {array|null} 景点列表
   */
  static async getCachedNearbySpots(location) {
    const manager = this.getCacheManager();
    const key = manager.generateKey('nearby_spots', {
      lat: Math.round(location.latitude * 1000) / 1000,
      lng: Math.round(location.longitude * 1000) / 1000
    });
    
    return await manager.get(key);
  }

  /**
   * 缓存讲解内容
   * @param {object} params 请求参数
   * @param {object} guide 讲解内容
   */
  static async cacheGuideContent(params, guide) {
    const manager = this.getCacheManager();
    const key = manager.generateKey('guide_content', params);
    
    await manager.set(key, guide, {
      memoryTTL: 30 * 60 * 1000, // 30分钟
      storageTTL: 7 * 24 * 60 * 60 * 1000 // 7天
    });
  }

  /**
   * 获取缓存的讲解内容
   * @param {object} params 请求参数
   * @returns {object|null} 讲解内容
   */
  static async getCachedGuideContent(params) {
    const manager = this.getCacheManager();
    const key = manager.generateKey('guide_content', params);
    return await manager.get(key);
  }
}

// 创建全局实例
const cacheManager = new CacheManager();

module.exports = {
  cacheManager,
  CacheManager,
  BusinessCache,
  
  // 便捷方法
  get: (...args) => cacheManager.get(...args),
  set: (...args) => cacheManager.set(...args),
  remove: (...args) => cacheManager.remove(...args),
  clear: (...args) => cacheManager.clear(...args),
  getStats: (...args) => cacheManager.getStats(...args)
};