import { request } from '../../../services/request';
Page({
  data: { resumeId: '', parsed: null as any },
  onLoad(options: any) {
    if (options.id) { this.setData({ resumeId: options.id }); this.loadResume(options.id); }
  },
  async loadResume(id: string) {
    const resp = await request({ url: `/resume/${id}` });
    this.setData({ parsed: resp.data.parsed_data });
  },
  async onConfirm() {
    await request({ url: `/resume/${this.data.resumeId}/confirm`, method: 'PUT', data: { parsed_data: this.data.parsed } });
    wx.redirectTo({ url: `/pages/task/jd-input/jd-input?resumeId=${this.data.resumeId}` });
  },
});
