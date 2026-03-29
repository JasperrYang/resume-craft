/**
 * HTTP 请求封装
 */
const app = getApp<IAppOption>();

interface RequestOptions {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  data?: any;
  needAuth?: boolean;
}

interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

/**
 * 统一请求函数
 */
export function request<T = any>(options: RequestOptions): Promise<ApiResponse<T>> {
  const { url, method = 'GET', data, needAuth = true } = options;
  const baseUrl = app.globalData.baseUrl;

  const header: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (needAuth) {
    const token = app.globalData.token || wx.getStorageSync('token');
    if (token) {
      header['Authorization'] = `Bearer ${token}`;
    }
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${baseUrl}${url}`,
      method,
      data,
      header,
      success: (res: any) => {
        const resp = res.data as ApiResponse<T>;

        // Token 过期，重新登录
        if (resp.code === 1002) {
          app.login().then(() => {
            // 重试请求
            request<T>(options).then(resolve).catch(reject);
          }).catch(reject);
          return;
        }

        if (resp.code !== 0) {
          wx.showToast({ title: resp.message || '请求失败', icon: 'none' });
          reject(new Error(resp.message));
          return;
        }

        resolve(resp);
      },
      fail: (err) => {
        wx.showToast({ title: '网络异常', icon: 'none' });
        reject(err);
      },
    });
  });
}

/**
 * 上传文件
 */
export function uploadFile(
  url: string,
  filePath: string,
  formData?: Record<string, string>,
): Promise<ApiResponse> {
  const baseUrl = app.globalData.baseUrl;
  const token = app.globalData.token || wx.getStorageSync('token');

  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: `${baseUrl}${url}`,
      filePath,
      name: 'file',
      formData,
      header: {
        'Authorization': `Bearer ${token}`,
      },
      success: (res) => {
        const resp = JSON.parse(res.data) as ApiResponse;
        if (resp.code !== 0) {
          wx.showToast({ title: resp.message || '上传失败', icon: 'none' });
          reject(new Error(resp.message));
          return;
        }
        resolve(resp);
      },
      fail: (err) => {
        wx.showToast({ title: '上传失败', icon: 'none' });
        reject(err);
      },
    });
  });
}
