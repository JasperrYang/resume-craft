import { request } from '../../../services/request';
Page({
  data: { list: [] as any[], loading: false },
  onShow() { this.loadList(); },
  async loadList() {
    this.setData({ loading: true });
    try {
      const resp = await request({ url: '/task?page=1&page_size=50' });
      this.setData({ list: resp.data.list, loading: false });
    } catch { this.setData({ loading: false }); }
  },
  onViewTask(e: any) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/task/result/result?id=${id}` });
  },
});
