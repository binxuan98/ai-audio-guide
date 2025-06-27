/**
 * 日志记录和错误处理工具
 * 统一管理日志输出、错误上报、用户反馈
 */

const config = require('./config.js');

class Logger {
  constructor() {
    this.logs = [];
    this.maxLogs = 100; // 最大日志条数
    this.errorCount = 0;
    this.warningCount = 0;
  }

  /**
   * 记录日志
   * @param {string} level 日志级别
   * @param {string} message 日志消息
   * @param {any} data 附加数据
   */
  log(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      data,
      page: this.getCurrentPage()
    };

    // 添加到日志队列
    this.logs.push(logEntry);
    
    // 保持日志队列大小
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // 控制台输出（仅在调试模式）
    if (config.isDebug()) {
      const consoleMethod = this.getConsoleMethod(level);
      const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
      
      if (data) {
        consoleMethod(prefix, message, data);
      } else {
        consoleMethod(prefix, message);
      }
    }

    // 统计错误和警告
    if (level === 'error') {
      this.errorCount++;
    } else if (level === 'warn') {
      this.warningCount++;
    }

    // 错误上报（生产环境）
    if (level === 'error' && !config.isDev()) {
      this.reportError(logEntry);
    }
  }

  /**
   * 信息日志
   * @param {string} message 消息
   * @param {any} data 数据
   */
  info(message, data) {
    this.log('info', message, data);
  }

  /**
   * 警告日志
   * @param {string} message 消息
   * @param {any} data 数据
   */
  warn(message, data) {
    this.log('warn', message, data);
  }

  /**
   * 错误日志
   * @param {string} message 消息
   * @param {any} error 错误对象
   */
  error(message, error) {
    const errorData = this.formatError(error);
    this.log('error', message, errorData);
  }

  /**
   * 调试日志
   * @param {string} message 消息
   * @param {any} data 数据
   */
  debug(message, data) {
    if (config.isDebug()) {
      this.log('debug', message, data);
    }
  }

  /**
   * 性能日志
   * @param {string} operation 操作名称
   * @param {number} duration 耗时
   * @param {any} data 附加数据
   */
  performance(operation, duration, data) {
    this.log('performance', `${operation} 耗时: ${duration}ms`, data);
    
    // 性能警告
    if (duration > 2000) {
      this.warn(`性能警告: ${operation} 耗时过长`, { duration, data });
    }
  }

  /**
   * 用户行为日志
   * @param {string} action 用户行为
   * @param {any} data 行为数据
   */
  userAction(action, data) {
    this.log('user', action, data);
  }

  /**
   * 获取当前页面路径
   * @returns {string} 页面路径
   */
  getCurrentPage() {
    try {
      const pages = getCurrentPages();
      if (pages.length > 0) {
        return pages[pages.length - 1].route;
      }
    } catch (e) {
      // 忽略错误
    }
    return 'unknown';
  }

  /**
   * 获取控制台输出方法
   * @param {string} level 日志级别
   * @returns {function} 控制台方法
   */
  getConsoleMethod(level) {
    switch (level) {
      case 'error':
        return console.error;
      case 'warn':
        return console.warn;
      case 'debug':
        return console.debug || console.log;
      case 'performance':
      case 'user':
      case 'info':
      default:
        return console.log;
    }
  }

  /**
   * 格式化错误对象
   * @param {any} error 错误
   * @returns {object} 格式化后的错误信息
   */
  formatError(error) {
    if (!error) return null;

    if (error instanceof Error) {
      return {
        name: error.name,
        message: error.message,
        stack: error.stack,
        code: error.code,
        statusCode: error.statusCode
      };
    }

    if (typeof error === 'string') {
      return { message: error };
    }

    return error;
  }

  /**
   * 错误上报
   * @param {object} logEntry 日志条目
   */
  reportError(logEntry) {
    try {
      // 这里可以集成第三方错误监控服务
      // 例如：Sentry, Bugsnag 等
      
      // 简单的错误统计
      wx.reportAnalytics && wx.reportAnalytics('error', {
        message: logEntry.message,
        page: logEntry.page,
        timestamp: logEntry.timestamp
      });
    } catch (e) {
      // 错误上报失败，忽略
    }
  }

  /**
   * 获取日志统计
   * @returns {object} 统计信息
   */
  getStats() {
    return {
      totalLogs: this.logs.length,
      errorCount: this.errorCount,
      warningCount: this.warningCount,
      lastError: this.logs.filter(log => log.level === 'error').pop(),
      lastWarning: this.logs.filter(log => log.level === 'warn').pop()
    };
  }

  /**
   * 获取最近的日志
   * @param {number} count 日志数量
   * @param {string} level 日志级别过滤
   * @returns {array} 日志列表
   */
  getRecentLogs(count = 10, level = null) {
    let logs = this.logs;
    
    if (level) {
      logs = logs.filter(log => log.level === level);
    }
    
    return logs.slice(-count);
  }

  /**
   * 清除日志
   */
  clear() {
    this.logs = [];
    this.errorCount = 0;
    this.warningCount = 0;
  }

  /**
   * 导出日志（用于调试）
   * @returns {string} 日志JSON字符串
   */
  export() {
    return JSON.stringify({
      stats: this.getStats(),
      logs: this.logs
    }, null, 2);
  }
}

// 创建全局实例
const logger = new Logger();

// 错误处理工具
class ErrorHandler {
  /**
   * 处理并显示错误
   * @param {string} message 用户友好的错误消息
   * @param {any} error 原始错误
   * @param {object} options 选项
   */
  static handle(message, error = null, options = {}) {
    const {
      showToast = true,
      duration = 2000,
      icon = 'none',
      logLevel = 'error'
    } = options;

    // 记录日志
    if (logLevel === 'error') {
      logger.error(message, error);
    } else if (logLevel === 'warn') {
      logger.warn(message, error);
    } else {
      logger.info(message, error);
    }

    // 显示用户提示
    if (showToast) {
      wx.showToast({
        title: message,
        icon,
        duration
      });
    }
  }

  /**
   * 处理网络错误
   * @param {any} error 网络错误
   * @param {string} operation 操作名称
   */
  static handleNetworkError(error, operation = '网络请求') {
    let message = `${operation}失败`;
    
    if (error.message) {
      if (error.message.includes('timeout')) {
        message = '请求超时，请检查网络连接';
      } else if (error.message.includes('network')) {
        message = '网络连接失败，请检查网络设置';
      } else if (error.statusCode >= 500) {
        message = '服务器暂时不可用，请稍后重试';
      } else if (error.statusCode >= 400) {
        message = '请求参数错误';
      }
    }
    
    this.handle(message, error);
  }

  /**
   * 处理权限错误
   * @param {string} permission 权限名称
   * @param {any} error 错误信息
   */
  static handlePermissionError(permission, error) {
    const message = `需要${permission}权限才能使用此功能`;
    this.handle(message, error, { logLevel: 'warn' });
  }
}

module.exports = {
  logger,
  Logger,
  ErrorHandler,
  
  // 便捷方法
  log: (...args) => logger.info(...args),
  warn: (...args) => logger.warn(...args),
  error: (...args) => logger.error(...args),
  debug: (...args) => logger.debug(...args),
  performance: (...args) => logger.performance(...args),
  userAction: (...args) => logger.userAction(...args),
  
  // 错误处理便捷方法
  handleError: (...args) => ErrorHandler.handle(...args),
  handleNetworkError: (...args) => ErrorHandler.handleNetworkError(...args),
  handlePermissionError: (...args) => ErrorHandler.handlePermissionError(...args)
};