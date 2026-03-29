/**
 * 首页逻辑
 */
const app = getApp<IAppOption>();

Page({
  data: {
    resumeCount: 0,
    taskCount: 0,
    remainingCount: 0,
    isLoggedIn: false,
  },

  onShow() {
    this.checkLoginAndLoadData();
  },

  /** 检查登录并加载数据 */
  async checkLoginAndLoadData() {
    const token = wx.getStorageSync('token');
    if (!token) {
      try {
        await app.login();
      } catch (e) {
        console.error('登录失败:', e);
        return;
      }
    }
    this.setData({ isLoggedIn: true });
    this.loadUserData();
  },

  /** 加载用户数据 */
  async loadUserData() {
    try {
      const { request } = require('../../services/request');
      const resp = await request({ url: '/auth/profile' });
      const user = resp.data;
      this.setData({
        resumeCount: user.stats?.total_resumes || 0,
        taskCount: user.stats?.total_tasks || 0,
        remainingCount: (user.quota?.paid_remaining || 0) + (user.quota?.free_daily_used < 1 ? 1 : 0),
      });
    } catch (e) {
      console.error('加载用户数据失败:', e);
    }
  },

  /** 新建优化任务 */
  onStartTask() {
    // 先检查是否有简历，没有则去上传
    if (this.data.resumeCount === 0) {
      wx.navigateTo({ url: '/pages/resume/upload/upload' });
    } else {
      wx.navigateTo({ url: '/pages/resume/list/list?action=select' });
    }
  },

  /** 跳转简历库 */
  onGoResumeList() {
    wx.navigateTo({ url: '/pages/resume/list/list' });
  },

  /** 跳转历史记录 */
  onGoHistory() {
    wx.switchTab({ url: '/pages/history/list/list' });
  },

  /** 跳转支付 */
  onGoPay() {
    wx.navigateTo({ url: '/pages/pay/index/index' });
  },
});
