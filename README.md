# ResumeCraft - 基于事实的简历精修师

> 绝不捏造经历，只做精准翻译

## 项目结构

```
resume-craft/
├── docs/                  # 设计文档
├── server/                # FastAPI 后端
└── miniprogram/           # 微信小程序前端
```

## 技术栈

- **前端**: 微信小程序原生 (WXML + WXSS + TypeScript)
- **后端**: Python 3.11+ / FastAPI
- **数据库**: MongoDB (腾讯云)
- **存储**: 腾讯云 COS
- **AI**: 腾讯云智能体开发平台
- **支付**: 微信支付 API v3

## 快速开始

### 后端

```bash
cd server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 填写配置
uvicorn app.main:app --reload --port 8000
```

### 小程序

使用微信开发者工具打开 `miniprogram/` 目录。

## 文档

- [产品设计](docs/01-product-design.md)
- [架构设计](docs/02-architecture.md)
- [数据库设计](docs/03-database.md)
- [接口设计](docs/04-api.md)
