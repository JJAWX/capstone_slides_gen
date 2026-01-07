"""
Content Agent - Generates detailed slide content based on outline sections and search results.
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class ContentAgent:
    """
    内容生成代理 - 根据大纲章节和搜索资料生成详细的PPT内容
    
    功能：
    - 接收大纲的某个章节
    - 结合搜索结果中的相关资料
    - 生成详细的PPT内容（markdown格式）
    - 保存到outputs/contents/目录
    """
    
    def __init__(self):
        """初始化内容代理"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("未找到OPENAI_API_KEY环境变量")
        
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = """
你是一个专业的PPT内容撰写专家。你的任务是根据提供的大纲章节和搜索资料，编写该章节的详细讲解内容。

【输出格式要求】
以自然段落的形式输出，类似一篇文章。不要使用过多的标题层级和要点符号，而是用流畅的段落来阐述内容。

格式示例：

# [章节标题]

[第一段：引入本章节的主题，概述核心内容]

[第二段：详细阐述第一个关键点，结合实例和数据]

[第三段：详细阐述第二个关键点，引用搜索资料中的信息]

[第四段：详细阐述第三个关键点，如有必要提供对比或案例]

[第五段：总结本章节的要点，为下一章节做铺垫]

【内容要求】
1. **自然流畅**：段落之间逻辑连贯，像在讲故事一样自然
2. **内容充实**：每段3-5句话，内容详实但不冗长
3. **引用数据**：自然地融入搜索资料中的数据和案例
4. **通俗易懂**：语言简洁明了，适合目标受众理解
5. **段落合理**：控制在4-6个段落，每段聚焦一个主题
6. **标注来源**：在段落中自然提及数据来源，如"根据XXX报告显示..."

【注意事项】
- 避免使用过多的列表和要点
- 段落要有起承转合，不是简单的信息堆砌
- 融入搜索资料的信息，但要自然，不生硬
- 保持专业性的同时兼顾可读性
- 总字数控制在800-1200字

请严格按照段落形式输出，不要添加"核心观点"、"详细内容"等额外的结构标签。
"""
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行内容生成任务
        
        Args:
            input_data: 包含以下键的字典
                - section_title: 章节标题（必需），如"第2章：机器学习的基本概念"
                - section_content: 章节的关键点列表（必需）
                - section_weight: 章节权重（可选）
                - search_results: 搜索结果JSON数据（可选）
                - target_audience: 目标受众（可选）
                - slide_number: 幻灯片编号（可选）
        
        Returns:
            包含生成内容的字典
        """
        try:
            # 提取输入数据
            section_title = input_data.get('section_title', '')
            section_content = input_data.get('section_content', [])
            section_weight = input_data.get('section_weight', 5)
            search_results = input_data.get('search_results', {})
            target_audience = input_data.get('target_audience', '通用受众')
            slide_number = input_data.get('slide_number', 1)
            
            if not section_title:
                raise ValueError("必须提供section_title")
            
            # 如果section_content是字符串，分割成列表
            if isinstance(section_content, str):
                section_content = [line.strip('- ').strip() for line in section_content.split('\n') if line.strip()]
            
            print(f"开始生成内容: {section_title}")
            
            # 构建用户提示
            user_prompt = self._build_user_prompt(
                section_title,
                section_content,
                section_weight,
                search_results,
                target_audience
            )
            
            # 调用OpenAI生成内容
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2500
            )
            
            # 提取生成的内容
            generated_content = response.choices[0].message.content.strip()
            
            # 添加元数据
            metadata = {
                'section_title': section_title,
                'slide_number': slide_number,
                'generated_at': datetime.now().isoformat(),
                'model': 'gpt-4o',
                'section_weight': section_weight,
                'target_audience': target_audience
            }
            
            # 保存内容
            saved_path = self.save_content(
                generated_content,
                metadata,
                section_title,
                slide_number
            )
            
            result = {
                'section_title': section_title,
                'slide_number': slide_number,
                'content': generated_content,
                'saved_path': saved_path,
                'metadata': metadata,
                'timestamp': datetime.now().timestamp()
            }
            
            print(f"✓ 内容生成完成，已保存到: {saved_path}")
            
            return result
            
        except Exception as e:
            print(f"内容生成失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': f'内容生成失败: {str(e)}',
                'section_title': input_data.get('section_title', ''),
                'timestamp': datetime.now().timestamp()
            }
    
    def _build_user_prompt(
        self,
        section_title: str,
        section_content: List[str],
        section_weight: int,
        search_results: Dict[str, Any],
        target_audience: str
    ) -> str:
        """
        构建发送给OpenAI的用户提示
        
        Args:
            section_title: 章节标题
            section_content: 关键点列表
            section_weight: 章节权重
            search_results: 搜索结果JSON对象（包含results数组）
            target_audience: 目标受众
        
        Returns:
            用户提示字符串
        """
        prompt_parts = [
            f"【章节信息】",
            f"标题：{section_title}",
            f"权重：{section_weight}/10",
            f"目标受众：{target_audience}",
            f"\n【大纲要点】"
        ]
        
        # 添加关键点
        for i, point in enumerate(section_content, 1):
            prompt_parts.append(f"{i}. {point}")
        
        # 添加搜索资料
        results_list = []
        if isinstance(search_results, dict):
            results_list = search_results.get('results', [])
        elif isinstance(search_results, list):
            results_list = search_results
        
        if results_list:
            prompt_parts.append("\n【参考资料】")
            prompt_parts.append("以下是搜索得到的相关资料，请自然地融入到文章内容中：\n")
            
            for i, result in enumerate(results_list[:5], 1):  # 最多使用5个搜索结果
                title = result.get('title', '无标题')
                snippet = result.get('snippet', '无摘要')
                url = result.get('url', '')
                domain = result.get('domain', '')
                
                prompt_parts.append(f"【资料{i}】")
                prompt_parts.append(f"来源：{domain}")
                prompt_parts.append(f"标题：{title}")
                prompt_parts.append(f"内容：{snippet[:300]}")
                if url:
                    prompt_parts.append(f"链接：{url}")
                prompt_parts.append("")
        else:
            prompt_parts.append("\n【参考资料】")
            prompt_parts.append("暂无搜索资料，请根据通用知识和大纲要点生成内容。")
        
        prompt_parts.append("\n【生成要求】")
        prompt_parts.append("请根据上述章节信息和参考资料，编写一篇流畅的文章。")
        prompt_parts.append("- 使用自然段落，不要过多使用列表")
        prompt_parts.append("- 自然融入参考资料中的信息")
        prompt_parts.append("- 覆盖所有大纲要点")
        prompt_parts.append("- 语言通俗易懂，适合目标受众")
        
        return "\n".join(prompt_parts)
    
    def save_content(
        self,
        content: str,
        metadata: Dict[str, Any],
        section_title: str,
        slide_number: int
    ) -> str:
        """
        保存生成的内容到文件
        
        Args:
            content: 生成的内容
            metadata: 元数据
            section_title: 章节标题
            slide_number: 幻灯片编号
        
        Returns:
            保存的文件路径
        """
        # 创建输出目录
        output_dir = Path('outputs/contents')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 清理文件名中的特殊字符
        safe_title = re.sub(r'[^\w\s-]', '', section_title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"slide_{slide_number:02d}_{safe_title}_{timestamp}.md"
        
        file_path = output_dir / filename
        
        # 构建完整的markdown内容（包含元数据）
        full_content = "---\n"
        for key, value in metadata.items():
            full_content += f"{key}: {value}\n"
        full_content += "---\n\n"
        full_content += content
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        return str(file_path)
    
    def generate_batch(
        self,
        sections: List[Dict[str, Any]],
        search_results_map: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量生成多个章节的内容
        
        Args:
            sections: 章节列表，每个章节包含title和content
            search_results_map: 章节标题到搜索结果的映射（可选）
        
        Returns:
            生成结果列表
        """
        results = []
        
        for i, section in enumerate(sections, 1):
            section_title = section.get('title', '')
            
            # 获取该章节对应的搜索结果
            search_results = []
            if search_results_map and section_title in search_results_map:
                search_results = search_results_map[section_title]
            
            input_data = {
                'section_title': section_title,
                'section_content': section.get('content', []),
                'section_weight': section.get('weight', 5),
                'search_results': search_results,
                'target_audience': section.get('target_audience', '通用受众'),
                'slide_number': i
            }
            
            result = self.execute(input_data)
            results.append(result)
        
        return results


# 测试函数
if __name__ == "__main__":
    agent = ContentAgent()
    
    # 模拟搜索结果JSON
    search_results = {
        'keywords': '机器学习基础',
        'total_results': 3,
        'results': [
            {
                'title': '监督学习和无监督学习的区别',
                'snippet': '监督学习使用标注的训练数据来学习输入和输出之间的映射关系，而无监督学习则从未标注的数据中发现模式和结构。在实际应用中，监督学习常用于分类和回归任务，比如图像识别和房价预测；无监督学习则用于聚类和降维，比如用户分群和数据可视化。',
                'url': 'https://example.com/ml-basics',
                'domain': 'example.com'
            },
            {
                'title': '机器学习中的特征工程',
                'snippet': '特征是描述数据的输入变量，标签是我们想要预测的目标变量。好的特征工程能够显著提升模型性能。例如，在预测房价时，房屋面积、位置、房间数量等都是特征，而房价本身就是标签。',
                'url': 'https://example.com/feature-engineering',
                'domain': 'example.com'
            },
            {
                'title': '数据集划分的最佳实践',
                'snippet': '在机器学习中，通常将数据集划分为训练集、验证集和测试集。常见的划分比例是70%训练、15%验证、15%测试。训练集用于训练模型，验证集用于调参，测试集用于最终评估模型的泛化能力。',
                'url': 'https://example.com/data-split',
                'domain': 'example.com'
            }
        ]
    }
    
    # 测试输入：模拟outline中的一个章节
    test_input = {
        'section_title': '第2章：机器学习的基本概念',
        'section_content': [
            '监督学习与无监督学习',
            '特征与标签的定义',
            '数据集的构建与划分'
        ],
        'section_weight': 8,
        'target_audience': '学生',
        'slide_number': 2,
        'search_results': search_results
    }
    
    result = agent.execute(test_input)
    
    print("\n" + "="*60)
    print("测试结果：")
    print("="*60)
    if 'error' not in result:
        print(f"章节标题: {result.get('section_title', '')}")
        print(f"保存路径: {result.get('saved_path', '')}")
        print(f"\n生成的内容：")
        print("="*60)
        print(result.get('content', ''))
    else:
        print(f"错误: {result.get('error', '')}")
