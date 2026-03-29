/**
 * 上传简历页逻辑
 */
import { uploadFile, request } from '../../../services/request';

Page({
  data: {
    title: '',
    fileName: '',
    uploading: false,
    progress: 0,
    uploadResult: null as any,
    parseStatus: 'pending',
    resumeId: '',
  },

  onTitleInput(e: any) {
    this.setData({ title: e.detail.value });
  },

  /** 选择文件 */
  onChooseFile() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['pdf', 'docx'],
      success: (res) => {
        const file = res.tempFiles[0];
        if (file.size > 10 * 1024 * 1024) {
          wx.showToast({ title: '文件不能超过10MB', icon: 'none' });
          return;
        }
        this.setData({ fileName: file.name });
        this.doUpload(file.path);
      },
    });
  },

  /** 执行上传 */
  async doUpload(filePath: string) {
    this.setData({ uploading: true, progress: 20 });

    try {
      const formData: Record<string, string> = {};
      if (this.data.title) {
        formData.title = this.data.title;
      }

      this.setData({ progress: 50 });
      const resp = await uploadFile('/resume/upload', filePath, formData);

      this.setData({
        progress: 80,
        uploadResult: resp.data,
        resumeId: resp.data.resume_id,
      });

      // 轮询解析状态
      this.pollParseStatus(resp.data.resume_id);
    } catch (e) {
      wx.showToast({ title: '上传失败', icon: 'none' });
      this.setData({ uploading: false, progress: 0 });
    }
  },

  /** 轮询解析状态 */
  async pollParseStatus(resumeId: string) {
    let retries = 0;
    const maxRetries = 30; // 最多等30次，每次2秒

    const poll = async () => {
      if (retries >= maxRetries) {
        this.setData({ uploading: false, parseStatus: 'failed' });
        wx.showToast({ title: '解析超时，请重试', icon: 'none' });
        return;
      }

      try {
        const resp = await request({ url: `/resume/${resumeId}` });
        const status = resp.data.parse_status;

        if (status === 'completed') {
          this.setData({
            uploading: false,
            progress: 100,
            parseStatus: 'completed',
          });
          return;
        }

        if (status === 'failed') {
          this.setData({ uploading: false, parseStatus: 'failed' });
          wx.showToast({ title: '解析失败，请重试', icon: 'none' });
          return;
        }

        retries++;
        setTimeout(poll, 2000);
      } catch (e) {
        retries++;
        setTimeout(poll, 2000);
      }
    };

    setTimeout(poll, 2000);
  },

  /** 下一步 */
  onNext() {
    wx.navigateTo({
      url: `/pages/resume/confirm/confirm?id=${this.data.resumeId}`,
    });
  },

  /** 重新上传 */
  onReupload() {
    this.setData({
      uploading: false,
      progress: 0,
      uploadResult: null,
      parseStatus: 'pending',
      resumeId: '',
      fileName: '',
    });
  },
});
