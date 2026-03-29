import { request } from '../../../services/request';
Page({
  data: { products: [] as any[], selectedType: 'pack_5', taskId: '', paying: false },
  onLoad(options: any) {
    if (options.taskId) this.setData({ taskId: options.taskId });
    this.loadProducts();
  },
  async loadProducts() {
    const resp = await request({ url: '/pay/products' });
    this.setData({ products: resp.data.products });
  },
  onSelectProduct(e: any) { this.setData({ selectedType: e.currentTarget.dataset.type }); },
  async onPay() {
    this.setData({ paying: true });
    try {
      const resp = await request({
        url: '/pay/create', method: 'POST',
        data: { product_type: this.data.selectedType, task_id: this.data.taskId || undefined },
      });
      const params = resp.data.wx_pay_params;
      wx.requestPayment({
        timeStamp: params.timeStamp, nonceStr: params.nonceStr,
        package: params.package, signType: params.signType, paySign: params.paySign,
        success: () => {
          wx.showToast({ title: '购买成功', icon: 'success' });
          setTimeout(() => {
            if (this.data.taskId) {
              wx.redirectTo({ url: `/pages/task/result/result?id=${this.data.taskId}` });
            } else { wx.navigateBack(); }
          }, 1500);
        },
        fail: () => wx.showToast({ title: '支付取消', icon: 'none' }),
      });
    } catch (e) {
      wx.showToast({ title: '创建订单失败', icon: 'none' });
    } finally { this.setData({ paying: false }); }
  },
});
