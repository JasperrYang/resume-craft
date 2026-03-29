/**
 * API 接口封装
 */
import { request, uploadFile } from './request';

/** 认证 */
export const authApi = {
  login: (code: string) =>
    request({ url: '/auth/login', method: 'POST', data: { code }, needAuth: false }),
  getProfile: () =>
    request({ url: '/auth/profile' }),
  updateProfile: (data: { nickname?: string; avatar_url?: string }) =>
    request({ url: '/auth/profile', method: 'PUT', data }),
};

/** 简历 */
export const resumeApi = {
  upload: (filePath: string, title?: string) =>
    uploadFile('/resume/upload', filePath, title ? { title } : undefined),
  parse: (resumeId: string) =>
    request({ url: `/resume/${resumeId}/parse`, method: 'POST' }),
  get: (resumeId: string) =>
    request({ url: `/resume/${resumeId}` }),
  confirm: (resumeId: string, parsedData: any) =>
    request({ url: `/resume/${resumeId}/confirm`, method: 'PUT', data: { parsed_data: parsedData } }),
  list: (page = 1, pageSize = 20) =>
    request({ url: `/resume?page=${page}&page_size=${pageSize}` }),
  delete: (resumeId: string) =>
    request({ url: `/resume/${resumeId}`, method: 'DELETE' }),
};

/** JD解析 */
export const jdApi = {
  parse: (text?: string, url?: string) =>
    request({ url: '/jd/parse', method: 'POST', data: { text, url } }),
};

/** 任务 */
export const taskApi = {
  create: (resumeId: string, jdText?: string, jdUrl?: string) =>
    request({ url: '/task/create', method: 'POST', data: { resume_id: resumeId, jd_text: jdText, jd_url: jdUrl } }),
  get: (taskId: string) =>
    request({ url: `/task/${taskId}` }),
  list: (page = 1, pageSize = 20) =>
    request({ url: `/task?page=${page}&page_size=${pageSize}` }),
  chat: (taskId: string, message: string) =>
    request({ url: `/task/${taskId}/chat`, method: 'POST', data: { message } }),
  chatAction: (taskId: string, messageId: string, action: 'apply' | 'revert') =>
    request({ url: `/task/${taskId}/chat/${messageId}/action`, method: 'PUT', data: { action } }),
  export: (taskId: string, format = 'pdf', template = 'classic') =>
    request({ url: `/task/${taskId}/export`, method: 'POST', data: { format, template } }),
};

/** 支付 */
export const payApi = {
  getProducts: () =>
    request({ url: '/pay/products' }),
  createOrder: (productType: string, taskId?: string) =>
    request({ url: '/pay/create', method: 'POST', data: { product_type: productType, task_id: taskId } }),
  getOrder: (orderId: string) =>
    request({ url: `/pay/order/${orderId}` }),
};
