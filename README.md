# HelloAgents Trip Planner

基于多智能体架构的AI旅行规划助手，使用LLM生成个性化旅行计划。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Vue](https://img.shields.io/badge/Vue-3.4+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-red.svg)

## 功能特性

- 智能行程规划：根据目的地、日期、偏好自动生成旅行计划
- 景点推荐：基于用户偏好推荐适合的景点
- 预算估算：自动计算旅行费用明细
- 天气信息：提供旅行期间的天气预报
- 高德地图集成：可视化展示景点位置
- 行程编辑：支持手动调整景点顺序和删除景点
- 导出功能：支持导出为图片和PDF

## 技术栈

### 后端
- FastAPI - 现代化Web框架
- OpenAI/MiniMax - LLM API
- Pydantic - 数据验证
- 高德地图 API - 地理位置服务
- Unsplash - 图片服务

### 前端
- Vue 3 - 渐进式JavaScript框架
- TypeScript - 类型安全
- Ant Design Vue - UI组件库
- Vite - 构建工具
- 高德地图 JS API - 地图展示
- html2canvas + jsPDF - 导出功能

## 项目结构

```
helloagents-trip-planner/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── agents/         # 智能体模块
│   │   ├── api/            # API路由
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务服务
│   │   ├── config.py       # 配置管理
│   │   └── tools.py        # MCP工具
│   ├── main.py             # 应用入口
│   ├── requirements.txt    # Python依赖
│   └── .env.example        # 环境变量模板
└── frontend/               # 前端代码
    ├── src/
    │   ├── views/          # 页面组件
    │   ├── services/       # API服务
    │   ├── types/          # TypeScript类型
    │   └── router/         # 路由配置
    ├── package.json        # Node依赖
    └── vite.config.ts      # Vite配置
```

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd helloagents-trip-planner
```

### 2. 后端安装

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate      # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的API密钥
```

需要配置的API密钥：

| 配置项 | 说明 | 获取地址 |
|--------|------|----------|
| AMAP_API_KEY | 高德地图服务端Key | [高德开放平台](https://console.amap.com/dev/key/app) |
| AMAP_WEB_KEY | 高德地图JS Key | [高德开放平台](https://console.amap.com/dev/key/app) |
| UNSPLASH_ACCESS_KEY | Unsplash图片API | [Unsplash Developers](https://unsplash.com/developers) |
| LLM_API_KEY | LLM API密钥 | [OpenAI](https://platform.openai.com/) 或 [MiniMax](https://api.minimax.chat/) |
| LLM_BASE_URL | LLM API地址 | 根据选择的提供商填写 |
| LLM_MODEL | 模型名称 | 如: gpt-3.5-turbo, abab6.5-chat |

### 4. 前端安装

```bash
cd frontend

# 安装依赖
npm install
# 或
yarn install
```

## 运行项目

### 1. 启动后端

```bash
cd backend
python main.py
```

后端将运行在 `http://localhost:8000`

### 2. 启动前端

```bash
cd frontend
npm run dev
```

前端将运行在 `http://localhost:3000`

### 3. 访问应用

打开浏览器访问 `http://localhost:3000`

## API 接口

### GET /health
健康检查

### GET /api/trip/config
获取前端配置（高德地图Web Key等）

### POST /api/trip/plan
生成旅行计划

请求体：
```json
{
  "city": "杭州",
  "start_date": "2026-03-10",
  "end_date": "2026-03-12",
  "days": 3,
  "preferences": "历史文化",
  "budget": "中等",
  "transportation": "公共交通",
  "accommodation": "经济型酒店"
}
```

## 开发说明

### 后端开发

- 使用 `uvicorn` 作为ASGI服务器
- 热重载已启用，修改代码自动重启
- API文档: `http://localhost:8000/docs`

### 前端开发

- 使用 Vite 进行快速开发
- 支持 Vue DevTools 调试
- 代理配置已设置 `/api` 转发到后端

### 测试

运行后端测试：

```bash
cd backend

# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_models.py

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

## 构建部署

### 前端构建

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist` 目录

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request
