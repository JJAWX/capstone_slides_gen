# Intelligent Slides Generator - Backend Analysis

## 项目概述

这是一个基于AI的PPT生成系统，使用FastAPI后端和Next.js前端。系统采用多Agent协作的工作流来生成专业的PowerPoint演示文稿。

## 架构设计

```
Browser (Next.js UI)
  ↓ call /api/decks (same origin)
Next.js Route Handlers (BFF)
  ↓ call FastAPI http://localhost:8000
FastAPI Pipeline
  - OpenAI outline/plan/compress
  - python-pptx render
  ↓ returns deckId/status/file
```

## 技术栈

### 后端
- **框架**: FastAPI (异步Web框架)
- **语言**: Python 3.8+
- **AI**: OpenAI GPT API
- **PPT生成**: python-pptx
- **数据验证**: Pydantic v2
- **图表生成**: Matplotlib + Pillow
- **图片搜索**: Unsplash API
- **服务器**: Uvicorn (ASGI服务器)

### 前端
- **框架**: Next.js 16.1.1
- **语言**: TypeScript
- **UI**: React + Ant Design
- **构建**: Turbopack

## API接口设计

### 基础信息
- **Base URL**: `http://localhost:8000`
- **认证**: 无 (开发环境)
- **数据格式**: JSON
- **CORS**: 允许 `http://localhost:3001`

### API端点

#### 1. GET `/`
健康检查和API信息
```json
{
  "message": "Intelligent Slides Generator API",
  "version": "1.0.0",
  "endpoints": [
    "GET /decks - List all decks",
    "POST /decks - Create new deck",
    "GET /decks/{deck_id}/status - Get deck status",
    "GET /decks/{deck_id}/download - Download deck file"
  ]
}
```

#### 2. GET `/decks`
获取所有演示文稿列表
- **响应**: 包含所有deck的基本信息和状态
```json
{
  "decks": [
    {
      "deckId": "uuid",
      "status": "done|error|processing",
      "progress": 100,
      "prompt": "AI in Healthcare",
      "slideCount": 10,
      "template": "corporate",
      "createdAt": "2024-01-01T00:00:00",
      "error": null
    }
  ],
  "total": 1
}
```

#### 3. POST `/decks`
创建新的演示文稿生成任务
- **请求体**: DeckRequest
- **响应**: 立即返回deckId，异步处理
- **后台任务**: 启动完整的工作流

**请求示例**:
```json
{
  "prompt": "AI in Healthcare: Transforming Patient Care",
  "slideCount": 10,
  "audience": "business",
  "template": "corporate"
}
```

**响应示例**:
```json
{
  "deckId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "outline",
  "message": "Deck generation started"
}
```

#### 4. GET `/decks/{deck_id}/status`
获取演示文稿生成状态
- **响应**: 当前进度和状态信息

**响应示例**:
```json
{
  "deckId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "content",
  "progress": 30,
  "currentStep": "Generating slide content...",
  "error": null
}
```

#### 5. GET `/decks/{deck_id}/download`
下载生成的PPT文件
- **条件**: status必须为"done"
- **响应**: PPTX文件下载
- **文件名**: `presentation-{deck_id}.pptx`

#### 6. DELETE `/decks/{deck_id}`
删除演示文稿及其文件
- **清理**: 删除文件和存储记录

## 数据模型

### 请求模型

#### DeckRequest
```python
class DeckRequest(BaseModel):
    prompt: str  # 演示文稿主题 (1-500字符)
    slideCount: int  # 幻灯片数量 (5-30)
    audience: Audience  # 目标受众
    template: Template  # 模板样式
```

**Audience类型**: `"technical" | "business" | "academic" | "general"`

**Template类型**:
```python
"corporate" | "academic" | "startup" | "minimal" |
"creative" | "nature" | "futuristic" | "luxury"
```

### 响应模型

#### DeckStatus
```python
"outline" | "analyze" | "content" | "charts" | "optimize" |
"layout" | "design" | "images" | "adjust" | "review" | "done" | "error"
```

#### SlideContent (核心内容模型)
```python
class SlideContent(BaseModel):
    title: str  # 幻灯片标题
    content: List[str]  #  bullet points
    paragraph: Optional[str]  # 详细段落文本
    table: Optional[TableData]  # 表格数据
    image_description: Optional[str]  # 图片描述
    image_url: Optional[str]  # 图片URL
    background_image_url: Optional[str]  # 背景图片URL
    chart_url: Optional[str]  # 图表图片路径
    chart_type: Optional[str]  # 图表类型: bar, line, pie, area, scatter
    slideType: Literal["title", "content", "comparison", "data", "table", "image", "narrative"]
    layout: Optional[SlideLayoutResponse]  # 布局信息
    notes: Optional[str]  # 演讲者备注
    content_role: Optional[Literal["outline", "detail", "summary"]]
    layout_adjustments: Optional[dict]  # 布局调整提示
```

## 生成工作流

### 工作流概述
系统采用11阶段的Agent-Based工作流，每个阶段由专门的Agent负责：

1. **大纲生成 (10%)** - `OutlineAgent`
2. **权重布局 (18%)** - 动态分配幻灯片数量
3. **内容生成 (30%)** - `ContentAgent` 并发生成
4. **图表生成 (36%)** - `ChartAgent` 数据可视化
5. **内容优化 (42%)** - 模板特定优化
6. **布局选择 (52%)** - `LayoutAgent` 选择最佳布局
7. **背景嵌入 (60%)** - `DesignAgent` + `ImageAgent`
8. **图片搜索 (70%)** - `ImageSearchAgent` Unsplash搜索
9. **布局调整 (80%)** - `LayoutAdjustmentAgent` 验证布局
10. **最终检查 (90%)** - `ReviewAgent` 质量审查
11. **生成完毕 (100%)** - `PPTXGenerator` 创建文件

### Agent架构

#### 核心Agent列表
- `OutlineAgent` - 大纲规划
- `ContentAgent` - 内容创作
- `ChartAgent` - 图表生成
- `LayoutAgent` - 布局选择
- `DesignAgent` - 视觉设计
- `ImageAgent` - 图片建议
- `ImageSearchAgent` - 图片搜索
- `LayoutAdjustmentAgent` - 布局调整
- `ReviewAgent` - 最终审查

#### Agent协作模式
```
WorkflowManager
├── 初始化所有Agent
├── 按顺序执行各阶段
├── 更新进度状态
└── 返回最终结果
```

## 文件存储架构

### 目录结构
```
backend/
├── app/                    # 应用代码
├── data/                   # 数据存储
│   └── decks.json         # 演示文稿元数据
├── output/                 # 生成的文件
│   ├── charts/            # 图表图片
│   └── *.pptx             # PPT文件
├── templates/             # PPT模板
└── requirements.txt       # 依赖
```

### 存储机制
- **内存存储**: 运行时状态管理
- **持久化**: JSON文件存储元数据
- **文件存储**: 本地文件系统存储PPT
- **图表缓存**: 自动清理临时图表文件

## 运行方式

### 开发环境启动
使用 `start-dev.sh` 脚本：
```bash
./start-dev.sh
```

该脚本会：
1. 检查环境变量文件
2. 启动FastAPI后端 (端口8001)
3. 启动Next.js前端 (端口3001)

### 手动启动

#### 后端启动
```bash
# 从项目根目录运行
python3 -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8001
```

#### 前端启动
```bash
npm run dev
```

### 环境配置

#### 后端环境变量 (backend/.env)
```bash
OPENAI_API_KEY=your_openai_api_key
OUTPUT_DIR=backend/output
TEMPLATES_DIR=backend/templates
```

#### 前端环境变量 (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## 依赖管理

### Python依赖 (requirements.txt)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-pptx==0.6.23
openai>=1.50.0
pydantic>=2.0.0,<3.0.0
matplotlib>=3.7.0
Pillow>=10.0.0
requests>=2.31.0
python-dotenv==1.0.0
```

### Node.js依赖 (package.json)
- Next.js 16.1.1
- React 18+
- Ant Design
- TypeScript

## 错误处理

### 状态码
- `200`: 成功
- `201`: 创建成功
- `400`: 请求错误
- `404`: 资源不存在
- `500`: 服务器错误

### 错误状态
- **error**: 生成失败，包含error字段
- **异常处理**: 所有异常都会记录到日志并更新状态

## 性能优化

### 异步处理
- FastAPI异步端点
- 后台任务处理生成
- 并发生成多个幻灯片内容

### 缓存策略
- 图表图片缓存
- 模板预加载
- 状态持久化

### 资源管理
- 自动清理临时文件
- 内存状态管理
- 文件系统监控

## 扩展点

### 新增Agent
1. 创建Agent类继承BaseAgent
2. 在WorkflowManager中初始化
3. 添加到工作流执行链

### 新增模板
1. 在templates目录添加.pptx文件
2. 更新Template类型定义
3. 添加模板特定优化逻辑

### 新增API端点
1. 在main.py中添加路由
2. 定义请求/响应模型
3. 实现业务逻辑

## 重构建议

### 架构优化
1. **微服务化**: 将Agent拆分为独立服务
2. **消息队列**: 使用Redis/RabbitMQ处理任务
3. **数据库**: 替换JSON文件存储为PostgreSQL
4. **缓存层**: 添加Redis缓存
5. **监控**: 添加Prometheus监控

### 代码优化
1. **依赖注入**: 使用依赖注入容器
2. **配置管理**: 集中化配置管理
3. **错误处理**: 统一的错误处理机制
4. **测试覆盖**: 增加单元测试和集成测试
5. **类型安全**: 完善TypeScript类型定义

### 性能优化
1. **并发处理**: 优化Agent并发执行
2. **流式生成**: 支持大文件流式下载
3. **CDN集成**: 图片和文件CDN加速
4. **缓存策略**: 智能缓存重复内容

---

*此文档基于现有代码分析生成，记录了完整的后端架构和API设计，为后续重构提供参考。*</content>
<parameter name="filePath">/Users/gigg1ty/Documents/GitHub/capstone_slides_gen/backend_analysis.md