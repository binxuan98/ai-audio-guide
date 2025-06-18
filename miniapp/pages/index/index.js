Page({
    data: {
      latitude: 0,
      longitude: 0 
    },
  
    onLoad() {
      this.getUserLocation()
    },
  
    getUserLocation() {
      wx.getLocation({
        type: 'gcj02',
        success: (res) => {
          this.setData({
            latitude: res.latitude,
            longitude: res.longitude
          });
        },
        fail: (err) => {
          // 第一步：获取微信 App 的定位授权状态
          wx.getAppAuthorizeSetting({
            success: (appAuth) => {
              if (!appAuth.locationAuthorized) {
                wx.showModal({
                  title: '提示',
                  content: '请授权微信定位权限',
                  confirmText: '去设置',
                  success: (res) => {
                    if (res.confirm) {
                      wx.openAppAuthorizeSetting(); // 打开系统设置
                    }
                  }
                });
                return;
              }
    
              // 第二步：检查小程序的定位权限
              wx.getSetting({
                success: (settingRes) => {
                  if (!settingRes.authSetting['scope.userLocation']) {
                    wx.showModal({
                      title: '提示',
                      content: '请允许小程序获取您的定位信息',
                      confirmText: '去授权',
                      success: (res) => {
                        if (res.confirm) {
                          wx.openSetting(); // 打开小程序设置页面
                        }
                      }
                    });
                  } else {
                    // 已授权，但仍失败，可能是网络/GPS问题
                    wx.showModal({
                      title: '提示',
                      content: '定位失败，请检查系统定位是否开启，或切换至稳定网络后重试。',
                      confirmText: '我知道了'
                    });
                  }
                },
                fail: () => {
                  wx.showToast({
                    title: '获取授权状态失败',
                    icon: 'none'
                  });
                }
              });
            },
            fail: () => {
              wx.showToast({
                title: '获取系统定位权限失败',
                icon: 'none'
              });
            }
          });
        }
      });
    }
    
  })
  