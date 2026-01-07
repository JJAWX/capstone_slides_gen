"""
Structure Agent - Designs detailed PPT structure based on outline and template knowledge.
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class StructureAgent:
    """
    结构设计代理 - 根据大纲和模板知识库设计详细的PPT结构
    
    功能：
    - 读取outline文件和模板知识库
    - 设计每个章节的页数分配
    - 为每一页选择合适的template
    - 确定每页的具体内容
    - 输出JSON格式的设计大纲
    """
    
    def __init__(self):
        """初始化结构代理"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("未找到OPENAI_API_KEY环境变量")
        
        self.client = OpenAI(api_key=api_key)
        
        # 加载模板知识库
        self.templates_guide = self._load_knowledge('templates_guide')
        
        self.system_prompt = f"""
你是一个专业的PPT结构设计专家。你的任务是根据提供的大纲和模板知识库，设计出详细的PPT结构。

【模板知识库】
{self.templates_guide}

【你的任务】
1. 分析大纲中的每个章节
2. 根据章节权重和内容，决定每个章节需要多少页幻灯片
3. 为每一页选择最合适的template
4. 确定每页的具体内容主题

【输出格式】
必须严格按照以下JSON格式输出：

{{
  "title": "PPT总标题",
  "total_slides": 总页数,
  "sections": [
    {{
      "section_number": 1,
      "section_title": "第1章：章节标题",
      "section_weight": 权重值,
      "slides_count": 该章节的页数,
      "slides": [
        {{
          "slide_number": 1,
          "slide_title": "标题页",
          "template": "title.xml",
          "content_type": "title_page",
          "content_description": "PPT封面，展示主标题和副标题"
        }},
        {{
          "slide_number": 2,
          "slide_title": "具体内容标题",
          "template": "content.xml",
          "content_type": "text_content",
          "content_description": "详细说明该页要展示的具体内容",
          "key_points": ["要点1", "要点2", "要点3"]
        }}
      ]
    }}
  ]
}}

【设计原则】
1. **页数分配**：
   - 权重9-10的章节：3-4页
   - 权重7-8的章节：2-3页
   - 权重5-6的章节：1-2页
   - 权重3-4的章节：1页

2. **模板选择**：
   - 第一页：使用title.xml
   - 纯文字说明：使用content.xml
   - 对比内容：使用two_content.xml
   - 需要配图说明：使用picture_content.xml
   - 数据表格：使用table_content.xml
   - 章节开始：使用section.xml
   - 最后一页：使用end.xml

3. **内容设计**：
   - 每页聚焦一个主题
   - 内容不要过于拥挤
   - 逻辑连贯，循序渐进
   - 考虑视觉平衡

请严格按照JSON格式输出，不要添加任何额外的解释或markdown代码块标记。
"""
    
    def _load_knowledge(self, knowledge_name: str) -> str:
        """
        从知识库加载知识文档
        
        Args:
            knowledge_name: 知识文档名称（不含.md后缀）
        
        Returns:
            知识文档内容
        """
        knowledge_dir = Path('knowledge')
        knowledge_file = knowledge_dir / f'{knowledge_name}.md'
        
        if not knowledge_file.exists():
            raise FileNotFoundError(f"知识文档不存在: {knowledge_file}")
        
        return knowledge_file.read_text(encoding='utf-8')
    
    def parse_outline(self, outline_path: str) -> Dict[str, Any]:
        """
        解析outline文件
        
        Args:
            outline_path: outline文件路径
        
        Returns:
            解析后的outline数据
        """
        with open(outline_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取元数据
        metadata = {}
        if content.startswith('---'):
            end_idx = content.find('---', 3)
            if end_idx != -1:
                metadata_text = content[3:end_idx]
                for line in metadata_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
                
                content = content[end_idx+3:].strip()
        
        # 提取标题
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else "未命名PPT"
        
        # 提取章节
        sections = []
        pattern = r'## (第\d+章：[^(]+) \(权重: (\d+)\)\n((?:- .+\n?)+)'
        
        for match in re.finditer(pattern, content):
            section_title = match.group(1).strip()
            weight = int(match.group(2))
            points_text = match.group(3)
            points = [line.strip('- ').strip() for line in points_text.split('\n') if line.strip()]
            
            sections.append({
                'title': section_title,
                'weight': weight,
                'key_points': points
            })
        
        return {
            'title': title,
            'metadata': metadata,
            'sections': sections
        }
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行结构设计任务
        
        Args:
            input_data: 包含以下键的字典
                - outline_path: outline文件路径（必需）
                或
                - outline_data: 已解析的outline数据（必需）
        
        Returns:
            包含设计结果的字典
        """
        try:
            # 获取outline数据
            if 'outline_path' in input_data:
                outline_path = input_data['outline_path']
                print(f"正在解析outline文件: {outline_path}")
                outline_data = self.parse_outline(outline_path)
            elif 'outline_data' in input_data:
                outline_data = input_data['outline_data']
            else:
                raise ValueError("必须提供outline_path或outline_data")
            
            print(f"开始设计PPT结构: {outline_data['title']}")
            
            # 构建用户提示
            user_prompt = self._build_user_prompt(outline_data)
            
            # 调用OpenAI生成结构设计
            print("正在调用OpenAI生成结构设计...")
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # 提取生成的JSON
            design_json_str = response.choices[0].message.content.strip()
            design_data = json.loads(design_json_str)
            
            # 添加元数据
            design_data['metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'model': 'gpt-4o',
                'source_outline': outline_data.get('metadata', {}),
                'total_sections': len(design_data.get('sections', []))
            }
            
            # 保存设计
            saved_path = self.save_design(design_data, outline_data['title'])
            
            result = {
                'design': design_data,
                'saved_path': saved_path,
                'timestamp': datetime.now().timestamp()
            }
            
            print(f"✓ 结构设计完成")
            print(f"  - 总页数: {design_data.get('total_slides', 0)}")
            print(f"  - 章节数: {len(design_data.get('sections', []))}")
            print(f"  - 保存位置: {saved_path}")
            
            return result
            
        except Exception as e:
            print(f"结构设计失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': f'结构设计失败: {str(e)}',
                'timestamp': datetime.now().timestamp()
            }
    
    def _build_user_prompt(self, outline_data: Dict[str, Any]) -> str:
        """
        构建发送给OpenAI的用户提示
        
        Args:
            outline_data: outline数据
        
        Returns:
            用户提示字符串
        """
        prompt_parts = [
            f"【PPT标题】\n{outline_data['title']}",
            f"\n【章节列表】"
        ]
        
        for i, section in enumerate(outline_data['sections'], 1):
            prompt_parts.append(f"\n章节 {i}：")
            prompt_parts.append(f"  标题：{section['title']}")
            prompt_parts.append(f"  权重：{section['weight']}/10")
            prompt_parts.append(f"  关键点：")
            for point in section['key_points']:
                prompt_parts.append(f"    - {point}")
        
        prompt_parts.append("\n\n【任务】")
        prompt_parts.append("请根据以上大纲，设计详细的PPT结构。")
        prompt_parts.append("为每个章节分配合适的页数，并为每一页选择最合适的template。")
        prompt_parts.append("确保结构合理，内容分布均衡。")
        
        return "\n".join(prompt_parts)
    
    def save_design(self, design_data: Dict[str, Any], title: str) -> str:
        """
        保存设计到JSON文件
        
        Args:
            design_data: 设计数据
            title: PPT标题
        
        Returns:
            保存的文件路径
        """
        # 创建输出目录
        output_dir = Path('outputs/design')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 清理文件名
        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"design_{safe_title}_{timestamp}.json"
        
        file_path = output_dir / filename
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(design_data, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def print_design_summary(self, design_data: Dict[str, Any]):
        """
        打印设计摘要
        
        Args:
            design_data: 设计数据
        """
        print("\n" + "="*60)
        print("PPT结构设计摘要")
        print("="*60)
        print(f"标题: {design_data.get('title', '未命名')}")
        print(f"总页数: {design_data.get('total_slides', 0)}")
        print(f"章节数: {len(design_data.get('sections', []))}")
        print("\n章节详情:")
        print("-"*60)
        
        for section in design_data.get('sections', []):
            print(f"\n{section.get('section_title', '')}")
            print(f"  权重: {section.get('section_weight', 0)}/10")
            print(f"  页数: {section.get('slides_count', 0)}")
            
            for slide in section.get('slides', []):
                template = slide.get('template', 'unknown')
                print(f"    • 第{slide.get('slide_number', 0)}页: {slide.get('slide_title', '')}")
                print(f"      模板: {template}")
        
        print("\n" + "="*60)


# 测试函数
if __name__ == "__main__":
    agent = StructureAgent()
    
    # 查找最新的outline文件
    outline_dir = Path('outputs/outlines')
    outline_files = sorted(outline_dir.glob('*.md'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not outline_files:
        print("错误: 未找到outline文件")
        exit(1)
    
    outline_file = outline_files[0]
    print(f"使用outline文件: {outline_file.name}")
    
    # 执行结构设计
    result = agent.execute({'outline_path': str(outline_file)})
    
    if 'error' not in result:
        # 打印设计摘要
        agent.print_design_summary(result['design'])
        
        print(f"\n完整设计已保存到: {result['saved_path']}")
    else:
        print(f"错误: {result['error']}")
