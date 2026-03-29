import { request } from '../../../services/request';
Page({
  data: { list: [] as any[], loading: false, action: '' },
  onLoad(options: any) { this.setData({ action: options.action || '' }); },
  onShow() { this.loadList(); },
  async loadList() {
    this.setData({ loading: true });
    const resp = await request({ url: '/resume?page=1&page_size=50' });
    this.setData({ list: resp.data.list, loading: false });
  },
  onAdd() { wx.navigateTo({ url: '/pages/resume/upload/upload' }); },
  onSelect(e: any) {
    const item = e.currentTarget.dataset.item;
    if (this.data.action === 'select') {
      if (item.parse_status !== 'completed') { wx.showToast({ title: '该简历尚未解析完成', icon: 'none' }); return; }
      wx.redirectTo({ url: `/pages/task/jd-input/jd-input?resumeId=${item.id}` });
    } else {
      wx.navigateTo({ url: `/pages/resume/confirm/confirm?id=${item.id}` });
    }
  },
});
