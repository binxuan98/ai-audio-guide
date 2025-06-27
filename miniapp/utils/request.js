/**
 * 网络请求工具
 * 统一处理API请求，包含重试机制、错误处理、性能监控
 */

const config = require('./config.js');
const { performanceMonitor } = require('./performance.js');

class RequestManager {
  constructor() {
    this.requestCount = 0;
    this.pendingRequests = new Map();
  }

  /**
   * 发起请求
   * @param {object} options 请求选项
   * @returns {Promise} 请求Promise
   */
  async request(options) {
    const requestId = ++this.requestCount;
    const startTime = Date.now();
    
    // 性能监控
    const monitorKey = `request_${requestId}_${options.url}`;
    performanceMonitor.start(monitorKey);
    
    // 默认配置
    const defaultOptions = {
      method: 'GET',
      timeout: config.API.TIMEOUT,
      header: {
        'Content-Type': 'application/json'
      }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    // 如果是开发环境且启用模拟数据
    if (config.FEATURES.USE_MOCK_DATA) {
      return this.getMockData(finalOptions);
    }
    
    // 构建完整URL
    if (!finalOptions.url.startsWith('http')) {
      finalOptions.url = config.getApiUrl(finalOptions.url);
    }
    
    config.log('发起请求:', finalOptions);
    
    try {
      const result = await this.executeRequest(finalOptions, requestId);
      performanceMonitor.end(monitorKey);
      return result;
    } catch (error) {
      performanceMonitor.end(monitorKey);
      config.warn('请求失败:', error);
      throw error;
    }
  }
  
  /**
   * 执行请求
   * @param {object} options 请求选项
   * @param {number} requestId 请求ID
   * @returns {Promise} 请求结果
   */
  executeRequest(options, requestId) {
    return new Promise((resolve, reject) => {
      const requestTask = wx.request({
        ...options,
        success: (res) => {
          this.pendingRequests.delete(requestId);
          
          if (res.statusCode >= 200 && res.statusCode < 300) {
            config.log('请求成功:', res);
            resolve(res);
          } else {
            const error = new Error(`HTTP ${res.statusCode}: ${res.errMsg}`);
            error.statusCode = res.statusCode;
            error.response = res;
            reject(error);
          }
        },
        fail: (err) => {
          this.pendingRequests.delete(requestId);
          config.warn('请求失败:', err);
          
          const error = new Error(err.errMsg || '网络请求失败');
          error.code = err.errno;
          error.originalError = err;
          reject(error);
        }
      });
      
      // 保存请求任务，用于取消
      this.pendingRequests.set(requestId, requestTask);
    });
  }
  
  /**
   * 带重试机制的请求
   * @param {object} options 请求选项
   * @param {number} maxRetries 最大重试次数
   * @returns {Promise} 请求结果
   */
  async requestWithRetry(options, maxRetries = config.PERFORMANCE.MAX_RETRY_COUNT) {
    let lastError;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        if (attempt > 0) {
          // 指数退避延迟
          const delay = config.PERFORMANCE.RETRY_DELAY_BASE * Math.pow(2, attempt - 1);
          config.log(`第${attempt}次重试，延迟${delay}ms`);
          await this.delay(delay);
        }
        
        const result = await this.request(options);
        
        if (attempt > 0) {
          config.log(`重试成功，尝试次数: ${attempt}`);
        }
        
        return result;
      } catch (error) {
        lastError = error;
        config.warn(`请求失败 (尝试 ${attempt + 1}/${maxRetries + 1}):`, error.message);
        
        // 如果是最后一次尝试，或者是不可重试的错误，直接抛出
        if (attempt === maxRetries || !this.isRetryableError(error)) {
          break;
        }
      }
    }
    
    throw lastError;
  }
  
  /**
   * 判断错误是否可重试
   * @param {Error} error 错误对象
   * @returns {boolean} 是否可重试
   */
  isRetryableError(error) {
    // 网络错误、超时错误可重试
    if (error.message.includes('timeout') || 
        error.message.includes('network') ||
        error.message.includes('fail')) {
      return true;
    }
    
    // 5xx服务器错误可重试
    if (error.statusCode >= 500) {
      return true;
    }
    
    // 4xx客户端错误不重试
    return false;
  }
  
  /**
   * 延迟函数
   * @param {number} ms 延迟毫秒数
   * @returns {Promise} 延迟Promise
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  /**
   * 获取模拟数据
   * @param {object} options 请求选项
   * @returns {Promise} 模拟数据
   */
  async getMockData(options) {
    config.log('使用模拟数据:', options.url);
    
    // 模拟网络延迟
    await this.delay(500 + Math.random() * 1000);
    
    // 根据URL返回不同的模拟数据
    if (options.url.includes('/guide/styles')) {
      return {
        statusCode: 200,
        data: {
          styles: [
            { name: '历史文化', description: '深度解读历史背景' },
            { name: '趣闻轶事', description: '有趣的故事和传说' },
            { name: '诗词文学', description: '诗词歌赋的文学魅力' },
            { name: '人物故事', description: '历史人物的精彩故事' }
          ]
        }
      };
    }
    
    if (options.url.includes('/spots/nearby')) {
      return {
        statusCode: 200,
        data: {
          spots: [
            {
              id: 1,
              name: '模拟景点1',
              latitude: 39.9042,
              longitude: 116.4074,
              description: '这是一个模拟的景点'
            },
            {
              id: 2,
              name: '模拟景点2', 
              latitude: 39.9052,
              longitude: 116.4084,
              description: '这是另一个模拟的景点'
            }
          ]
        }
      };
    }
    
    if (options.url.includes('/guide')) {
      return {
        statusCode: 200,
        data: {
          text: `这是${options.data?.style || '默认'}风格的模拟讲解内容。在实际项目中，这里会是AI生成的真实讲解内容。`,
          audio_url: 'https://example.com/mock-audio.mp3'
        }
      };
    }
    
    // 默认返回
    return {
      statusCode: 200,
      data: { message: '模拟数据' }
    };
  }
  
  /**
   * 取消所有待处理的请求
   */
  cancelAllRequests() {
    this.pendingRequests.forEach((task, id) => {
      try {
        task.abort();
        config.log(`取消请求: ${id}`);
      } catch (e) {
        config.warn(`取消请求失败: ${id}`, e);
      }
    });
    this.pendingRequests.clear();
  }
  
  /**
   * 获取待处理请求数量
   * @returns {number} 待处理请求数量
   */
  getPendingRequestCount() {
    return this.pendingRequests.size;
  }
}

// 创建全局实例
const requestManager = new RequestManager();

module.exports = {
  requestManager,
  RequestManager,
  
  // 便捷方法
  request: (options) => requestManager.request(options),
  requestWithRetry: (options, maxRetries) => requestManager.requestWithRetry(options, maxRetries),
  
  // GET请求
  get: (url, data = {}) => requestManager.request({ url, method: 'GET', data }),
  
  // POST请求
  post: (url, data = {}) => requestManager.request({ url, method: 'POST', data }),
  
  // 带重试的GET请求
  getWithRetry: (url, data = {}, maxRetries) => 
    requestManager.requestWithRetry({ url, method: 'GET', data }, maxRetries),
  
  // 带重试的POST请求
  postWithRetry: (url, data = {}, maxRetries) => 
    requestManager.requestWithRetry({ url, method: 'POST', data }, maxRetries)
};