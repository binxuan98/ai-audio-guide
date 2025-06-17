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
          })
        },
        fail: () => {
          wx.showToast({
            title: '获取定位失败',
            icon: 'none'
          })
        }
      })
    }
  })
  