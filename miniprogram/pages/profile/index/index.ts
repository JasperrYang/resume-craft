import { request } from '../../../services/request';
Page({
  data: { userInfo: {} as any, quota: { paid_remaining: 0, free_daily_used: 0, chat_remaining: 0 } },
  onShow() { this.loadProfile(); },
  async loadProfile() {
    try {
      const resp = await request({ url: '/auth/profile' });
      this.setData({ userInfo: resp.data, quota: resp.data.quota });
    } catch (e) { console.error(e); }
  },
  onGoPay() { wx.navigateTo({ url: '/pages/pay/index/index' }); },
  onGoResumes() { wx.navigateTo({ url: '/pages/resume/list/list' }); },
  onGoHistory() { wx.switchTab({ url: '/pages/history/list/list' }); },
  onFeedback() { wx.showToast({ title: '功能开发中', icon: 'none' }); },
  onAbout() { wx.showToast({ title: 'ResumeCraft v1.0', icon: 'none' }); },
});
