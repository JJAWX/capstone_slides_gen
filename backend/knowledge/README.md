# 知识库目录

本目录包含PPT生成系统的相关知识文档，供各个Agent使用。

## 知识库列表

1. [PPT模板说明](templates_guide.md) - templates目录中各个XML模板的用途和使用方法
2. _更多知识文档待添加..._

## 知识库结构

```
knowledge/
├── README.md                 # 本文件
├── templates_guide.md        # PPT模板使用指南
└── [未来可添加更多知识文档]
```

## 使用方式

各个Agent可以通过读取这些知识文档来获取必要的背景知识：

```python
from pathlib import Path

# 读取知识库文档
knowledge_dir = Path('knowledge')
templates_guide = (knowledge_dir / 'templates_guide.md').read_text(encoding='utf-8')

# 在prompt中引用
system_prompt = f"""
参考以下知识库信息：

{templates_guide}

根据上述信息完成任务...
"""
```

## 知识库维护

- 添加新的知识文档时，请更新本README的知识库列表
- 保持文档格式统一，使用Markdown格式
- 包含清晰的示例和说明
- 定期更新和维护已有文档
