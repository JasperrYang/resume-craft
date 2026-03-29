import { request } from '../../../services/request';
const steps = ['正在解析JD关键词...', '正在匹配能力库...', '正在智能改写...', '正在生成报告...'];

Page({
  data: { taskId: '', stepIndex: 0, currentStep: steps[0] },
  _timer: null as any,

  onLoad(options: any) {
    if (options.id) {
      this.setData({ taskId: options.id });
      this.startAnimation();
      this.pollStatus(options.id);
    }
  },

  onUnload() { if (this._timer) clearInterval(this._timer); },

  startAnimation() {
    let i = 0;
    this._timer = setInterval(() => {
      i = Math.min(i + 1, steps.length - 1);
      this.setData({ stepIndex: i, currentStep: steps[i] });
    }, 3000);
  },

  async pollStatus(taskId: string) {
    const poll = async () => {
      try {
        const resp = await request({ url: `/task/${taskId}` });
        if (resp.data.status === 'completed' || resp.data.status === 'failed') {
          if (this._timer) clearInterval(this._timer);
          if (resp.data.status === 'completed') {
            wx.redirectTo({ url: `/pages/task/result/result?id=${taskId}` });
          } else {
            wx.showToast({ title: '分析失败，请重试', icon: 'none' });
            setTimeout(() => wx.navigateBack(), 1500);
          }
          return;
        }
        setTimeout(poll, 2000);
      } catch { setTimeout(poll, 2000); }
    };
    setTimeout(poll, 2000);
  },
});
