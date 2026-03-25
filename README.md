# 多 Agent 智能独自旅行助手

一个面向**独自旅行用户**的 AI 行前规划产品原型。  
项目聚焦“**已确定目的地后的旅行规划**”场景，围绕用户在独自旅行中常见的**信息检索分散、行程组织繁琐、决策成本高**等问题，设计并实现了从需求输入、任务拆解、工具调用到结果生成的完整 AI 产品链路。

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Vue](https://img.shields.io/badge/Vue-3-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-API-red.svg)
![MCP](https://img.shields.io/badge/MCP-AMap-green.svg)

## 项目背景

独自旅行用户在出发前通常需要分别处理：

- 景点筛选
- 天气查询
- 酒店选择
- 餐饮安排
- 预算估算
- 日内交通与返程判断

传统方式往往依赖地图、OTA、内容平台等多个渠道反复切换，导致：

- 信息获取链路长，检索成本高
- 决策信息分散，难以快速形成完整方案
- 行程、预算、交通缺乏统一组织，执行成本高

基于此，项目将场景收敛为：

**用户已经确定目的地，希望快速获得一份适合独自旅行、结构完整、可参考执行的个性化行程方案。**

## 产品定位

本项目不是泛旅行攻略工具，也不是开放式目的地推荐产品。  
它的定位是一个**独自旅行场景下的 AI 行前规划 MVP**，优先解决“目的地已明确之后，如何高效完成旅行规划”这一问题。

### 当前版本聚焦

- 独自旅行
- 已确定目的地
- 行前规划
- 多约束输入下的方案生成

### 当前版本不聚焦

- 开放式目的地推荐
- 多人旅行协同决策
- 地图级路径最优解
- 内容社区型攻略分发

## 产品设计思路

### 1. 场景收敛

没有直接做“大而全的旅行助手”，而是优先聚焦：

- 独自旅行用户
- 已确定目的地后的行前规划场景

这样做的目的是在原型阶段控制复杂度，优先验证 AI 在复杂生活决策场景中的产品价值。

### 2. 需求拆解

围绕“帮用户规划一次独自旅行”这一需求，项目将核心任务拆解为六类：

- 天气查询
- 景点推荐
- 酒店推荐
- 餐饮推荐
- 每日行程描述生成
- 预算计算

同时补充了：

- 参数校验
- 错误处理
- 结果结构保护
- 局部降级与整链路兜底

### 3. 核心链路设计

项目采用以下主链路：

**用户输入与参数校验 → 多 Agent 任务拆解 → 外部服务查询或 LLM 生成 → 结果组装展示**

其中：

- 输入层负责收集城市、日期、预算、交通、住宿和独自旅行偏好
- 任务层将复杂规划问题拆成多个职责模块
- 执行层优先获取真实数据，不足部分由模型补全
- 展示层按“概览 → 独自旅行提醒 → 预算 → 每日行程”的顺序组织结果

## 核心产品能力

### 输入设计

当前版本保留了影响结果质量和用户决策的关键字段：

- 城市
- 开始日期 / 结束日期
- 预算
- 出行方式
- 住宿偏好
- 行程节奏偏好
- 安全偏好
- 夜间安排偏好

字段设计原则是：

**先保留影响生成结果结构和决策效率的核心变量，再逐步扩展增强字段。**

### 多 Agent 协作

项目采用任务拆解式多 Agent 协作方案，主要包括：

- Weather Agent
- Attraction Agent
- Hotel Agent
- Meal Agent
- Planner Agent

通过模块化分工，降低一次性生成导致的信息混乱、字段缺失和结果不稳定问题。

### 独自旅行特化

相较于普通旅行规划，项目额外强调：

- 独自旅行提醒
- 夜间安排建议
- 安全优先提示
- 节奏偏好适配
- 天气与日程调整建议

目标不是“生成一份攻略”，而是输出一份**更贴近单人出行决策过程**的可参考方案。

## 技术实现

### 前端

- Vue 3
- TypeScript
- Ant Design Vue
- 自定义自然纸面风格 UI

### 后端

- FastAPI
- 多 Agent 编排
- REST API / MCP 混合接入
- 参数校验、错误处理、健康检查、fallback 机制

### 外部能力

- 高德地图 POI / 天气 / 路线能力
- AMap MCP 接入
- Unsplash 图片增强
- OpenAI / MiniMax 兼容式 LLM 调用

## 可用性设计

为了避免 AI 原型“能跑但不稳定”，项目重点补充了以下机制：

- 参数校验：拦截无效输入
- 错误处理：统一转换内部异常和外部服务失败
- 结果结构保护：避免字段缺失导致页面崩溃
- partial fallback：局部降级，尽量保留真实结果
- full fallback：在外部服务或模型不可用时，仍返回基础可用方案

设计目标不是追求完美输出，而是优先保证：

**在限流、超时、配置异常等场景下，系统仍能返回可展示、可参考的行前规划结果。**

## 验证方式

项目围绕原型阶段的产品可用性设计了基础验证方案。  
当前已沉淀 benchmark case，用于验证：

- 结果结构完整性
- 关键字段覆盖情况
- 降级链路稳定性
- 端到端响应时延

### 当前 benchmark 覆盖

- 18 个 case
- 10 个核心场景
- 5 个压力场景
- 3 个降级场景

### 重点关注指标

- 任务成功率
- 结果完整性
- 关键字段覆盖率
- 降级链路稳定性
- 端到端响应时延

## 项目价值

这个项目的核心价值不只是“做出一个旅行 Demo”，而是验证了三件事：

1. AI 产品在复杂生活服务场景中，需要先做场景收敛，而不是盲目追求大而全
2. 多 Agent 任务拆解比单次大模型生成更适合处理结构复杂、约束较多的规划问题
3. AI 产品经理不仅要设计需求和链路，也需要理解模型、工具、异常和兜底机制，推动原型真正可用

## 项目结构

```text
helloagents-trip-planner/
├─ backend/
│  ├─ app/
│  │  ├─ agents/
│  │  ├─ api/
│  │  ├─ models/
│  │  ├─ services/
│  │  └─ utils/
│  ├─ tests/
│  ├─ .env.example
│  ├─ main.py
│  └─ requirements.txt
├─ benchmark/
│  ├─ benchmark_cases.json
│  ├─ benchmark_report_template.md
│  └─ run_benchmark.py
├─ frontend/
│  ├─ src/
│  │  ├─ router/
│  │  ├─ services/
│  │  ├─ types/
│  │  └─ views/
│  ├─ index.html
│  ├─ package.json
│  └─ vite.config.ts
├─ README.md
└─ REPAIR_REPORT.md
```

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

至少需要配置：

- `AMAP_API_KEY`
- `AMAP_WEB_KEY`
- `LLM_API_KEY`

可选配置：

- `USE_AMAP_MCP=true`
- `UNSPLASH_ACCESS_KEY`
- `LLM_BASE_URL`
- `LLM_PROVIDER`
- `LLM_MODEL`

### 3. 启动后端

```bash
cd backend
python main.py
```

后端默认运行在：

`http://localhost:8000`

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在：

`http://localhost:3000`

## API

### `GET /health`

健康检查。

### `GET /api/trip/config`

获取前端配置。

### `POST /api/trip/plan`

生成旅行方案。

请求示例：

```json
{
  "city": "青岛",
  "start_date": "2026-03-26",
  "end_date": "2026-03-31",
  "days": 6,
  "preferences": "历史文化,城市漫游",
  "budget": "medium",
  "transportation": "public",
  "accommodation": "economy",
  "pace_preference": "平衡",
  "safety_preference": "稳妥优先",
  "night_preference": "早归休息"
}
```

## 后续迭代方向

- 增加更多独自旅行约束，如体力强度、返程风险、拍照偏好
- 优化景点主题分配和跨天节奏设计
- 完善餐饮风格去重与本地特色优先逻辑
- 优化真实交通链路，逐步扩展到“景点—餐饮—住宿”的完整日内动线
- 继续探索 MCP 在多工具接入中的统一编排价值

## License

MIT
