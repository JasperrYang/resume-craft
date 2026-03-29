/**
 * 对话式调整页逻辑
 */
import { request } from '../../../services/request';

Page({
  data: {
    taskId: '',
    messages: [] as any[],
    inputText: '',
    isThinking: false,
    scrollToId: 'msg-welcome',
    previewExpanded: false,
    resumeText: '',
    matchScore: 0,
    chatUsed: 0,
    chatLimit: 3,
    quickTags: ['更简洁', '更详细', '更正式', '突出管理能力', '突出技术深度', '调整排序'],
  },

  onLoad(options: any) {
    if (options.id) {
      this.setData({ taskId: options.id });
      this.loadTaskData(options.id);
    }
  },

  /** 加载任务数据 */
  async loadTaskData(taskId: string) {
    try {
      const resp = await request({ url: `/task/${taskId}` });
      const data = resp.data;
      this.setData({
        resumeText: data.result?.optimized_text || '',
        matchScore: data.result?.match_score?.after || 0,
        chatUsed: data.chat_rounds_used || 0,
        chatLimit: data.chat_rounds_limit || 3,
      });
    } catch (e) {
      console.error('加载任务失败:', e);
    }
  },

  /** 切换预览展开 */
  togglePreview() {
    this.setData({ previewExpanded: !this.data.previewExpanded });
  },

  onInput(e: any) {
    this.setData({ inputText: e.detail.value });
  },

  /** 快捷标签 */
  onQuickTag(e: any) {
    const tag = e.currentTarget.dataset.tag;
    this.setData({ inputText: tag });
    this.doSend(tag);
  },

  /** 发送消息 */
  onSend() {
    if (!this.data.inputText.trim()) return;
    this.doSend(this.data.inputText);
  },

  /** 执行发送 */
  async doSend(message: string) {
    const msgId = `user-${Date.now()}`;

    // 添加用户消息
    const messages = [...this.data.messages, {
      id: msgId,
      role: 'user',
      content: message,
    }];

    this.setData({
      messages,
      inputText: '',
      isThinking: true,
      scrollToId: `msg-${msgId}`,
    });

    try {
      const resp = await request({
        url: `/task/${this.data.taskId}/chat`,
        method: 'POST',
        data: { message },
      });

      const aiData = resp.data;
      const aiMsgId = aiData.message_id;

      // 添加AI回复
      messages.push({
        id: aiMsgId,
        role: 'assistant',
        content: aiData.reply,
        changes: aiData.changes,
        applied: false,
        reverted: false,
      });

      this.setData({
        messages,
        isThinking: false,
        scrollToId: `msg-${aiMsgId}`,
        chatUsed: aiData.chat_rounds_used,
        matchScore: aiData.updated_match_score || this.data.matchScore,
        resumeText: aiData.updated_full_text || this.data.resumeText,
      });
    } catch (e: any) {
      this.setData({ isThinking: false });

      if (e.message?.includes('次数已达上限')) {
        wx.showModal({
          title: '对话次数已用完',
          content: '免费调整次数已用完，是否购买额外次数？',
          confirmText: '去购买',
          success: (res) => {
            if (res.confirm) {
              wx.navigateTo({ url: '/pages/pay/index/index' });
            }
          },
        });
      }
    }
  },

  /** 应用修改 */
  async onApply(e: any) {
    const msgId = e.currentTarget.dataset.msgid;
    try {
      await request({
        url: `/task/${this.data.taskId}/chat/${msgId}/action`,
        method: 'PUT',
        data: { action: 'apply' },
      });

      const messages = this.data.messages.map(m =>
        m.id === msgId ? { ...m, applied: true, reverted: false } : m
      );
      this.setData({ messages });

      wx.showToast({ title: '已应用', icon: 'success' });
    } catch (e) {
      wx.showToast({ title: '操作失败', icon: 'none' });
    }
  },

  /** 撤销修改 */
  async onRevert(e: any) {
    const msgId = e.currentTarget.dataset.msgid;
    try {
      await request({
        url: `/task/${this.data.taskId}/chat/${msgId}/action`,
        method: 'PUT',
        data: { action: 'revert' },
      });

      const messages = this.data.messages.map(m =>
        m.id === msgId ? { ...m, applied: false, reverted: true } : m
      );
      this.setData({ messages });

      wx.showToast({ title: '已撤销', icon: 'success' });
    } catch (e) {
      wx.showToast({ title: '操作失败', icon: 'none' });
    }
  },
});
