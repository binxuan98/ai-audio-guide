/**
 * 音频管理工具
 * 统一管理音频播放、状态控制和错误处理
 */

const config = require('./config.js');
const { logger, handleError } = require('./logger.js');
const { performanceMonitor } = require('./performance.js');

class AudioManager {
  constructor() {
    this.context = null;
    this.isPlaying = false;
    this.currentAudio = null;
    this.playbackHistory = [];
    this.maxHistorySize = 10;
  }

  /**
   * 初始化音频上下文
   * @returns {Promise<wx.InnerAudioContext>} 音频上下文
   */
  async init() {
    if (this.context) {
      logger.debug('音频上下文已存在，跳过初始化');
      return this.context;
    }

    try {
      performanceMonitor.start('audio_init');
      
      this.context = wx.createInnerAudioContext();
      
      // 设置音频属性
      this.context.autoplay = false;
      this.context.loop = false;
      this.context.volume = config.AUDIO.DEFAULT_VOLUME || 1.0;
      this.context.playbackRate = config.AUDIO.DEFAULT_PLAYBACK_RATE || 1.0;
      
      // 绑定事件监听
      this.bindEvents();
      
      const initTime = performanceMonitor.end('audio_init');
      logger.performance('音频初始化', initTime);
      logger.info('音频上下文初始化成功');
      
      return this.context;
    } catch (error) {
      performanceMonitor.end('audio_init');
      logger.error('音频上下文初始化失败', error);
      throw error;
    }
  }

  /**
   * 绑定音频事件
   */
  bindEvents() {
    if (!this.context) return;

    // 播放开始
    this.context.onPlay(() => {
      this.isPlaying = true;
      logger.info('音频开始播放');
      this.notifyStateChange('play');
    });

    // 播放暂停
    this.context.onPause(() => {
      this.isPlaying = false;
      logger.info('音频暂停播放');
      this.notifyStateChange('pause');
    });

    // 播放结束
    this.context.onEnded(() => {
      this.isPlaying = false;
      logger.info('音频播放结束');
      this.addToHistory(this.currentAudio);
      this.notifyStateChange('ended');
    });

    // 播放错误
    this.context.onError((error) => {
      this.isPlaying = false;
      logger.error('音频播放错误', error);
      this.notifyStateChange('error', error);
    });

    // 音频加载完成
    this.context.onCanplay(() => {
      logger.debug('音频可以播放');
      this.notifyStateChange('canplay');
    });

    // 音频缓冲中
    this.context.onWaiting(() => {
      logger.debug('音频缓冲中');
      this.notifyStateChange('waiting');
    });

    // 音频时间更新
    this.context.onTimeUpdate(() => {
      this.notifyStateChange('timeupdate', {
        currentTime: this.context.currentTime,
        duration: this.context.duration
      });
    });
  }

  /**
   * 播放音频
   * @param {string} audioUrl 音频URL
   * @param {object} options 播放选项
   * @returns {Promise<void>}
   */
  async play(audioUrl, options = {}) {
    if (!this.context) {
      await this.init();
    }

    const {
      title = '音频',
      autoRetry = true,
      maxRetries = config.AUDIO.MAX_RETRIES || 3
    } = options;

    try {
      performanceMonitor.start('audio_play');
      
      // 如果是新的音频源，更新src
      if (this.context.src !== audioUrl) {
        this.context.src = audioUrl;
        this.currentAudio = {
          url: audioUrl,
          title,
          startTime: Date.now()
        };
        logger.info('设置新的音频源', { url: audioUrl, title });
      }

      // 等待音频准备就绪并播放
      await this.waitForCanplay();
      
      this.context.play();
      
      const playTime = performanceMonitor.end('audio_play');
      logger.performance('音频播放启动', playTime);
      
    } catch (error) {
      performanceMonitor.end('audio_play');
      
      if (autoRetry && maxRetries > 0) {
        logger.warn('音频播放失败，尝试重试', error);
        await new Promise(resolve => setTimeout(resolve, 1000));
        return this.play(audioUrl, { ...options, maxRetries: maxRetries - 1 });
      }
      
      logger.error('音频播放失败', error);
      throw error;
    }
  }

  /**
   * 暂停音频
   */
  pause() {
    if (!this.context) {
      logger.warn('音频上下文未初始化');
      return;
    }

    try {
      this.context.pause();
      logger.info('音频已暂停');
    } catch (error) {
      logger.error('暂停音频失败', error);
      throw error;
    }
  }

  /**
   * 停止音频
   */
  stop() {
    if (!this.context) {
      logger.warn('音频上下文未初始化');
      return;
    }

    try {
      this.context.stop();
      this.isPlaying = false;
      logger.info('音频已停止');
    } catch (error) {
      logger.error('停止音频失败', error);
      throw error;
    }
  }

  /**
   * 切换播放状态
   */
  toggle() {
    if (!this.context) {
      logger.warn('音频上下文未初始化');
      return;
    }

    if (this.isPlaying) {
      this.pause();
    } else {
      if (this.context.src) {
        this.context.play();
      } else {
        logger.warn('没有音频源可播放');
      }
    }
  }

  /**
   * 设置音量
   * @param {number} volume 音量 (0-1)
   */
  setVolume(volume) {
    if (!this.context) {
      logger.warn('音频上下文未初始化');
      return;
    }

    const clampedVolume = Math.max(0, Math.min(1, volume));
    this.context.volume = clampedVolume;
    logger.debug('设置音量', { volume: clampedVolume });
  }

  /**
   * 设置播放速度
   * @param {number} rate 播放速度 (0.5-2.0)
   */
  setPlaybackRate(rate) {
    if (!this.context) {
      logger.warn('音频上下文未初始化');
      return;
    }

    const clampedRate = Math.max(0.5, Math.min(2.0, rate));
    this.context.playbackRate = clampedRate;
    logger.debug('设置播放速度', { rate: clampedRate });
  }

  /**
   * 跳转到指定时间
   * @param {number} time 时间（秒）
   */
  seek(time) {
    if (!this.context) {
      logger.warn('音频上下文未初始化');
      return;
    }

    try {
      this.context.seek(time);
      logger.debug('跳转到指定时间', { time });
    } catch (error) {
      logger.error('音频跳转失败', error);
      throw error;
    }
  }

  /**
   * 获取播放状态
   * @returns {object} 播放状态
   */
  getState() {
    if (!this.context) {
      return {
        isPlaying: false,
        currentTime: 0,
        duration: 0,
        src: null
      };
    }

    return {
      isPlaying: this.isPlaying,
      currentTime: this.context.currentTime || 0,
      duration: this.context.duration || 0,
      src: this.context.src,
      volume: this.context.volume,
      playbackRate: this.context.playbackRate
    };
  }

  /**
   * 等待音频可播放
   * @returns {Promise<void>}
   */
  waitForCanplay() {
    return new Promise((resolve, reject) => {
      if (!this.context) {
        reject(new Error('音频上下文未初始化'));
        return;
      }

      // 如果音频已经可以播放，直接resolve
      if (this.context.readyState >= 3) { // HAVE_FUTURE_DATA
        resolve();
        return;
      }

      const timeout = setTimeout(() => {
        this.context.offCanplay(onCanplay);
        this.context.offError(onError);
        this.context.offWaiting && this.context.offWaiting(onWaiting);
        reject(new Error('音频加载超时'));
      }, config.AUDIO.LOAD_TIMEOUT || 15000);

      const onCanplay = () => {
        clearTimeout(timeout);
        this.context.offCanplay(onCanplay);
        this.context.offError(onError);
        this.context.offWaiting && this.context.offWaiting(onWaiting);
        logger.info('音频加载完成，可以播放');
        resolve();
      };

      const onError = (error) => {
        clearTimeout(timeout);
        this.context.offCanplay(onCanplay);
        this.context.offError(onError);
        this.context.offWaiting && this.context.offWaiting(onWaiting);
        logger.error('音频加载出错', error);
        reject(error);
      };

      const onWaiting = () => {
        logger.info('音频缓冲中...');
      };

      this.context.onCanplay(onCanplay);
      this.context.onError(onError);
      this.context.onWaiting && this.context.onWaiting(onWaiting);
      
      // 尝试预加载
      if (config.AUDIO.PRELOAD) {
        this.context.load && this.context.load();
      }
    });
  }

  /**
   * 添加到播放历史
   * @param {object} audio 音频信息
   */
  addToHistory(audio) {
    if (!audio) return;

    const historyItem = {
      ...audio,
      endTime: Date.now(),
      duration: audio.startTime ? Date.now() - audio.startTime : 0
    };

    this.playbackHistory.unshift(historyItem);
    
    // 保持历史记录大小
    if (this.playbackHistory.length > this.maxHistorySize) {
      this.playbackHistory = this.playbackHistory.slice(0, this.maxHistorySize);
    }

    logger.debug('添加播放历史', historyItem);
  }

  /**
   * 获取播放历史
   * @returns {array} 播放历史
   */
  getHistory() {
    return [...this.playbackHistory];
  }

  /**
   * 清除播放历史
   */
  clearHistory() {
    this.playbackHistory = [];
    logger.info('播放历史已清除');
  }

  /**
   * 状态变化通知
   * @param {string} event 事件类型
   * @param {any} data 事件数据
   */
  notifyStateChange(event, data = null) {
    // 可以在这里添加状态变化的回调通知
    // 例如：通知页面更新UI状态
    if (this.onStateChange) {
      this.onStateChange(event, data);
    }
  }

  /**
   * 设置状态变化回调
   * @param {function} callback 回调函数
   */
  setStateChangeCallback(callback) {
    this.onStateChange = callback;
  }

  /**
   * 销毁音频管理器
   */
  destroy() {
    if (this.context) {
      try {
        this.context.stop();
        this.context.destroy();
        logger.info('音频上下文已销毁');
      } catch (error) {
        logger.error('销毁音频上下文失败', error);
      }
    }

    this.context = null;
    this.isPlaying = false;
    this.currentAudio = null;
    this.onStateChange = null;
    
    logger.info('音频管理器已销毁');
  }
}

// 创建全局实例
const audioManager = new AudioManager();

module.exports = {
  audioManager,
  AudioManager,
  
  // 便捷方法
  init: (...args) => audioManager.init(...args),
  play: (...args) => audioManager.play(...args),
  pause: (...args) => audioManager.pause(...args),
  stop: (...args) => audioManager.stop(...args),
  toggle: (...args) => audioManager.toggle(...args),
  setVolume: (...args) => audioManager.setVolume(...args),
  setPlaybackRate: (...args) => audioManager.setPlaybackRate(...args),
  seek: (...args) => audioManager.seek(...args),
  getState: (...args) => audioManager.getState(...args),
  getHistory: (...args) => audioManager.getHistory(...args),
  clearHistory: (...args) => audioManager.clearHistory(...args),
  destroy: (...args) => audioManager.destroy(...args)
};