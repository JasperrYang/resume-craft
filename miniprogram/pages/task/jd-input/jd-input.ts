/**
 * JD输入页逻辑
 */
import { request } from '../../../services/request';

Page({
  data: {
    jdText: '',
    jdUrl: '',
    selectedResume: null as any,
    resumeId: '',
    submitting: false,
  },

  onLoad(options: any) {
    if (options.resumeId) {
      this.setData({ resumeId: options.resumeId });
      this.loadResumeInfo(options.resumeId);
    }
  },

  /** 加载简历信息 */
  async loadResumeInfo(resumeId: string) {
    try {
      const resp = await request({ url: `/resume/${resumeId}` });
      this.setData({ selectedResume: resp.data });
    } catch (e) {
      console.error('加载简历失败:', e);
    }
  },

  onJdInput(e: any) {
    this.setData({ jdText: e.detail.value });
  },

  onUrlInput(e: any) {
    this.setData({ jdUrl: e.detail.value });
  },

  onChangeResume() {
    wx.navigateTo({ url: '/pages/resume/list/list?action=select' });
  },

  /** 提交优化任务 */
  async onSubmit() {
    if (!this.data.jdText && !this.data.jdUrl) {
      wx.showToast({ title: '请输入JD内容', icon: 'none' });
      return;
    }

    this.setData({ submitting: true });

    try {
      const resp = await request({
        url: '/task/create',
        method: 'POST',
        data: {
          resume_id: this.data.resumeId,
          jd_text: this.data.jdText || undefined,
          jd_url: this.data.jdUrl || undefined,
        },
      });

      // 跳转到分析中页面
      wx.redirectTo({
        url: `/pages/task/analyzing/analyzing?id=${resp.data.task_id}`,
      });
    } catch (e: any) {
      if (e.message?.includes('免费次数已用完')) {
        wx.showModal({
          title: '次数不足',
          content: '免费次数已用完，是否购买优化次数？',
          confirmText: '去购买',
          success: (res) => {
            if (res.confirm) {
              wx.navigateTo({ url: '/pages/pay/index/index' });
            }
          },
        });
      }
    } finally {
      this.setData({ submitting: false });
    }
  },
});
