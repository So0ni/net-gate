# Net Gate

> 面向移动端测试场景的透明网络限速网关，支持按设备 MAC 地址独立模拟弱网、断网、3G、4G 等网络环境。

---

## 产品定位

移动端 App 测试中，开发者需要验证应用在各类网络条件下的表现。Net Gate 作为一个透明网关部署在局域网中，测试设备只需将默认网关指向它，无需安装任何证书或 Agent，即可被独立施加网络限速策略。

**核心能力：**

- 按 MAC 地址为每台设备独立配置网络策略
- 内置常用网络预设（3G / 4G / 弱网 / 断网），支持自定义
- 策略实时生效，无需重启
- Web 控制台统一管理，操作直观

---

## 设计哲学

**透明性优先**
网关对设备完全透明。设备侧只需修改默认网关 IP，流量自然流经 Net Gate，无感知。

**MAC 地址作为设备身份**
在局域网二层，MAC 地址是设备最稳定的标识符。所有策略以 MAC 地址为锚点，与 IP 地址变化无关。

**预设驱动，简单可控**
不暴露 tc/iptables 底层参数给用户，而是通过语义化的网络预设（Profile）来描述网络状态，降低使用门槛。高级用户可自定义预设参数。

**单容器，开箱即用**
整个服务打包为一个 Docker 镜像，前后端一体，一条命令启动，无外部依赖。

**最小化运行时状态**
设备与策略的绑定关系持久化到 SQLite，容器重启后自动恢复网络策略，不丢失配置。

---

## 技术选型

| 层次 | 技术 | 选型理由 |
|---|---|---|
| 后端框架 | Python + FastAPI | 异步支持好，调用系统命令简洁，自带 OpenAPI 文档 |
| Python 包管理 | uv | 极速依赖解析，替代 pip/virtualenv，lock 文件确保可复现 |
| 数据库 | SQLite + SQLAlchemy | 零依赖，单文件，适合配置型数据持久化 |
| 前端框架 | React + TypeScript | 组件化，类型安全 |
| 前端构建 | Vite | 开发体验好，构建快 |
| 前端样式 | Tailwind CSS v3 | 原子化 CSS，设计一致性强，v3 CLI 稳定 |
| 流量整形 | tc netem (Linux) | 内核级流量控制，支持延迟/抖动/丢包/带宽限速 |
| 数据包标记 | ebtables + iptables | L2 按 MAC 打 mark，L3 按 mark 路由到对应 tc class |
| 容器化 | Docker (multi-stage) | Stage 1 构建前端，Stage 2 运行 Python，单镜像交付 |
| 实时通信 | WebSocket | 推送设备在线状态变更 |

---

## 项目结构

```
network-gate/
├── Dockerfile                     # multi-stage：Node 构建前端 → Python 运行时
├── docker-compose.yml
├── .env.example
│
├── backend/
│   ├── pyproject.toml             # uv 项目配置与依赖声明
│   ├── uv.lock
│   ├── main.py                    # FastAPI 入口：挂载 /api 路由，托管前端静态文件
│   ├── config.py                  # 环境变量读取（端口、网卡名、数据库路径等）
│   │
│   ├── api/
│   │   ├── router.py              # 汇总所有子路由，统一注册 prefix=/api
│   │   ├── devices.py             # 设备管理接口
│   │   ├── profiles.py            # 网络预设接口
│   │   └── ws.py                  # WebSocket：/ws，推送设备状态
│   │
│   ├── core/                      # 系统能力封装层
│   │   ├── gateway.py             # 网关初始化：开启 ip_forward，建立 tc 根队列
│   │   ├── tc_manager.py          # tc netem 操作：为每个 mark 值配置 qdisc 参数
│   │   ├── ebtables_manager.py    # 将 MAC 地址映射到 nfmark
│   │   └── iptables_manager.py    # 将 nfmark 路由到对应 tc class
│   │
│   ├── services/
│   │   └── policy_service.py      # 业务逻辑：将设备与预设绑定，协调 core 层执行
│   │
│   ├── models/
│   │   ├── device.py              # ORM：Device 表
│   │   └── profile.py             # ORM：Profile 表
│   │
│   ├── schemas/
│   │   ├── device.py              # Pydantic：设备请求/响应结构
│   │   └── profile.py             # Pydantic：预设请求/响应结构
│   │
│   └── db.py                      # SQLite 初始化，内置预设种子数据
│
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts          # Tailwind v3 配置
    ├── tsconfig.json
    └── src/
        ├── main.tsx
        ├── App.tsx                 # 路由：/ → Dashboard，/profiles → Profiles
        ├── api/
        │   └── client.ts          # axios 实例，baseURL=/api，统一错误处理
        ├── hooks/
        │   └── useWebSocket.ts    # WebSocket 连接管理，设备状态订阅
        ├── components/
        │   ├── DeviceCard.tsx     # 单设备卡片：MAC / 别名 / 当前预设 / 快速切换
        │   ├── ProfileSelector.tsx # 预设下拉选择器
        │   └── StatusDot.tsx      # 在线状态指示点
        └── pages/
            ├── Dashboard.tsx      # 主页：设备列表总览
            └── Profiles.tsx       # 预设管理：增删改内置与自定义预设
```

---

## 数据模型

### Device（设备）

| 字段 | 类型 | 说明 |
|---|---|---|
| mac_address | TEXT PK | 设备 MAC 地址，格式 aa:bb:cc:dd:ee:ff |
| alias | TEXT | 用户自定义设备名称 |
| ip_address | TEXT | 最近一次观测到的 IP（手动录入） |
| profile_id | INTEGER FK | 当前绑定的网络预设 |
| mark_id | INTEGER | 分配给该设备的 nfmark 值（1-based 自增）|
| created_at | DATETIME | 注册时间 |

### Profile（网络预设）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | 预设名称，如 "3G" "弱网" |
| latency_ms | INTEGER | 单向延迟（毫秒） |
| jitter_ms | INTEGER | 延迟抖动（毫秒） |
| loss_percent | FLOAT | 丢包率（0-100） |
| bandwidth_kbps | INTEGER | 下行带宽限制（0 表示不限） |
| is_builtin | BOOLEAN | 是否为内置预设（不可删除） |

### 内置预设

| 名称 | 延迟 | 抖动 | 丢包 | 带宽 |
|---|---|---|---|---|
| 直连（无限速） | 0ms | 0ms | 0% | 不限 |
| 4G | 30ms | 10ms | 0.5% | 20Mbps |
| 3G | 100ms | 20ms | 1% | 1Mbps |
| 弱网 | 400ms | 100ms | 8% | 256Kbps |
| 断网 | — | — | 100% | — |

---

## API 路由概览

```
GET    /api/devices              # 获取所有已注册设备
POST   /api/devices              # 注册新设备（提交 MAC + 别名）
PATCH  /api/devices/{mac}        # 更新设备信息或绑定预设
DELETE /api/devices/{mac}        # 移除设备（并清除其流量规则）

GET    /api/profiles             # 获取所有预设
POST   /api/profiles             # 创建自定义预设
PATCH  /api/profiles/{id}        # 更新自定义预设
DELETE /api/profiles/{id}        # 删除自定义预设（内置不可删）

WS     /ws                       # 实时推送设备状态变更

GET    /                         # 前端入口（SPA index.html）
GET    /assets/*                 # 前端静态资源
```

---

## 部署架构

### 网络流量路径

```
测试设备（网关指向 Linux 主机 IP）
    ↓
Linux 主机（Docker 容器，network_mode: host）
    ├── ebtables: 匹配 MAC → 打 nfmark
    ├── iptables: 按 nfmark 路由到 tc class
    ├── tc netem: 施加延迟 / 丢包 / 带宽策略
    └── ip_forward: 转发到上游路由器
    ↓
上游路由器 / 互联网
```

### 容器配置要点

```yaml
# docker-compose.yml 关键配置
services:
  network-gate:
    build: .
    network_mode: host        # 共享宿主机网络栈，必须
    privileged: true          # 操作 tc / iptables / ebtables，必须
    environment:
      - INTERFACE=eth0        # 指定流量整形的网卡名
      - PORT=8080
      - DB_PATH=/data/gate.db
    volumes:
      - ./data:/data          # 可选：挂载 SQLite 文件到宿主机持久化
```

> **数据持久化说明：** 默认情况下 SQLite 文件存储在容器内部，容器删除后配置丢失。如需持久化，取消注释 `volumes` 配置，将 `./data` 目录挂载到宿主机。

### Dockerfile 构建流程

```
Stage 1 (node:20-alpine)
  → 安装前端依赖（npm install）
  → 构建前端（npm run build）
  → 产出 frontend/dist/

Stage 2 (python:3.12-slim)
  → 安装 uv
  → 通过 uv sync 安装 Python 依赖
  → 复制 backend/ 源码
  → 复制 frontend/dist/ → backend/static/
  → 启动 uvicorn
```

---

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| PORT | 8080 | 服务监听端口 |
| INTERFACE | eth0 | 执行流量整形的网卡名 |
| DB_PATH | /data/gate.db | SQLite 数据库文件路径 |
| LOG_LEVEL | info | 日志级别 |

---

## 依赖清单

### Backend（pyproject.toml）

- `fastapi` — Web 框架
- `uvicorn[standard]` — ASGI 服务器
- `sqlalchemy` — ORM
- `pydantic-settings` — 环境变量管理
- `websockets` — WebSocket 支持

### Frontend（package.json）

- `react` + `react-dom`
- `typescript`
- `vite`
- `tailwindcss@^3` + `postcss` + `autoprefixer`
- `axios`
- `react-router-dom`
