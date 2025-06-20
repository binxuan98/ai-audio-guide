Page({
  data: {
    // 位置 & 地图
    latitude: 0,
    longitude: 0,
    markers: [],

    // 讲解与音频
    currentGuide: null,   // { name, audio }
    isPlaying: false,
    innerAudioContext: null
  },

  /* 生命周期 */
  onLoad() {
    this.getUserLocation(); // 获取定位（含授权处理）
    this.initAudio();       // 初始化音频实例
  },
  onUnload() {
    // 页面卸载时销毁音频，释放资源
    if (this.data.innerAudioContext) {
      this.data.innerAudioContext.destroy();
    }
  },

  /* ---------------- 位置相关 ---------------- */
  /** 带完整授权处理的定位函数 **/
  getUserLocation() {
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        const { latitude, longitude } = res;

        // 设置坐标
        this.setData({
          latitude,
          longitude,

          // 随手给一个示例景点作为 markers，真实项目里应调用后端获取周边景点
          markers: [{
            id: 1,
            latitude: latitude + 0.001,
            longitude: longitude + 0.001,
            name: '示例景点',
            title: '示例景点',
            iconPath: '/assets/icon-headphone.png',
            width: 36,
            height: 36
          }],

          // 当前讲解（示例）
          currentGuide: {
            name: '示例景点讲解',
            audio: 'https://example.com/audio.mp3'
          }
        });
      },

      /* ======= 定位失败 / 未授权 ======= */
      fail: () => {
        // ① 先查微信 App 的系统级定位授权
        wx.getAppAuthorizeSetting({
          success: (appAuth) => {
            if (!appAuth.locationAuthorized) {
              // 未授权系统定位
              wx.showModal({
                title: '提示',
                content: '请在系统设置中打开微信定位权限',
                confirmText: '去设置',
                success: (res) => {
                  if (res.confirm) wx.openAppAuthorizeSetting();
                }
              });
              return;
            }

            // ② 再查小程序自身的定位授权
            wx.getSetting({
              success: (settingRes) => {
                if (!settingRes.authSetting['scope.userLocation']) {
                  wx.showModal({
                    title: '提示',
                    content: '请允许小程序获取您的定位信息',
                    confirmText: '去授权',
                    success: (res) => {
                      if (res.confirm) wx.openSetting();
                    }
                  });
                } else {
                  // 已授权仍失败 → 可能是网络或 GPS 关闭
                  wx.showModal({
                    title: '提示',
                    content: '定位失败，请检查系统定位是否开启，或切换到稳定网络后重试。',
                    confirmText: '我知道了'
                  });
                }
              },
              fail: () => {
                wx.showToast({ title: '获取授权状态失败', icon: 'none' });
              }
            });
          },
          fail: () => {
            wx.showToast({ title: '获取系统定位权限失败', icon: 'none' });
          }
        });
      }
    });
  },

  /* ---------------- 音频播放 ---------------- */
  /** 创建音频上下文 **/
  initAudio() {
    const innerAudioContext = wx.createInnerAudioContext();
    this.setData({ innerAudioContext });
  },

  /** 播放 / 暂停 **/
  playAudio() {
    const { isPlaying, innerAudioContext, currentGuide } = this.data;
    if (!innerAudioContext || !currentGuide) return;

    if (isPlaying) {
      innerAudioContext.pause();
    } else {
      innerAudioContext.src = currentGuide.audio;
      innerAudioContext.play();
    }
    this.setData({ isPlaying: !isPlaying });
  }
});

  