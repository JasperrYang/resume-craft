# ResumeCraft 数据库设计文档

> 版本：v1.0 MVP  
> 更新日期：2026-03-29  
> 数据库：MongoDB

---

## 一、数据库概览

### 数据库名称

```
resume_craft
```

### Collections 清单

| Collection | 说明 | 预估数据量(MVP) |
|-----------|------|----------------|
| users | 用户信息 | 1万+ |
| resumes | 简历库（结构化数据） | 3万+ |
| tasks | 优化任务 | 5万+ |
| orders | 支付订单 | 1万+ |
| chat_messages | 对话调整记录 | 10万+ |

---

## 二、Collection 详细设计

### 2.1 users（用户表）

```javascript
{
  _id: ObjectId,                    // MongoDB自动生成
  openid: String,                   // 微信小程序openid（唯一）
  unionid: String,                  // 微信unionid（可选，跨平台用）
  
  // 用户信息
  nickname: String,                 // 微信昵称
  avatar_url: String,               // 微信头像URL
  phone: String,                    // 手机号（加密存储，可选）
  
  // 会员与权益
  quota: {
    free_daily_used: Number,        // 今日已用免费次数
    free_daily_date: String,        // 免费次数日期标记 "2026-03-29"
    paid_remaining: Number,         // 付费剩余次数
    chat_remaining: Number          // 剩余对话调整次数
  },
  
  // 统计
  stats: {
    total_tasks: Number,            // 累计任务数
    total_resumes: Number,          // 累计简历数
    total_spent: Number             // 累计消费（分）
  },
  
  // 时间戳
  created_at: Date,                 // 注册时间
  updated_at: Date,                 // 最后更新
  last_login_at: Date               // 最后登录
}
```

**索引设计**：

```javascript
// 唯一索引
db.users.createIndex({ "openid": 1 }, { unique: true })

// unionid索引（跨平台查询）
db.users.createIndex({ "unionid": 1 }, { sparse: true })
```

---

### 2.2 resumes（简历表）

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,                // 关联用户
  
  // 基本信息
  title: String,                    // 简历标题，如"我的简历-2026春招"
  source_type: String,              // "upload_pdf" | "upload_docx" | "manual"
  source_file: {
    cos_key: String,                // COS文件路径
    cos_url: String,                // COS临时访问URL
    file_name: String,              // 原始文件名
    file_size: Number,              // 文件大小(字节)
    mime_type: String               // 文件MIME类型
  },
  
  // OCR原始文本
  raw_text: String,                 // OCR识别的原始文本
  
  // 结构化数据（核心：用户能力事实库）
  parsed_data: {
    
    // 基本信息
    basic_info: {
      name: String,                 // 姓名
      phone: String,                // 手机号
      email: String,                // 邮箱
      location: String,             // 所在城市
      birth_year: Number,           // 出生年份
      gender: String                // 性别
    },
    
    // 教育经历
    education: [{
      school: String,               // 学校名称
      degree: String,               // 学历："本科" | "硕士" | "博士" | "大专"
      major: String,                // 专业
      start_date: String,           // 开始日期 "2018-09"
      end_date: String,             // 结束日期 "2022-06"
      gpa: String,                  // GPA（可选）
      highlights: [String]          // 亮点，如"优秀毕业生"
    }],
    
    // 工作经历（核心）
    experience: [{
      company: String,              // 公司名称
      title: String,                // 职位名称
      department: String,           // 部门（可选）
      start_date: String,           // 开始日期
      end_date: String,             // 结束日期（"至今"或具体日期）
      is_current: Boolean,          // 是否当前在职
      description: String,          // 原始工作描述
      
      // AI提取的结构化标签
      keywords: [String],           // 关键词 ["Python", "数据分析", "团队管理"]
      metrics: [{                   // 量化指标
        text: String,               // "DAU从5万提升到15万"
        type: String                // "growth" | "scale" | "efficiency" | "revenue"
      }],
      responsibilities: [String],   // 核心职责列表
      achievements: [String]        // 核心成就列表
    }],
    
    // 项目经历
    projects: [{
      name: String,                 // 项目名称
      role: String,                 // 角色
      start_date: String,
      end_date: String,
      description: String,          // 项目描述
      tech_stack: [String],         // 技术栈
      highlights: [String]          // 项目亮点
    }],
    
    // 技能
    skills: [{
      name: String,                 // 技能名称
      category: String,             // 分类："language" | "framework" | "tool" | "soft_skill"
      level: String                 // 熟练度："精通" | "熟练" | "了解"（可选）
    }],
    
    // 证书/资质
    certifications: [{
      name: String,                 // 证书名称
      issuer: String,               // 颁发机构
      date: String                  // 获取日期
    }],
    
    // 其他（如自我评价、兴趣爱好）
    additional: {
      self_assessment: String,      // 自我评价
      languages: [String],          // 语言能力
      others: String                // 其他
    }
  },
  
  // 解析状态
  parse_status: String,             // "pending" | "parsing" | "completed" | "failed"
  parse_error: String,              // 解析失败原因
  
  // 用户是否已确认/修正
  is_confirmed: Boolean,            // 用户是否确认了解析结果
  
  // 时间戳
  created_at: Date,
  updated_at: Date
}
```

**索引设计**：

```javascript
// 用户ID索引
db.resumes.createIndex({ "user_id": 1 })

// 用户+创建时间复合索引（列表查询）
db.resumes.createIndex({ "user_id": 1, "created_at": -1 })

// 全文搜索索引（可选）
db.resumes.createIndex({ "raw_text": "text", "title": "text" })
```

---

### 2.3 tasks（优化任务表）

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,                // 关联用户
  resume_id: ObjectId,              // 关联的简历
  
  // JD信息
  jd: {
    raw_text: String,               // JD原始文本
    source_url: String,             // JD来源链接（可选）
    
    // AI解析的JD结构化数据
    analysis: {
      company: String,              // 公司名称
      position: String,             // 职位名称
      location: String,             // 工作地点
      salary_range: String,         // 薪资范围（可选）
      
      required_skills: [{           // 必须技能
        name: String,
        weight: Number              // 权重 1-10
      }],
      preferred_skills: [{          // 加分技能
        name: String,
        weight: Number
      }],
      responsibilities: [String],   // 核心职责
      requirements: [String],       // 硬性要求（学历、年限等）
      
      // 提取的全部关键词及权重
      keywords: [{
        word: String,
        weight: Number,             // 1-10
        category: String            // "skill" | "tool" | "soft_skill" | "domain"
      }]
    }
  },
  
  // 改写结果
  result: {
    // 匹配度评分
    match_score: {
      before: Number,               // 优化前匹配度 (0-100)
      after: Number,                // 优化后匹配度 (0-100)
      details: {
        skills_match: Number,       // 技能匹配度
        experience_match: Number,   // 经验匹配度
        keyword_match: Number,      // 关键词覆盖率
        education_match: Number     // 学历匹配度
      }
    },
    
    // 优化后的完整简历文本
    optimized_text: String,
    
    // 逐项改动记录
    changes: [{
      section: String,              // 改动区域，如"工作经历-腾讯"
      section_type: String,         // "experience" | "project" | "skill" | "summary"
      original: String,             // 改动前
      optimized: String,            // 改动后
      reason: String,               // 改动原因
      matched_keywords: [String]    // 本次改动匹配到的JD关键词
    }],
    
    // 缺失项
    missing_items: [{
      requirement: String,          // JD要求的内容
      importance: String,           // "high" | "medium" | "low"
      suggestion: String            // 建议（诚实说明）
    }],
    
    // 优化建议
    tips: [String]                  // 额外建议
  },
  
  // 对话调整轮次消耗
  chat_rounds_used: Number,         // 已用对话调整轮数
  chat_rounds_limit: Number,        // 对话调整上限（默认3）
  
  // 导出记录
  exports: [{
    type: String,                   // "pdf" | "text"
    cos_key: String,                // 导出文件COS路径
    created_at: Date
  }],
  
  // 任务状态
  status: String,                   // "pending" | "analyzing_jd" | "rewriting" | "completed" | "failed"
  error_message: String,            // 失败原因
  
  // 是否已付费（免费用户只能看评分）
  is_paid: Boolean,
  order_id: ObjectId,               // 关联的支付订单
  
  // 时间戳
  created_at: Date,
  updated_at: Date,
  completed_at: Date
}
```

**索引设计**：

```javascript
// 用户ID + 时间（列表查询）
db.tasks.createIndex({ "user_id": 1, "created_at": -1 })

// 状态索引（查询进行中的任务）
db.tasks.createIndex({ "status": 1 })

// 订单关联
db.tasks.createIndex({ "order_id": 1 }, { sparse: true })
```

---

### 2.4 chat_messages（对话调整记录表）

```javascript
{
  _id: ObjectId,
  task_id: ObjectId,                // 关联的任务
  user_id: ObjectId,                // 关联用户
  
  // 消息内容
  role: String,                     // "user" | "assistant" | "system"
  content: String,                  // 消息文本
  
  // AI回复的结构化数据（仅role=assistant时有值）
  ai_response: {
    reply: String,                  // AI的文字回复
    changes: [{                     // 本轮修改
      section: String,
      before: String,
      after: String
    }],
    updated_match_score: Number,    // 更新后的匹配度
    needs_confirmation: Boolean,    // 是否需要用户确认（事实数据变更时）
    confirmation_message: String    // 确认提示语
  },
  
  // 用户操作
  applied: Boolean,                 // 是否已应用该修改
  reverted: Boolean,                // 是否已撤销
  
  // 时间戳
  created_at: Date
}
```

**索引设计**：

```javascript
// 任务ID + 时间（获取对话历史）
db.chat_messages.createIndex({ "task_id": 1, "created_at": 1 })
```

---

### 2.5 orders（支付订单表）

```javascript
{
  _id: ObjectId,
  user_id: ObjectId,                // 关联用户
  
  // 订单信息
  order_no: String,                 // 商户订单号（唯一，格式：RC+时间戳+随机数）
  
  // 商品信息
  product: {
    type: String,                   // "single" | "pack_5" | "pack_20"
    name: String,                   // 商品名称
    quantity: Number,               // 包含次数
    unit_price: Number              // 单价（分）
  },
  
  // 金额
  amount: Number,                   // 订单总金额（分）
  
  // 微信支付信息
  wechat_pay: {
    prepay_id: String,              // 预支付交易会话标识
    transaction_id: String,         // 微信支付订单号
    pay_time: Date                  // 支付完成时间
  },
  
  // 订单状态
  status: String,                   // "pending" | "paid" | "failed" | "refunded" | "expired"
  
  // 关联信息
  task_id: ObjectId,                // 关联的任务（单次购买时）
  
  // 退款信息（如有）
  refund: {
    refund_id: String,
    amount: Number,
    reason: String,
    refunded_at: Date
  },
  
  // 时间戳
  created_at: Date,
  updated_at: Date,
  expired_at: Date                  // 订单过期时间（创建后30分钟）
}
```

**索引设计**：

```javascript
// 商户订单号唯一索引
db.orders.createIndex({ "order_no": 1 }, { unique: true })

// 用户ID + 时间
db.orders.createIndex({ "user_id": 1, "created_at": -1 })

// 微信支付订单号
db.orders.createIndex({ "wechat_pay.transaction_id": 1 }, { sparse: true })

// 状态 + 过期时间（定时清理过期订单）
db.orders.createIndex({ "status": 1, "expired_at": 1 })
```

---

## 三、数据关系图

```
users
  │
  ├── 1:N ──▶ resumes（一个用户多份简历）
  │
  ├── 1:N ──▶ tasks（一个用户多个任务）
  │              │
  │              ├── N:1 ──▶ resumes（每个任务关联一份简历）
  │              │
  │              ├── 1:N ──▶ chat_messages（每个任务多条对话）
  │              │
  │              └── 1:1 ──▶ orders（每个任务可关联一个订单）
  │
  └── 1:N ──▶ orders（一个用户多个订单）
```

---

## 四、数据迁移与备份策略

### 4.1 备份

| 策略 | 说明 |
|------|------|
| 全量备份 | 每日凌晨3:00自动备份（腾讯云MongoDB自带） |
| 增量备份 | oplog持续同步 |
| 保留周期 | 保留7天备份 |

### 4.2 数据清理

| 数据 | 清理策略 |
|------|---------|
| 过期未支付订单 | 30分钟后标记expired，每日批量清理 |
| 失败任务 | 保留7天后清理 |
| COS临时文件 | 设置生命周期，导出的PDF保留30天 |

---

## 五、性能考量

### 5.1 热点查询优化

| 查询场景 | 优化方式 |
|---------|---------|
| 用户登录查openid | openid唯一索引，O(1)查询 |
| 用户简历列表 | user_id + created_at复合索引 |
| 任务详情 | _id主键查询 |
| 对话历史 | task_id + created_at复合索引 |
| 订单查询 | order_no唯一索引 |

### 5.2 数据量预估

| 阶段 | 用户量 | 简历量 | 任务量 | 存储预估 |
|------|--------|--------|--------|---------|
| MVP | 1千 | 3千 | 5千 | < 500MB |
| 半年 | 1万 | 3万 | 5万 | < 5GB |
| 一年 | 5万 | 15万 | 25万 | < 25GB |
