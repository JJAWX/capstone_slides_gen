"""
XML Agent - 为单个幻灯片生成完整的XML代码

根据设计信息、内容文件和模板类型，生成符合Office Open XML格式的幻灯片XML
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class XMLAgent:
    """生成单个幻灯片的XML代码"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
        self.templates_dir = Path(__file__).parent.parent.parent / "templates"
        self.outputs_dir = Path(__file__).parent.parent.parent / "outputs"
        self.xml_output_dir = self.outputs_dir / "xml_slides"
        self.xml_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载所有模板文件
        self.templates = self._load_all_templates()
    
    def _load_all_templates(self) -> Dict[str, str]:
        """加载所有XML模板文件"""
        templates = {}
        template_files = [
            "title.xml",
            "content.xml",
            "two_content.xml",
            "picture_content.xml",
            "table_content.xml",
            "section.xml",
            "end.xml"
        ]
        
        for filename in template_files:
            template_path = self.templates_dir / filename
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    templates[filename] = f.read()
            else:
                print(f"⚠️  模板文件不存在: {filename}")
        
        return templates
    
    def execute(
        self,
        slide_info: Dict[str, Any],
        content_text: Optional[str] = None,
        section_title: Optional[str] = None
    ) -> str:
        """
        为单个幻灯片生成XML
        
        Args:
            slide_info: 幻灯片信息（来自design JSON）
                {
                    "slide_number": 1,
                    "slide_title": "标题",
                    "template": "content.xml",
                    "content_type": "text_content",
                    "content_description": "描述",
                    "key_points": ["point1", "point2"]
                }
            content_text: 生成的内容文本（来自content_agent的markdown文件）
            section_title: 章节标题（用于section页）
        
        Returns:
            生成的XML字符串
        """
        template_name = slide_info.get("template", "content.xml")
        slide_title = slide_info.get("slide_title", "")
        slide_number = slide_info.get("slide_number", 1)
        content_type = slide_info.get("content_type", "")
        
        # 获取模板内容
        template_xml = self.templates.get(template_name, "")
        if not template_xml:
            raise ValueError(f"未找到模板: {template_name}")
        
        print(f"正在为幻灯片 #{slide_number} 生成XML...")
        print(f"  • 标题: {slide_title}")
        print(f"  • 模板: {template_name}")
        print(f"  • 类型: {content_type}")
        
        # 调用OpenAI生成XML
        xml_content = self._generate_xml_with_openai(
            slide_info=slide_info,
            template_xml=template_xml,
            content_text=content_text,
            section_title=section_title
        )
        
        # 保存XML到文件
        output_filename = f"slide_{slide_number:03d}_{slide_title[:20]}.xml"
        output_path = self.xml_output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"✓ XML已保存: {output_filename}")
        
        return xml_content
    
    def _generate_xml_with_openai(
        self,
        slide_info: Dict[str, Any],
        template_xml: str,
        content_text: Optional[str],
        section_title: Optional[str]
    ) -> str:
        """使用OpenAI生成XML内容"""
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            slide_info=slide_info,
            template_xml=template_xml,
            content_text=content_text,
            section_title=section_title
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            xml_content = response.choices[0].message.content.strip()
            
            # 清理可能的markdown代码块标记
            if xml_content.startswith("```xml"):
                xml_content = xml_content[6:]
            if xml_content.startswith("```"):
                xml_content = xml_content[3:]
            if xml_content.endswith("```"):
                xml_content = xml_content[:-3]
            
            xml_content = xml_content.strip()
            
            return xml_content
            
        except Exception as e:
            print(f"❌ 生成XML时出错: {e}")
            raise
    
    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        return """你是一个专业的Office Open XML (OOXML) PPT生成专家。

你的任务是根据提供的模板和内容，生成完整、格式正确的PowerPoint幻灯片XML代码。

关键要求：
1. **严格遵守OOXML规范**: 使用正确的命名空间、元素结构和属性
2. **坐标系统**: 使用EMU (English Metric Units)，1英寸 = 914400 EMU
3. **标准页面尺寸**: 9144000 x 5143500 EMU (10英寸 x 5.625英寸, 16:9比例)
4. **文本格式化**:
   - 使用<a:r>和<a:t>标签包裹文本
   - sz属性表示字体大小（单位：1/100磅，例如sz="2400"表示24磅）
   - b="1"表示加粗，i="1"表示斜体
5. **段落格式**:
   - 使用<a:p>标签表示段落
   - <a:pPr>设置段落属性（对齐、缩进等）
   - lvl属性表示列表层级（0=一级，1=二级）
6. **占位符类型**:
   - type="title": 标题占位符
   - type="body": 正文占位符
   - type="subTitle": 副标题占位符

输出要求：
- 只输出完整的XML代码，不要有任何解释文字
- 保持XML格式正确、缩进清晰
- 确保所有标签正确闭合
- 替换模板中的占位文本为实际内容
"""
    
    def _build_user_prompt(
        self,
        slide_info: Dict[str, Any],
        template_xml: str,
        content_text: Optional[str],
        section_title: Optional[str]
    ) -> str:
        """构建用户提示"""
        
        template_name = slide_info.get("template", "")
        slide_title = slide_info.get("slide_title", "")
        content_type = slide_info.get("content_type", "")
        key_points = slide_info.get("key_points", [])
        
        prompt = f"""请为以下幻灯片生成完整的XML代码：

## 幻灯片信息
- 标题: {slide_title}
- 模板: {template_name}
- 内容类型: {content_type}

## 模板XML
```xml
{template_xml}
```

"""
        
        # 根据不同模板类型添加内容
        if template_name == "title.xml":
            # 标题页：主标题 + 副标题
            prompt += f"""## 内容要求
这是PPT封面页，请：
1. 主标题使用: "{slide_title}"
2. 副标题可以添加合适的描述文字（如"专业演示文稿"）

请替换模板中的"主标题"和"副标题"占位文本。
"""
        
        elif template_name == "section.xml":
            # 章节页：只有大标题
            section_text = section_title or slide_title
            prompt += f"""## 内容要求
这是章节分隔页，请：
1. 使用大标题: "{section_text}"
2. 保持简洁，无需额外内容

请替换模板中的"章节标题"占位文本。
"""
        
        elif template_name == "end.xml":
            # 结束页：感谢语
            prompt += f"""## 内容要求
这是结束页，请：
1. 主标题: "{slide_title}"
2. 可添加"感谢观看"、"谢谢"等结束语

请替换模板中的占位文本。
"""
        
        elif template_name == "content.xml":
            # 单栏内容页
            if content_text:
                prompt += f"""## 内容文本
{content_text}

## 内容要求
这是单栏内容页，请：
1. 标题: "{slide_title}"
2. 将内容文本转换为清晰的要点列表（3-5个要点）
3. 保持简洁，每个要点1-2行
4. 使用<a:p>段落分隔不同要点
5. 可以使用二级要点（lvl="1"）添加补充说明

请替换模板中的"内容标题"和"内容区域"占位文本。
"""
            elif key_points:
                points_text = "\n".join([f"- {point}" for point in key_points])
                prompt += f"""## 关键要点
{points_text}

## 内容要求
请将关键要点转换为格式化的XML内容。
"""
        
        elif template_name == "two_content.xml":
            # 双栏内容页
            if key_points and len(key_points) >= 2:
                prompt += f"""## 关键要点
- 左栏主题: {key_points[0]}
- 右栏主题: {key_points[1] if len(key_points) > 1 else key_points[0]}

## 内容文本
{content_text or ""}

## 内容要求
这是双栏对比页，请：
1. 标题: "{slide_title}"
2. 左栏展示第一个主题的内容（2-3个要点）
3. 右栏展示第二个主题的内容（2-3个要点）
4. 形成对比或互补关系

请替换模板中的占位文本，为左右两栏分别填充内容。
"""
        
        elif template_name == "picture_content.xml":
            # 图文混排页
            prompt += f"""## 内容要求
这是图文混排页，请：
1. 标题: "{slide_title}"
2. 文字区域：添加2-3个要点（基于内容或关键要点）
3. 图片区域：保留占位符（稍后会插入实际图片）

内容文本（如有）：
{content_text or ""}

关键要点（如有）：
{', '.join(key_points) if key_points else '无'}

请替换模板中的文字占位符，图片占位符保持不变。
"""
        
        elif template_name == "table_content.xml":
            # 表格页
            prompt += f"""## 内容要求
这是表格页，请：
1. 标题: "{slide_title}"
2. 创建一个简单的3x3表格（可根据内容调整）
3. 表格内容基于提供的关键要点或内容文本

内容文本（如有）：
{content_text or ""}

关键要点（如有）：
{', '.join(key_points) if key_points else '无'}

请生成包含表格的XML内容。
"""
        
        prompt += """

## 最终要求
- 输出完整的XML代码
- 确保所有文本内容被正确替换
- 保持XML格式正确
- 不要添加任何解释文字，只输出XML
"""
        
        return prompt
    
    def save_xml(self, xml_content: str, slide_number: int, slide_title: str) -> Path:
        """保存XML到文件"""
        filename = f"slide_{slide_number:03d}_{slide_title[:20]}.xml"
        output_path = self.xml_output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        return output_path


if __name__ == "__main__":
    # 测试XML Agent
    agent = XMLAgent()
    
    # 测试数据
    test_slide = {
        "slide_number": 2,
        "slide_title": "机器学习简介",
        "template": "content.xml",
        "content_type": "text_content",
        "content_description": "介绍机器学习的定义与重要性",
        "key_points": [
            "机器学习的定义",
            "机器学习的应用领域",
            "机器学习的发展历程"
        ]
    }
    
    test_content = """
机器学习是人工智能的一个重要分支，它使计算机系统能够从数据中学习和改进，
而无需进行明确的编程。通过分析大量数据，机器学习算法可以识别模式、
做出预测并不断优化性能。

在现代社会中，机器学习已经广泛应用于各个领域，包括图像识别、
自然语言处理、推荐系统等。从智能手机的语音助手到电商平台的个性化推荐，
机器学习技术正在深刻改变我们的生活方式。
"""
    
    print("=" * 60)
    print("测试 XML Agent")
    print("=" * 60)
    
    xml_output = agent.execute(
        slide_info=test_slide,
        content_text=test_content
    )
    
    print("\n" + "=" * 60)
    print("生成的XML预览 (前500字符)")
    print("=" * 60)
    print(xml_output[:500])
    print("...")
