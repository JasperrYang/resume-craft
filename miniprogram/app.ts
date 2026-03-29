/**
 * ResumeCraft 小程序入口
 */

// 开发环境配置
const IS_DEV = true; // 上线前改为 false
const DEV_BASE_URL = 'http://127.0.0.1:8000/api/v1';
const PROD_BASE_URL = 'https://your-domain.com/api/v1';

App({
  globalData: {
    userInfo: null,
    token: '',
    baseUrl: IS_DEV ? DEV_BASE_URL : PROD_BASE_URL,
  },

  onLaunch() {
    const token = wx.getStorageSync('token');
    if (token) {
      this.globalData.token = token;
    }
  },

  /**
   * 登录（Mock模式下直接调用后端Mock接口）
   */
  login(): Promise<any> {
    return new Promise((resolve, reject) => {
      if (IS_DEV) {
        // Mock 模式：直接请求 mock login 接口
        wx.request({
          url: `${this.globalData.baseUrl}/auth/login`,
          method: 'POST',
          data: { code: 'mock_code' },
          success: (resp: any) => {
            if (resp.data.code === 0) {
              const { token, user } = resp.data.data;
              this.globalData.token = token;
              this.globalData.userInfo = user;
              wx.setStorageSync('token', token);
              wx.setStorageSync('userInfo', user);
              resolve(user);
            } else {
              reject(new Error(resp.data.message));
            }
          },
          fail: reject,
        });
        return;
      }

      // 正式模式：走微信登录流程
      wx.login({
        success: (res) => {
          if (res.code) {
            wx.request({
              url: `${this.globalData.baseUrl}/auth/login`,
              method: 'POST',
              data: { code: res.code },
              success: (resp: any) => {
                if (resp.data.code === 0) {
                  const { token, user } = resp.data.data;
                  this.globalData.token = token;
                  this.globalData.userInfo = user;
                  wx.setStorageSync('token', token);
                  wx.setStorageSync('userInfo', user);
                  resolve(user);
                } else {
                  reject(new Error(resp.data.message));
                }
              },
              fail: reject,
            });
          } else {
            reject(new Error('微信登录失败'));
          }
        },
        fail: reject,
      });
    });
  },
});
