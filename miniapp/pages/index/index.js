const config = require('../../utils/config.js');
const { performanceMonitor } = require('../../utils/performance.js');
const { getWithRetry, postWithRetry } = require('../../utils/request.js');
const { logger, handleError, handleNetworkError, handlePermissionError } = require('../../utils/logger.js');
const { BusinessCache } = require('../../utils/cache.js');
const { audioManager } = require('../../utils/audio.js');

Page({
  data: {
    // 位置 & 地图
    latitude: 0,
    longitude: 0,
    markers: [],
    
    // 讲解与音频
    currentGuide: null,   // { name, audio }
    isPlaying: false,
    innerAudioContext: null,
    
    // 景点信息
    sceneName: '',
    styles: ['历史文化', '趣闻轶事', '诗词文学', '人物故事'],
    style: '历史文化',
    text: '',
    loading: false,
    
    // 性能优化相关
    locationLoaded: false,
    stylesLoaded: false,
    
    // 错误处理
    errorMessage: '',
    retryCount: 0,
    maxRetries: 3
  },

  /* 生命周期 */
  async onLoad() {
    performanceMonitor.start('page_load');
    logger.info('页面开始加载');
    
    try {
      await this.initializeApp();
      
      const loadTime = performanceMonitor.end('page_load');
      logger.performance('页面加载', loadTime);
      
      // 性能警告
      if (loadTime > config.PERFORMANCE.PAGE_LOAD_THRESHOLD) {
        logger.warn('页面加载时间过长', { loadTime, threshold: config.PERFORMANCE.PAGE_LOAD_THRESHOLD });
      }
      
      logger.info('页面加载完成');
    } catch (error) {
      logger.error('页面初始化失败', error);
      handleError('页面初始化失败，请重试', error);
    }
  },
  
  onUnload() {
    logger.info('页面卸载，清理资源');
    // 清理定时器等资源
    this.clearResources();
  },
  
  onShow() {
    logger.info('页面显示，同步音频状态');
    // 页面显示时检查音频状态
    this.syncAudioState();
  },

  /* ---------------- 位置相关 ---------------- */
  /** 异步获取用户位置 **/
  async getUserLocationAsync(isHighAccuracy = true) {
    try {
      // 先尝试从缓存获取位置（如果缓存时间较短）
      const cachedLocation = await BusinessCache.getCachedUserLocation();
      if (cachedLocation) {
        logger.info('用户位置缓存命中');
        this.setData({
          userLocation: cachedLocation,
          locationLoaded: true,
          sceneName: '示例景点', // 设置景点名称
          // 设置示例标记点
          markers: [{
            id: 1,
            latitude: cachedLocation.latitude + 0.001,
            longitude: cachedLocation.longitude + 0.001,
            name: '示例景点',
            title: '示例景点',
            iconPath: '/assets/icon-headphone.svg',
            width: 36,
            height: 36
          }],
          // 当前讲解（示例）
          currentGuide: {
            name: '示例景点讲解',
            audio: 'https://example.com/audio.mp3'
          }
        });
        
        // 获取周边景点信息
        this.getNearbySpots(cachedLocation.latitude, cachedLocation.longitude);
        
        return cachedLocation;
      }
      
      // 从系统获取位置
      const location = await new Promise((resolve, reject) => {
        wx.getLocation({
          type: 'gcj02',
          isHighAccuracy,
          success: resolve,
          fail: reject
        });
      });
      
      logger.info('位置获取成功', { 
        latitude: location.latitude, 
        longitude: location.longitude,
        accuracy: location.accuracy 
      });
      
      const userLocation = {
        latitude: location.latitude,
        longitude: location.longitude,
        accuracy: location.accuracy,
        timestamp: Date.now()
      };
      
      // 缓存位置信息
      await BusinessCache.cacheUserLocation(userLocation);
      
      this.setData({
        userLocation,
        locationLoaded: true,
        // 随手给一个示例景点作为 markers，真实项目里应调用后端获取周边景点
        markers: [{
          id: 1,
          latitude: location.latitude + 0.001,
          longitude: location.longitude + 0.001,
          name: '示例景点',
          title: '示例景点',
          iconPath: '/assets/icon-headphone.svg',
          width: 36,
          height: 36
        }],

        // 当前讲解（示例）
        currentGuide: {
          name: '示例景点讲解',
          audio: 'https://example.com/audio.mp3'
        },
        
        sceneName: '示例景点'
      });

      // 获取周边景点信息
      this.getNearbySpots(location.latitude, location.longitude);
      
      return userLocation;
    } catch (error) {
      logger.error('位置获取失败', error);
      this.handleLocationError(error);
      throw error;
    }
  },
  
  /** 处理位置获取错误 **/
  handleLocationError(error) {
    logger.error('位置获取错误', error);
    
    let message = '获取位置失败';
    let showSettings = false;
    
    if (error.errMsg) {
      if (error.errMsg.includes('auth deny')) {
        message = '需要位置权限才能使用此功能';
        showSettings = true;
      } else if (error.errMsg.includes('timeout')) {
        message = '位置获取超时，请检查GPS设置';
      } else if (error.errMsg.includes('fail')) {
        message = '位置服务不可用，请检查设置';
        showSettings = true;
      }
    }
    
    if (showSettings) {
      wx.showModal({
        title: '位置权限',
        content: message + '，是否前往设置？',
        success: (res) => {
          if (res.confirm) {
            wx.openSetting({
              success: (settingRes) => {
                if (settingRes.authSetting['scope.userLocation']) {
                  logger.info('用户已授权位置权限');
                  // 重新获取位置
                  this.getUserLocationAsync();
                } else {
                  handlePermissionError('位置权限', '用户拒绝授权位置权限');
                }
              },
              fail: (err) => {
                logger.error('打开设置页面失败', err);
                handleError('无法打开设置页面');
              }
            });
          }
        }
      });
    } else {
      handleError(message, error);
    }
    
    // 设置默认状态，避免显示"获取中..."
    this.setData({
      sceneName: '位置获取失败',
      locationLoaded: false
    });
  },
  
  /** 兼容旧版本的同步方法 **/
  getUserLocation() {
    this.getUserLocationAsync().catch(console.error);
  },
  
  /* ---------------- 后端API调用 ---------------- */
  /** 获取周边景点 **/
  async getNearbySpots(lat, lng) {
    performanceMonitor.start('get_nearby_spots');
    
    try {
      const location = { latitude: lat, longitude: lng };
      
      // 先尝试从缓存获取
      let spots = await BusinessCache.getCachedNearbySpots(location);
      
      if (spots) {
        logger.info('周边景点缓存命中');
        
        // 如果有缓存的周边景点，使用第一个景点作为当前景点
        const currentSpot = spots[0] || null;
        
        this.setData({ 
          nearbySpots: spots,
          sceneName: currentSpot ? currentSpot.name : '示例景点'
        });
        performanceMonitor.end('get_nearby_spots');
        return;
      }
      
      // 从网络获取
      const res = await getWithRetry(config.API.ENDPOINTS.NEARBY_SPOTS, {
        lat, 
        lng, 
        radius: config.MAP.SEARCH_RADIUS
      });
      
      const loadTime = performanceMonitor.end('get_nearby_spots');
      logger.performance('周边景点加载', loadTime, { count: res.data?.spots?.length });
      
      if (res.data && res.data.spots) {
        // 缓存数据
        await BusinessCache.cacheNearbySpots(location, res.data.spots);
        
        // 更新地图标记
        const markers = res.data.spots.map(spot => ({
          id: spot.id,
          latitude: spot.latitude,
          longitude: spot.longitude,
          title: spot.name,
          iconPath: '/assets/icon-headphone.svg',
          width: config.MAP.MARKER_SIZE,
          height: config.MAP.MARKER_SIZE
        }));
        
        // 如果有周边景点，使用第一个景点作为当前景点
        const currentSpot = res.data.spots[0] || null;
        
        this.setData({ 
          markers,
          nearbySpots: res.data.spots,
          sceneName: currentSpot ? currentSpot.name : '示例景点'
        });
        
        logger.info('周边景点加载成功', { count: res.data.spots.length });
      } else {
        logger.warn('周边景点数据格式异常', res);
      }
    } catch (error) {
      performanceMonitor.end('get_nearby_spots');
      logger.error('获取周边景点失败', error);
      handleNetworkError(error, '获取周边景点');
    }
  },
  
  /** 应用初始化 **/
  initializeApp() {
    return new Promise(async (resolve, reject) => {
      try {
        // 并行初始化各组件
        await Promise.all([
          this.initAudioAsync(),
          this.getUserLocationAsync()
        ]);
        
        // 加载讲解风格（可能依赖位置信息，所以放在后面）
        await this.loadGuideStylesAsync();
        
        resolve();
      } catch (error) {
        console.error('初始化失败:', error);
        reject(error);
      }
    });
  },
  
  /** 清理资源 **/
  clearResources() {
    logger.info('开始清理资源');
    
    // 销毁音频管理器
    try {
      audioManager.destroy();
      logger.info('音频资源已清理');
    } catch (error) {
      logger.error('清理音频资源失败', error);
    }
    
    // 清理性能监控
    performanceMonitor.clear();
    
    // 重置状态
    this.setData({
      isPlaying: false,
      currentGuide: null
    });
    
    logger.info('资源清理完成');
  },
  
  /** 同步音频状态 **/
  syncAudioState() {
    const audioState = audioManager.getState();
    if (audioState.isPlaying !== this.data.isPlaying) {
      logger.debug('同步音频状态', { 
        audioManagerState: audioState.isPlaying, 
        pageState: this.data.isPlaying 
      });
      this.setData({ isPlaying: audioState.isPlaying });
    }
  },
  
  /** 错误处理 **/
  handleError(message, error = null) {
    if (error) console.error(message, error);
    
    this.setData({
      errorMessage: message,
      loading: false
    });
    
    wx.showToast({
      title: message,
      icon: 'none',
      duration: 2000
    });
  },
  
  /** 重试机制 **/
  async retryOperation(operation, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
      try {
        logger.debug(`尝试操作，第${i + 1}次`, operation.name);
        return await operation();
      } catch (error) {
        logger.warn(`操作失败，第${i + 1}次`, error);
        
        if (i === maxRetries - 1) {
          throw error;
        }
        
        // 指数退避
        const delay = Math.pow(2, i) * 1000;
        logger.debug(`等待${delay}ms后重试`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  },
  
  /** 加载讲解风格（异步版本） **/
  async loadGuideStylesAsync() {
    performanceMonitor.start('load_guide_styles');
    
    try {
      // 先尝试从缓存获取
      let styles = await BusinessCache.getCachedGuideStyles();
      
      if (styles) {
        logger.info('讲解风格缓存命中');
        this.setData({
          guideStyles: styles,
          stylesLoaded: true
        });
        performanceMonitor.end('load_guide_styles');
        return;
      }
      
      // 从网络获取
      const response = await getWithRetry(config.API.ENDPOINTS.GUIDE_STYLES, {
        timeout: config.API.TIMEOUT
      });
      
      const loadTime = performanceMonitor.end('load_guide_styles');
      logger.performance('讲解风格加载', loadTime, { count: response.data?.length });
      
      if (response.data && Array.isArray(response.data)) {
        // 缓存数据
        await BusinessCache.cacheGuideStyles(response.data);
        
        this.setData({
          guideStyles: response.data,
          stylesLoaded: true
        });
        
        logger.info('讲解风格加载成功', { count: response.data.length });
      } else {
        throw new Error('讲解风格数据格式错误');
      }
    } catch (error) {
      performanceMonitor.end('load_guide_styles');
      logger.error('加载讲解风格失败', error);
      
      // 使用默认数据
      const defaultStyles = [
        { id: 1, name: '专业讲解', description: '详细专业的景点介绍' },
        { id: 2, name: '趣味故事', description: '生动有趣的历史故事' },
        { id: 3, name: '简洁介绍', description: '简明扼要的要点说明' }
      ];
      
      this.setData({
        guideStyles: defaultStyles,
        stylesLoaded: true
      });
      
      logger.warn('使用默认讲解风格', { count: defaultStyles.length });
    }
  },

  /* ---------------- 音频播放 ---------------- */
  /** 异步初始化音频上下文 **/
  async initAudioAsync() {
    try {
      await audioManager.init();
      
      // 设置状态变化回调
      audioManager.setStateChangeCallback((event, data) => {
        switch (event) {
          case 'play':
            this.setData({ isPlaying: true });
            break;
          case 'pause':
          case 'ended':
          case 'error':
            this.setData({ isPlaying: false });
            break;
          case 'timeupdate':
            // 可以在这里更新播放进度
            break;
        }
      });
      
      logger.info('音频管理器初始化成功');
      return audioManager;
    } catch (error) {
      logger.error('音频初始化失败', error);
      throw error;
    }
  },
  
  /** 兼容旧版本的同步方法 **/
  initAudio() {
    this.initAudioAsync().catch(console.error);
  },

  /** 播放 / 暂停 **/
  async playAudio() {
    const { isPlaying, currentGuide } = this.data;
    
    if (!currentGuide || !currentGuide.audio) {
      logger.warn('没有可播放的音频');
      handleError('没有可播放的音频内容');
      return;
    }

    try {
      if (isPlaying) {
        // 暂停播放
        audioManager.pause();
        logger.userAction('暂停音频播放');
      } else {
        // 开始播放
        await audioManager.play(currentGuide.audio, {
          title: currentGuide.title || '景点讲解'
        });
        logger.userAction('开始播放音频', { 
          url: currentGuide.audio,
          title: currentGuide.title 
        });
      }
    } catch (error) {
      logger.error('音频播放控制失败', error);
      
      let errorMessage = '音频播放失败';
      if (error.message.includes('超时')) {
        errorMessage = '音频加载超时，请检查网络连接';
      } else if (error.message.includes('网络')) {
        errorMessage = '网络连接异常，请稍后重试';
      } else if (error.message.includes('格式')) {
        errorMessage = '音频格式不支持';
      }
      
      // 显示重试选项
      wx.showModal({
        title: '播放失败',
        content: errorMessage + '，是否重试？',
        success: (res) => {
          if (res.confirm) {
            // 延迟重试
            setTimeout(() => {
              this.playAudio();
            }, 1000);
          }
        }
      });
    }
  },
  
  /* ---------------- UI 交互 ---------------- */
  /** 选择讲解风格 **/
  // 风格选择事件处理
  onStyleTap(e) {
    this.selectStyle(e);
  },

  selectStyle(e) {
    const selectedStyle = e.currentTarget.dataset.style;
    
    if (selectedStyle === this.data.selectedStyle) {
      logger.debug('重复选择相同风格', selectedStyle);
      return;
    }
    
    logger.userAction('选择讲解风格', { style: selectedStyle });
    
    this.setData({
      selectedStyle
    });
  },

  /** 生成并播放讲解 **/
  async generateGuide() {
    logger.userAction('点击生成讲解');
    
    if (!this.data.userLocation) {
      handleError('请先获取位置信息');
      return;
    }
    
    if (!this.data.selectedStyle) {
      handleError('请选择讲解风格');
      return;
    }
    
    this.setData({ isGenerating: true });
    
    try {
      await this.requestGuideWithRetry();
      logger.userAction('讲解生成成功');
    } catch (error) {
      logger.error('生成讲解失败', error);
      handleError('生成讲解失败，请重试', error);
    } finally {
      this.setData({ isGenerating: false });
    }
  },
  
  /** 带重试机制的讲解请求 **/
 
   // 处理播放按钮点击事件
   async handlePlay() {
     logger.userAction('点击播放讲解按钮');
     
     // 如果已有讲解内容，直接播放
     if (this.data.currentGuide && this.data.currentGuide.audio) {
       await this.playAudio();
       return;
     }
     
     // 否则先生成讲解
     await this.generateGuide();
   },

  requestGuideWithRetry(params) {
    return this.retryOperation(
      () => this.requestGuide(params),
      '生成讲解失败'
    );
  },
  
  /** 请求讲解内容 **/
  async requestGuide(params) {
    performanceMonitor.start('request_guide');
    
    try {
      // 先尝试从缓存获取
      let guide = await BusinessCache.getCachedGuideContent(params);
      
      if (guide) {
        logger.info('讲解内容缓存命中');
        this.setData({ currentGuide: guide });
        
        // 根据配置决定是否自动播放
        if (config.AUDIO.AUTO_PLAY && guide.audio) {
          await this.playAudio();
        }
        
        performanceMonitor.end('request_guide');
        return;
      }
      
      // 从网络获取
      const response = await postWithRetry(config.API.ENDPOINTS.GENERATE_GUIDE, {
        data: params,
        timeout: config.API.TIMEOUT
      });
      
      const loadTime = performanceMonitor.end('request_guide');
      logger.performance('讲解内容生成', loadTime, { textLength: response.data?.text?.length });
      
      if (response.data && response.data.text) {
        const guideContent = {
          text: response.data.text,
          audio: response.data.audio,
          title: response.data.title || '景点讲解',
          timestamp: Date.now()
        };
        
        // 缓存讲解内容
        await BusinessCache.cacheGuideContent(params, guideContent);
        
        this.setData({ currentGuide: guideContent });
        
        logger.info('讲解内容生成成功', { 
          textLength: response.data.text.length,
          hasAudio: !!response.data.audio 
        });
        
        // 根据配置决定是否自动播放
        if (config.AUDIO.AUTO_PLAY && response.data.audio) {
          await this.playAudio();
        }
      } else {
        throw new Error('讲解内容数据格式错误');
      }
    } catch (error) {
      performanceMonitor.end('request_guide');
      logger.error('请求讲解内容失败', error);
      throw error;
    }
  }
});

  