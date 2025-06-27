/**
 * 性能监控工具
 * 用于监控小程序性能指标
 */

class PerformanceMonitor {
  constructor() {
    this.metrics = {};
    this.startTimes = {};
  }

  /**
   * 开始计时
   * @param {string} name 指标名称
   */
  start(name) {
    this.startTimes[name] = Date.now();
    console.log(`[性能监控] ${name} 开始`);
  }

  /**
   * 结束计时
   * @param {string} name 指标名称
   * @returns {number} 耗时（毫秒）
   */
  end(name) {
    if (!this.startTimes[name]) {
      console.warn(`[性能监控] ${name} 未找到开始时间`);
      return 0;
    }

    const duration = Date.now() - this.startTimes[name];
    this.metrics[name] = duration;
    delete this.startTimes[name];

    console.log(`[性能监控] ${name} 完成，耗时: ${duration}ms`);
    
    // 性能警告 - 为不同操作设置不同阈值
    const thresholds = {
      'audio_play': 2000,      // 音频播放允许2秒
      'get_nearby_spots': 3000, // 获取景点允许3秒
      'generate_guide': 5000,   // 生成讲解允许5秒
      'default': 1000          // 其他操作1秒
    };
    
    const threshold = thresholds[name] || thresholds.default;
    if (duration > threshold) {
      console.warn(`[性能警告] ${name} 耗时过长: ${duration}ms (阈值: ${threshold}ms)`);
    }

    return duration;
  }

  /**
   * 获取所有指标
   * @returns {object} 性能指标对象
   */
  getMetrics() {
    return { ...this.metrics };
  }

  /**
   * 清除所有指标
   */
  clear() {
    this.metrics = {};
    this.startTimes = {};
  }

  /**
   * 记录自定义指标
   * @param {string} name 指标名称
   * @param {number} value 指标值
   */
  record(name, value) {
    this.metrics[name] = value;
    console.log(`[性能监控] ${name}: ${value}`);
  }
}

// 创建全局实例
const performanceMonitor = new PerformanceMonitor();

module.exports = {
  performanceMonitor,
  PerformanceMonitor
};