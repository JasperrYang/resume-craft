/**
 * 优化结果页逻辑
 */
import { request } from '../../../services/request';

Page({
  data: {
    taskId: '',
    isPaid: false,
    result: null as any,
    preview: null as any,
    loading: true,
  },

  onLoad(options: any) {
    if (options.id) {
      this.setData({ taskId: options.id });
      this.loadTask(options.id);
    }
  },

  /** 加载任务结果 */
  async loadTask(taskId: string) {
    try {
      const resp = await request({ url: `/task/${taskId}` });
      const data = resp.data;

      this.setData({
        isPaid: data.is_paid,
        result: data.result || data,
        preview: data.preview,
        loading: false,
      });
    } catch (e) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  /** 去支付 */
  onGoPay() {
    wx.navigateTo({
      url: `/pages/pay/index/index?taskId=${this.data.taskId}`,
    });
  },

  /** 对话微调 */
  onChat() {
    wx.navigateTo({
      url: `/pages/task/chat/chat?id=${this.data.taskId}`,
    });
  },

  /** 导出PDF */
  async onExport() {
    wx.showLoading({ title: '生成中...' });
    try {
      const resp = await request({
        url: `/task/${this.data.taskId}/export`,
        method: 'POST',
        data: { format: 'pdf', template: 'classic' },
      });

      wx.hideLoading();

      // 打开文档预览
      const downloadUrl = resp.data.download_url;
      wx.downloadFile({
        url: downloadUrl,
        success: (res) => {
          wx.openDocument({
            filePath: res.tempFilePath,
            fileType: 'pdf',
          });
        },
      });
    } catch (e) {
      wx.hideLoading();
      wx.showToast({ title: '导出失败', icon: 'none' });
    }
  },
});
