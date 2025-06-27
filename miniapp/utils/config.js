/**
 * 配置管理工具
 * 统一管理API域名、超时时间等配置
 */

// 获取当前环境
const getEnvType = () => {
  try {
    return __wxConfig.envVersion || 'release';
  } catch (e) {
    return 'release';
  }
};

// 环境配置
const ENV_CONFIG = {
  // 开发环境
  develop: {
    API_BASE_URL: 'http://localhost:5001',
    USE_MOCK_DATA: true,
    DEBUG: true,
    REQUEST_TIMEOUT: 10000
  },
  // 体验版
  trial: {
    API_BASE_URL: 'https://api-test.example.com',
    USE_MOCK_DATA: false,
    DEBUG: true,
    REQUEST_TIMEOUT: 15000
  },
  // 正式版
  release: {
    API_BASE_URL: 'https://api.example.com',
    USE_MOCK_DATA: false,
    DEBUG: false,
    REQUEST_TIMEOUT: 15000
  }
};

// 当前环境配置
const currentEnv = getEnvType();
const config = ENV_CONFIG[currentEnv] || ENV_CONFIG.release;

// 导出配置
module.exports = {
  // 当前环境
  ENV: currentEnv,
  
  // API配置
  API: {
    BASE_URL: config.API_BASE_URL,
    TIMEOUT: config.REQUEST_TIMEOUT,
    ENDPOINTS: {
      GUIDE_STYLES: '/guide/styles',
      NEARBY_SPOTS: '/spots/nearby',
      GENERATE_GUIDE: '/guide'
    }
  },
  
  // 功能开关
  FEATURES: {
    USE_MOCK_DATA: config.USE_MOCK_DATA,
    DEBUG: config.DEBUG,
    PERFORMANCE_MONITOR: true,
    ERROR_REPORTING: true
  },
  
  // 性能配置
  PERFORMANCE: {
    MAX_LOAD_TIME: 2000, // 最大加载时间（毫秒）
    MAX_RETRY_COUNT: 3,   // 最大重试次数
    RETRY_DELAY_BASE: 500 // 重试延迟基数（毫秒）
  },
  
  // 地图配置
  MAP: {
    DEFAULT_ZOOM: 16,
    MARKER_SIZE: 30,
    SEARCH_RADIUS: 1000 // 搜索半径（米）
  },
  
  // 音频配置
  AUDIO: {
    DEFAULT_VOLUME: 1.0,
    DEFAULT_PLAYBACK_RATE: 1.0,
    AUTO_PLAY: true,
    PRELOAD: true,        // 启用预加载以提高播放速度
    LOAD_TIMEOUT: 15000,  // 音频加载超时时间：15秒
    MAX_RETRIES: 3        // 最大重试次数
  },
  
  // 缓存配置
  CACHE: {
    MEMORY_TTL: 5 * 60 * 1000,    // 内存缓存过期时间：5分钟
    STORAGE_TTL: 30 * 60 * 1000,  // 本地存储缓存过期时间：30分钟
    MAX_MEMORY_SIZE: 50,          // 最大内存缓存条目数
    AUTO_CLEANUP: true            // 自动清理过期缓存
  },
  
  // 获取完整API URL
  getApiUrl(endpoint) {
    return `${this.API.BASE_URL}${endpoint}`;
  },
  
  // 是否为开发环境
  isDev() {
    return currentEnv === 'develop';
  },
  
  // 是否启用调试
  isDebug() {
    return config.DEBUG;
  },
  
  // 日志输出
  log(...args) {
    if (this.isDebug()) {
      console.log('[CONFIG]', ...args);
    }
  },
  
  // 警告输出
  warn(...args) {
    if (this.isDebug()) {
      console.warn('[CONFIG]', ...args);
    }
  }
};

// 初始化日志
module.exports.log('当前环境:', currentEnv);
module.exports.log('配置信息:', config);