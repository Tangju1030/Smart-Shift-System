# 智能年委排班系统

基于 **FastAPI + Vue3 + SQLite** 的智能值班排班系统，支持可视化配置规则、自动生成排班、AI辅助优化。

---

## 项目结构

```
智能年委排班系统/
├── backend/                    # 后端 (FastAPI)
│   ├── app.py                  # 应用入口
│   ├── database.py             # 数据库连接
│   ├── init_db.py              # 数据库初始化脚本
│   ├── requirements.txt        # Python依赖
│   ├── Dockerfile              # 后端容器
│   ├── models/                 # SQLAlchemy 数据模型
│   │   ├── user.py             # 值班人员
│   │   ├── schedule.py         # 排班结果/历史/课表
│   │   └── rule.py             # 规则配置
│   ├── schemas/                # Pydantic 请求/响应模型
│   │   ├── user.py
│   │   ├── schedule.py
│   │   └── rule.py
│   ├── scheduler/              # 排班引擎（核心算法）
│   │   ├── models.py           # 引擎数据模型
│   │   ├── constraints.py      # 约束层
│   │   ├── evaluator.py        # 评分层
│   │   ├── engine.py           # 搜索层+编排
│   │   └── parser.py           # Word/Excel课表解析
│   ├── services/               # 业务服务层
│   │   ├── user_service.py
│   │   ├── rule_service.py
│   │   ├── schedule_service.py
│   │   ├── export_service.py
│   │   └── ai_service.py       # AI 供应商抽象
│   └── routers/                # API 路由
│       ├── users.py
│       ├── rules.py
│       ├── schedule.py
│       ├── availability.py
│       └── ai.py
│
├── frontend/                   # 前端 (Vue3 + TS + Element Plus)
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── main.ts             # 入口
│       ├── App.vue
│       ├── router/index.ts     # 路由
│       ├── store/index.ts      # Pinia 状态管理
│       ├── types/index.ts      # TypeScript 类型
│       ├── api/                # API 调用
│       │   ├── index.ts
│       │   ├── users.ts
│       │   ├── rules.ts
│       │   ├── schedule.ts
│       │   └── ai.ts
│       ├── components/
│       │   └── Layout.vue      # 侧边栏布局
│       └── pages/
│           ├── Dashboard.vue   # 仪表盘
│           ├── Scheduler.vue   # 排班管理
│           ├── Settings.vue    # 规则配置+人员管理
│           └── AIAssistant.vue # AI 助手
│
├── docker-compose.yml          # Docker 部署编排
├── .env.example                # 环境变量模板
└── README.md
```

---

## 主要功能

- **仪表盘** — 在册人数、历史总记录、均衡度一目了然
- **排班管理** — 设置周次日期即可自动生成排班，支持 Word/CSV 导出
- **排班编辑** — 点击表格任意时段，可增删值班人员，累计次数实时更新
- **规则配置** — 每人每周次数上限、连续天开关、均衡权重、每时段人数等均可动态调整
- **课表管理** — 上传 Word/Excel 课表自动解析空闲时段，支持手动编辑
- **历史次数** — 支持批量导入历史值班次数，累计统计自动计算
- **AI 助手** — 支持 OpenAI/DeepSeek，可优化规则、解释排班结果、自由问答

---

## 快速开始

### 环境要求

| 组件 | 版本要求 |
|------|----------|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |

### 方式一：Docker 部署（推荐）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 AI_API_KEY（可选）

# 2. 启动
docker compose up -d

# 3. 访问
# 前端: http://localhost
# 后端API: http://localhost:8000/docs
```

### 方式二：本地开发

**后端：**

```bash
cd backend

# 创建虚拟环境
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（含37人默认名单）
python init_db.py

# 启动服务
uvicorn app:app --reload --port 8000
```

**前端：**

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问 http://localhost:5173
```

---

## API 接口

### 用户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users/` | 获取所有人员 |
| POST | `/api/users/` | 新增人员 |
| PUT | `/api/users/{id}` | 修改人员 |
| DELETE | `/api/users/{id}` | 删除人员 |
| POST | `/api/users/batch` | 批量导入 |
| GET | `/api/users/historical-counts` | 查看历史次数 |
| POST | `/api/users/historical-counts` | 导入历史次数 |

### 排班

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/schedule/generate` | 生成排班 |
| GET | `/api/schedule/result` | 查看排班结果 |
| GET | `/api/schedule/summary` | 仪表盘汇总 |
| GET | `/api/schedule/export/docx` | 导出 Word 值班表 |
| GET | `/api/schedule/export/csv` | 导出 CSV |
| PUT | `/api/schedule/slot/add` | 编辑：添加人员到时段 |
| DELETE | `/api/schedule/slot/remove` | 编辑：从时段移除人员 |

### 规则配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/rules/` | 获取所有规则 |
| GET | `/api/rules/config` | 获取解析后配置 |
| PUT | `/api/rules/config` | 更新全部配置 |
| PUT | `/api/rules/{key}` | 更新单个规则 |

### 课表管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/availability/{user_id}` | 获取某人课表 |
| PUT | `/api/availability/{user_id}` | 手动更新课表 |
| POST | `/api/availability/upload/docx` | 上传 Word 课表 |
| POST | `/api/availability/upload/xlsx` | 上传 Excel 课表 |

### AI 助手

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ai/optimize-rule` | AI 规则优化建议 |
| POST | `/api/ai/explain-schedule` | AI 解释排班 |
| POST | `/api/ai/chat` | AI 自由对话 |

---

## 排班规则可配置项

| 规则 | 默认值 | 说明 |
|------|--------|------|
| `max_weekly_shifts` | 2 | 每人每周最多值班次数 |
| `allow_consecutive_days` | false | 是否允许连续天值班 |
| `balance_weight` | 70 | 历史均衡权重 (0-100) |
| `randomness_weight` | 30 | 随机性权重 (0-100) |
| `search_iterations` | 200 | 多种子搜索次数 |
| `period_capacities` | 每节2人 | 每时段人数上限 (JSON) |

所有规则通过 Web 界面实时修改，修改后下次排班立即生效。

---

## 排班算法

### 三层架构

```
┌──────────────────────────────┐
│       Search Layer           │  ← 多种子搜索 + 早停
│   (engine.py)                │
├──────────────────────────────┤
│       Scoring Layer          │  ← 历史均衡 + 随机扰动 + 工作量
│   (evaluator.py)             │
├──────────────────────────────┤
│     Constraint Layer         │  ← 有课不排 / 次数限制 / 连续天
│   (constraints.py)           │
└──────────────────────────────┘
```

### 搜索策略

```
Phase 1 — 覆盖优先: 每人 ≤1次，优先空槽
Phase 2 — 填满优先: 已排1次者可获第2次，优先有人槽

择优: 遍历 N 个随机种子 → 取累计次数极差最小方案 → 极差≤1 时早停
```

---

## AI 功能

支持多家 LLM 供应商：

| 供应商 | 环境变量 |
|--------|----------|
| OpenAI | `AI_PROVIDER=openai` `AI_API_KEY=sk-...` |
| DeepSeek | `AI_PROVIDER=deepseek` `AI_API_KEY=sk-...` |
| Claude | 预留 |
| Gemini | 预留 |

### AI 能力

- **规则优化** — 分析当前规则和历史数据，给出参数调整建议
- **排班解释** — 用自然语言解释排班结果的合理性
- **自由对话** — 聊天式交互，回答任何排班相关问题

---

## 数据库

使用 SQLite（通过 SQLAlchemy ORM），5 张核心表：

| 表名 | 说明 |
|------|------|
| `users` | 值班人员（姓名、学号、班级、启用状态） |
| `historical_duty` | 历史值班记录（用于累计次数计算） |
| `schedule_result` | 排班结果（本周安排） |
| `availability` | 课表可用性（每个人的空闲时段） |
| `schedule_rules` | 规则配置（动态键值对） |

初始化脚本自动创建表并填充 37 人默认名单 + 8 条默认规则。

---

## 代码设计原则

1. **高内聚低耦合** — 引擎/服务/路由三层分离
2. **规则配置化** — 零硬编码：人数、时段数、约束强度均可动态调整
3. **算法模块独立** — Constraint / Evaluator / Engine 可独立测试和替换
4. **新增规则无需修改引擎** — 通过 `ScheduleConfig` 数据类注入
5. **AI 供应商抽象** — `AIProvider` 基类 + 工厂模式，新增供应商只需实现接口

---

## 从旧版迁移

旧版文件位于 `AI排班助手/` 文件夹：
- `scheduler.py` → 算法已重构为 `backend/scheduler/engine.py`
- `值班排班工具.html` → 功能已升级为 Vue3 SPA
- `第10周年委值班签到表.docx` → 模板可用 `POST /api/availability/upload/docx` 上传

课表文件（`课表word文档版/` 下的 .docx）可通过 API 批量导入。
