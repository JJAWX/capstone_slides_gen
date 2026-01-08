# 架构重构方案 - 基于 Slidev 的经验

## 当前问题分析

### 1. **XML Agent 的设计缺陷**
- **问题**：我们让 AI 生成 OpenXML 格式的幻灯片 XML，这非常复杂且容易出错
- **Slidev 的做法**：不生成 XML，而是生成 **Web 页面** + **截图** + **图片转 PPTX**

### 2. **文件输出策略正确**
- ✅ 每个 Agent 的输出保存到独立文件 (outlines/, structures/, contents/)
- ✅ 这样可以实现过程可视化和调试
- ✅ 与 `new_features` 分支的架构一致

### 3. **PPTX 生成方案需要改变**

## 重构方案

### 方案 A：借鉴 Slidev - 基于浏览器渲染（推荐）

```
工作流：
1. OutlineAgent → JSON (大纲)
2. StructureAgent → JSON (结构)
3. ContentAgent → JSON (内容)
4. DesignAgent → JSON (设计配置)
5. HTML Generator → 生成 HTML 幻灯片
6. Playwright → 渲染 + 截图
7. PptxGenJS → PNG → PPTX
```

**优势**：
- 不需要生成复杂的 OpenXML
- 可以使用 CSS 实现专业设计
- 可以预览幻灯片（浏览器查看）
- 渲染质量高（浏览器渲染）

**劣势**：
- 需要安装 Playwright
- 生成速度稍慢（需要启动浏览器）

### 方案 B：继续使用 python-pptx（当前方案改进）

```
工作流：
1. OutlineAgent → JSON
2. StructureAgent → JSON
3. ContentAgent → JSON
4. DesignAgent → JSON
5. PythonPPTX Generator → 直接生成 PPTX
```

**优势**：
- 不需要额外依赖
- 生成速度快
- 文本可选（不是图片）

**劣势**：
- python-pptx 的布局能力有限
- 设计不如浏览器渲染专业
- 需要手动处理每种布局

---

## 推荐方案：**方案 A（Slidev 风格）**

### 实施步骤

#### 第 1 步：创建 HTML 幻灯片生成器

```python
# backend/app/renderers/html_slide_renderer.py

class HTMLSlideRenderer:
    """将 JSON 数据渲染为 HTML 幻灯片"""
    
    def render_presentation(
        self,
        outline: dict,
        structure: dict,
        contents: List[dict],
        design: dict
    ) -> str:
        """生成完整的 HTML 演示文稿"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{outline['title']}</title>
            <style>
                {self._generate_css(design)}
            </style>
        </head>
        <body>
            {self._render_slides(contents, design)}
        </body>
        </html>
        """
        return html
```

#### 第 2 步：使用 Playwright 截图

```python
# backend/app/utils/playwright_exporter.py

from playwright.async_api import async_playwright

class PlaywrightExporter:
    """使用 Playwright 导出幻灯片"""
    
    async def export_slides_to_png(
        self,
        html_file: Path,
        output_dir: Path
    ) -> List[Path]:
        """将 HTML 幻灯片导出为 PNG"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                viewport={"width": 1920, "height": 1080}
            )
            
            await page.goto(f"file://{html_file}")
            
            # 截图每张幻灯片
            slides = await page.query_selector_all('.slide')
            png_files = []
            
            for i, slide in enumerate(slides):
                png_file = output_dir / f"slide_{i+1:03d}.png"
                await slide.screenshot(path=png_file)
                png_files.append(png_file)
            
            await browser.close()
            return png_files
```

#### 第 3 步：PNG 转 PPTX

```python
# backend/app/utils/pptx_packager_v2.py

from pptxgenjs import PptxGenJS

class PPTXPackagerV2:
    """将 PNG 图片打包成 PPTX"""
    
    def pack_pngs_to_pptx(
        self,
        png_files: List[Path],
        output_file: Path,
        title: str,
        notes: List[str] = None
    ):
        pptx = PptxGenJS()
        pptx.layout = '16:9'
        pptx.title = title
        
        for i, png_file in enumerate(png_files):
            slide = pptx.addSlide()
            
            # 将 PNG 作为背景
            with open(png_file, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode()
            
            slide.background = {
                'data': f'data:image/png;base64,{img_data}'
            }
            
            # 添加演讲备注
            if notes and i < len(notes):
                slide.addNotes(notes[i])
        
        pptx.save(output_file)
```

#### 第 4 步：修改 Workflow

```python
# backend/app/workflow/workflow_manager.py

class WorkflowManager:
    def __init__(self):
        # ... existing agents ...
        self.html_renderer = HTMLSlideRenderer()
        self.playwright_exporter = PlaywrightExporter()
        self.pptx_packager = PPTXPackagerV2()
    
    async def execute_workflow(self, deck_id, request, storage):
        # Steps 1-10: 现有的 Agent 工作流
        # ...
        
        # Step 11: 生成 HTML 幻灯片
        html_file = self._generate_html_slides(
            outline, structure, contents, design_config
        )
        
        # Step 12: 使用 Playwright 截图
        png_files = await self.playwright_exporter.export_slides_to_png(
            html_file, 
            self.output_dir / "pngs"
        )
        
        # Step 13: 打包成 PPTX
        pptx_file = self.pptx_dir / f"{deck_id}.pptx"
        self.pptx_packager.pack_pngs_to_pptx(
            png_files, 
            pptx_file, 
            outline["title"]
        )
        
        return pptx_file
```

---

## 当前项目优化建议（不完全重构）

如果不想大规模重构，可以：

### 1. 保留文件输出结构 ✅
- 已完成：每个 Agent 输出保存到独立文件
- 继续完善：添加更多中间步骤的文件保存

### 2. 移除 XML Agent
- XML Agent 太复杂，错误率高
- 改用 python-pptx 直接生成 PPTX

### 3. 简化最终生成步骤
```python
# 不需要：
# - XML Agent 生成 OpenXML
# - XML 合并
# - Review Agent 审核 XML

# 只需要：
def _generate_final_pptx(self, contents, design):
    prs = Presentation()
    
    for slide_data in contents:
        slide = prs.slides.add_slide(layout)
        # 直接从 JSON 填充内容
        self._populate_slide(slide, slide_data, design)
    
    prs.save(output_file)
```

### 4. 改进输出目录结构
```
backend/output/
  ├── {deck_id}/              # 每个任务一个目录
  │   ├── outline.json
  │   ├── structure.json
  │   ├── contents/
  │   │   ├── slide_001.json
  │   │   ├── slide_002.json
  │   ├── design.json
  │   └── final.pptx
```

---

## 最终建议

**短期优化**（1-2天）：
1. ✅ 保持当前的文件输出结构
2. 移除 XML Agent 和 Review Agent
3. 简化 PPTX 生成为直接使用 python-pptx
4. 为每个 deck_id 创建独立目录

**长期重构**（1-2周）：
1. 实现 HTML 渲染器
2. 集成 Playwright
3. 实现 PNG → PPTX 管道
4. 添加浏览器预览功能

你想先做短期优化，还是直接开始长期重构？
