# ResumeCraft API 接口设计文档

> 版本：v1.0 MVP  
> 更新日期：2026-03-29  
> 基础路径：`/api/v1`

---

## 一、通用规范

### 1.1 请求格式

- **Content-Type**: `application/json`（文件上传除外）
- **认证方式**: JWT Bearer Token
- **请求头**: `Authorization: Bearer <token>`

### 1.2 统一响应格式

```json
{
  "code": 0,          // 0=成功，非0=失败
  "message": "success",
  "data": {}           // 响应数据
}
```

### 1.3 错误码定义

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | 参数校验失败 |
| 1002 | 未登录/Token过期 |
| 1003 | 权限不足 |
| 2001 | 用户不存在 |
| 3001 | 简历不存在 |
| 3002 | 简历解析失败 |
| 3003 | 文件格式不支持 |
| 3004 | 文件大小超限 |
| 4001 | 任务不存在 |
| 4002 | 任务处理失败 |
| 4003 | 免费次数已用完 |
| 4004 | 付费次数不足 |
| 4005 | 对话调整次数已达上限 |
| 5001 | 支付创建失败 |
| 5002 | 支付验签失败 |
| 5003 | 订单不存在 |
| 9999 | 系统内部错误 |

### 1.4 分页参数

```json
{
  "page": 1,       // 页码，从1开始
  "page_size": 20  // 每页数量，默认20，最大50
}
```

分页响应：

```json
{
  "code": 0,
  "data": {
    "list": [],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 二、认证模块 `/api/v1/auth`

### 2.1 微信登录

**POST** `/api/v1/auth/login`

用微信小程序 `wx.login()` 获取的 code 换取用户身份。

**请求参数**：

```json
{
  "code": "string"        // 必填，wx.login()返回的临时登录凭证
}
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOi...",           // JWT Token
    "expires_in": 7200,                  // Token有效期（秒）
    "user": {
      "id": "660a1b2c3d4e5f6789012345",
      "nickname": "",                    // 首次登录为空
      "avatar_url": "",
      "quota": {
        "free_daily_used": 0,
        "paid_remaining": 0
      },
      "is_new_user": true               // 是否新用户
    }
  }
}
```

**业务逻辑**：
1. 用 code 调用微信 `code2Session` 接口获取 openid
2. 查询用户是否存在，不存在则自动注册
3. 生成 JWT Token 返回

---

### 2.2 更新用户信息

**PUT** `/api/v1/auth/profile`

**请求参数**：

```json
{
  "nickname": "string",      // 可选
  "avatar_url": "string"     // 可选
}
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "id": "660a1b2c3d4e5f6789012345",
    "nickname": "小明",
    "avatar_url": "https://..."
  }
}
```

---

### 2.3 获取用户信息

**GET** `/api/v1/auth/profile`

**响应**：

```json
{
  "code": 0,
  "data": {
    "id": "660a1b2c3d4e5f6789012345",
    "nickname": "小明",
    "avatar_url": "https://...",
    "quota": {
      "free_daily_used": 1,
      "paid_remaining": 4,
      "chat_remaining": 9
    },
    "stats": {
      "total_tasks": 12,
      "total_resumes": 3
    },
    "created_at": "2026-03-29T10:00:00Z"
  }
}
```

---

## 三、简历模块 `/api/v1/resume`

### 3.1 上传简历文件

**POST** `/api/v1/resume/upload`

**Content-Type**: `multipart/form-data`

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | PDF或DOCX文件，最大10MB |
| title | string | 否 | 简历标题，默认"我的简历-{日期}" |

**响应**：

```json
{
  "code": 0,
  "data": {
    "resume_id": "660a1b2c3d4e5f6789012345",
    "title": "我的简历-20260329",
    "source_file": {
      "file_name": "张三_简历.pdf",
      "file_size": 524288
    },
    "parse_status": "pending"
  }
}
```

**业务逻辑**：
1. 校验文件类型（仅 PDF/DOCX）和大小（≤10MB）
2. 上传到腾讯云 COS
3. 创建 resume 记录，状态为 pending
4. 异步触发解析任务

---

### 3.2 解析简历（触发/查询）

**POST** `/api/v1/resume/{resume_id}/parse`

触发简历解析（如果尚未解析或需要重新解析）。

**响应**：

```json
{
  "code": 0,
  "data": {
    "resume_id": "660a1b2c3d4e5f6789012345",
    "parse_status": "parsing"
  }
}
```

---

### 3.3 获取简历解析结果

**GET** `/api/v1/resume/{resume_id}`

**响应**：

```json
{
  "code": 0,
  "data": {
    "id": "660a1b2c3d4e5f6789012345",
    "title": "我的简历-20260329",
    "source_type": "upload_pdf",
    "parse_status": "completed",
    "is_confirmed": false,
    "parsed_data": {
      "basic_info": {
        "name": "张三",
        "phone": "138****1234",
        "email": "zhangsan@example.com",
        "location": "深圳"
      },
      "education": [{
        "school": "华南理工大学",
        "degree": "本科",
        "major": "计算机科学",
        "start_date": "2016-09",
        "end_date": "2020-06"
      }],
      "experience": [{
        "company": "腾讯",
        "title": "高级后端工程师",
        "start_date": "2020-07",
        "end_date": "至今",
        "is_current": true,
        "description": "负责微信支付核心系统开发...",
        "keywords": ["Python", "Go", "微服务", "高并发"],
        "metrics": [
          { "text": "系统QPS从5000提升至20000", "type": "growth" }
        ],
        "responsibilities": ["核心系统架构设计", "团队Code Review"],
        "achievements": ["主导系统重构，性能提升300%"]
      }],
      "skills": [
        { "name": "Python", "category": "language", "level": "精通" },
        { "name": "Go", "category": "language", "level": "熟练" }
      ],
      "projects": [],
      "certifications": [],
      "additional": {
        "self_assessment": "5年后端开发经验..."
      }
    },
    "created_at": "2026-03-29T10:00:00Z"
  }
}
```

---

### 3.4 确认/修正解析结果

**PUT** `/api/v1/resume/{resume_id}/confirm`

用户确认或手动修正 AI 解析的结构化数据。

**请求参数**：

```json
{
  "parsed_data": {
    // 完整的结构化数据（用户修正后的版本）
    // 格式同 parsed_data 字段
  }
}
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "resume_id": "660a1b2c3d4e5f6789012345",
    "is_confirmed": true,
    "updated_at": "2026-03-29T10:05:00Z"
  }
}
```

---

### 3.5 获取简历列表

**GET** `/api/v1/resume/list?page=1&page_size=20`

**响应**：

```json
{
  "code": 0,
  "data": {
    "list": [
      {
        "id": "660a1b2c3d4e5f6789012345",
        "title": "我的简历-20260329",
        "source_type": "upload_pdf",
        "parse_status": "completed",
        "is_confirmed": true,
        "basic_info_summary": {
          "name": "张三",
          "latest_company": "腾讯",
          "latest_title": "高级后端工程师"
        },
        "created_at": "2026-03-29T10:00:00Z"
      }
    ],
    "total": 3,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 3.6 删除简历

**DELETE** `/api/v1/resume/{resume_id}`

**响应**：

```json
{
  "code": 0,
  "message": "删除成功"
}
```

**业务逻辑**：
1. 软删除（标记删除，不物理删除）
2. 关联的 COS 文件延迟清理

---

## 四、JD解析模块 `/api/v1/jd`

### 4.1 解析JD文本

**POST** `/api/v1/jd/parse`

**请求参数**：

```json
{
  "text": "string",          // JD文本（与url二选一）
  "url": "string"            // 招聘链接（与text二选一）
}
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "company": "字节跳动",
    "position": "高级后端工程师",
    "location": "北京",
    "required_skills": [
      { "name": "Go", "weight": 9 },
      { "name": "微服务", "weight": 8 },
      { "name": "高并发", "weight": 8 }
    ],
    "preferred_skills": [
      { "name": "Kubernetes", "weight": 6 },
      { "name": "大数据", "weight": 5 }
    ],
    "responsibilities": [
      "负责核心交易系统设计与开发",
      "主导系统架构优化和性能调优"
    ],
    "requirements": [
      "本科及以上学历",
      "5年以上后端开发经验"
    ],
    "keywords": [
      { "word": "Go", "weight": 9, "category": "language" },
      { "word": "微服务", "weight": 8, "category": "skill" },
      { "word": "团队管理", "weight": 7, "category": "soft_skill" }
    ]
  }
}
```

---

## 五、任务模块 `/api/v1/task`

### 5.1 创建优化任务

**POST** `/api/v1/task/create`

**请求参数**：

```json
{
  "resume_id": "string",     // 必填，选择的简历ID
  "jd_text": "string",       // JD文本（与jd_url二选一）
  "jd_url": "string"         // 招聘链接（与jd_text二选一）
}
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "task_id": "660a1b2c3d4e5f6789012346",
    "status": "analyzing_jd",
    "is_paid": false
  }
}
```

**业务逻辑**：
1. 校验简历是否已解析完成
2. 检查用户配额（免费/付费次数）
3. 创建任务，异步启动 AI 改写流程
4. 改写流程：解析JD → 匹配分析 → 改写 → 计算评分

---

### 5.2 获取任务结果

**GET** `/api/v1/task/{task_id}`

**响应（免费用户 - 未付费）**：

```json
{
  "code": 0,
  "data": {
    "id": "660a1b2c3d4e5f6789012346",
    "status": "completed",
    "is_paid": false,
    
    "jd_summary": {
      "company": "字节跳动",
      "position": "高级后端工程师",
      "top_keywords": ["Go", "微服务", "高并发"]
    },
    
    "match_score": {
      "before": 40,
      "after": null,
      "details": null
    },
    
    "preview": {
      "changes_count": 8,
      "missing_count": 2,
      "optimized_text": null,
      "changes": null
    },
    
    "need_pay": true,
    "pay_options": [
      { "type": "single", "name": "单次优化", "price": 390, "quantity": 1 },
      { "type": "pack_5", "name": "5次包", "price": 1490, "quantity": 5 },
      { "type": "pack_20", "name": "20次包", "price": 4990, "quantity": 20 }
    ],
    
    "created_at": "2026-03-29T10:10:00Z"
  }
}
```

**响应（已付费）**：

```json
{
  "code": 0,
  "data": {
    "id": "660a1b2c3d4e5f6789012346",
    "status": "completed",
    "is_paid": true,
    
    "jd": {
      "company": "字节跳动",
      "position": "高级后端工程师",
      "analysis": {
        "required_skills": [
          { "name": "Go", "weight": 9 }
        ],
        "keywords": [
          { "word": "Go", "weight": 9, "category": "language" }
        ]
      }
    },
    
    "result": {
      "match_score": {
        "before": 40,
        "after": 82,
        "details": {
          "skills_match": 75,
          "experience_match": 80,
          "keyword_match": 90,
          "education_match": 85
        }
      },
      "optimized_text": "张三\n高级后端工程师 | 深圳\n...",
      "changes": [
        {
          "section": "工作经历-腾讯",
          "section_type": "experience",
          "original": "负责微信支付核心系统开发，使用Python和Go...",
          "optimized": "主导微信支付核心交易系统架构设计与开发，基于Go微服务架构实现高并发交易处理（QPS 20000+）...",
          "reason": "JD要求Go和高并发经验，突出相关技术栈和指标",
          "matched_keywords": ["Go", "微服务", "高并发"]
        }
      ],
      "missing_items": [
        {
          "requirement": "Kubernetes容器化部署经验",
          "importance": "medium",
          "suggestion": "您的简历中未提及K8s经验，如果有相关项目经验建议补充"
        }
      ],
      "tips": [
        "建议将Go相关项目经历提前",
        "可以补充微服务架构的具体方案描述"
      ]
    },
    
    "chat_rounds_used": 1,
    "chat_rounds_limit": 3,
    
    "created_at": "2026-03-29T10:10:00Z",
    "completed_at": "2026-03-29T10:10:30Z"
  }
}
```

---

### 5.3 获取任务列表

**GET** `/api/v1/task/list?page=1&page_size=20`

**响应**：

```json
{
  "code": 0,
  "data": {
    "list": [
      {
        "id": "660a1b2c3d4e5f6789012346",
        "resume_title": "我的简历-20260329",
        "jd_summary": {
          "company": "字节跳动",
          "position": "高级后端工程师"
        },
        "match_score_before": 40,
        "match_score_after": 82,
        "status": "completed",
        "is_paid": true,
        "created_at": "2026-03-29T10:10:00Z"
      }
    ],
    "total": 12,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 5.4 对话式调整

**POST** `/api/v1/task/{task_id}/chat`

**请求参数**：

```json
{
  "message": "第二段工作经历重点突出团队管理能力"
}
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "message_id": "660a1b2c3d4e5f6789012347",
    "reply": "已调整第二段工作经历，重点突出了团队管理相关表述。",
    "changes": [
      {
        "section": "工作经历-ABC公司",
        "before": "负责后端系统开发，编写核心模块...",
        "after": "带领5人后端团队完成核心系统重构，制定代码规范和Review流程，推动团队效率提升40%..."
      }
    ],
    "updated_match_score": 85,
    "needs_confirmation": false,
    "chat_rounds_used": 2,
    "chat_rounds_remaining": 1,
    "updated_full_text": "完整更新后的简历文本..."
  }
}
```

**错误响应（超出对话次数）**：

```json
{
  "code": 4005,
  "message": "对话调整次数已达上限，请购买额外次数",
  "data": {
    "chat_rounds_used": 3,
    "chat_rounds_limit": 3,
    "extra_chat_price": 50
  }
}
```

---

### 5.5 应用/撤销对话修改

**PUT** `/api/v1/task/{task_id}/chat/{message_id}/action`

**请求参数**：

```json
{
  "action": "apply"          // "apply" | "revert"
}
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "action": "apply",
    "updated_match_score": 85,
    "updated_full_text": "应用修改后的完整简历文本..."
  }
}
```

---

### 5.6 导出PDF

**POST** `/api/v1/task/{task_id}/export`

**请求参数**：

```json
{
  "format": "pdf",            // "pdf" | "text"
  "template": "classic"       // "classic"（MVP只有一个模板）
}
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "download_url": "https://cos.example.com/exports/xxx.pdf?sign=...",
    "expires_in": 3600
  }
}
```

**业务逻辑**：
1. 用优化后的简历文本生成PDF
2. 上传到COS，生成临时访问URL（1小时有效）
3. 返回下载链接

---

## 六、支付模块 `/api/v1/pay`

### 6.1 获取商品列表

**GET** `/api/v1/pay/products`

**响应**：

```json
{
  "code": 0,
  "data": {
    "products": [
      {
        "type": "single",
        "name": "单次优化",
        "description": "1次完整改写 + 3轮对话调整 + PDF导出",
        "price": 390,
        "original_price": null,
        "quantity": 1,
        "badge": null
      },
      {
        "type": "pack_5",
        "name": "5次优化包",
        "description": "5次完整优化，每次含3轮对话调整",
        "price": 1490,
        "original_price": 1950,
        "quantity": 5,
        "badge": "最受欢迎"
      },
      {
        "type": "pack_20",
        "name": "20次优化包",
        "description": "20次完整优化，每次含3轮对话调整",
        "price": 4990,
        "original_price": 7800,
        "quantity": 20,
        "badge": "最划算"
      }
    ]
  }
}
```

---

### 6.2 创建支付订单

**POST** `/api/v1/pay/create`

**请求参数**：

```json
{
  "product_type": "single",  // "single" | "pack_5" | "pack_20"
  "task_id": "string"         // 可选，单次购买时关联的任务ID
}
```

**响应**：

```json
{
  "code": 0,
  "data": {
    "order_id": "660a1b2c3d4e5f6789012348",
    "order_no": "RC20260329100000001",
    "amount": 390,
    "wx_pay_params": {
      "timeStamp": "1711699200",
      "nonceStr": "abc123",
      "package": "prepay_id=wx2916...",
      "signType": "RSA",
      "paySign": "签名字符串"
    }
  }
}
```

**业务逻辑**：
1. 创建订单记录
2. 调用微信支付统一下单API（JSAPI下单）
3. 返回前端调起支付所需参数

---

### 6.3 微信支付回调

**POST** `/api/v1/pay/notify`

**说明**：微信支付异步通知回调接口，不需要认证。

**业务逻辑**：
1. 验证微信签名
2. 解密通知数据
3. 校验订单金额
4. 更新订单状态为 paid
5. 增加用户付费次数
6. 如关联了 task_id，标记任务为已付费
7. 返回成功响应给微信

**响应**（给微信支付的）：

```json
{
  "code": "SUCCESS",
  "message": "成功"
}
```

---

### 6.4 查询订单状态

**GET** `/api/v1/pay/order/{order_id}`

**响应**：

```json
{
  "code": 0,
  "data": {
    "order_id": "660a1b2c3d4e5f6789012348",
    "order_no": "RC20260329100000001",
    "product": {
      "type": "single",
      "name": "单次优化",
      "quantity": 1
    },
    "amount": 390,
    "status": "paid",
    "created_at": "2026-03-29T10:00:00Z",
    "paid_at": "2026-03-29T10:00:15Z"
  }
}
```

---

## 七、接口鉴权说明

### 7.1 无需鉴权的接口

| 接口 | 说明 |
|------|------|
| POST /api/v1/auth/login | 微信登录 |
| POST /api/v1/pay/notify | 微信支付回调 |

### 7.2 需要鉴权的接口

除上述两个外，所有接口均需在请求头携带 JWT Token。

### 7.3 Token 刷新机制

- Token 有效期：2小时
- 过期后前端自动调用 `wx.login()` 重新获取 code 登录
- 无需单独的刷新接口（小程序场景下直接重新登录更简洁）

---

## 八、接口限流

| 接口类别 | 限流策略 |
|---------|---------|
| 登录接口 | 10次/分钟/IP |
| 文件上传 | 5次/分钟/用户 |
| AI改写任务 | 10次/小时/用户 |
| 对话调整 | 20次/分钟/用户 |
| 支付接口 | 10次/分钟/用户 |
| 其他查询 | 60次/分钟/用户 |
