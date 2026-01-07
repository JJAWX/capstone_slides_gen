"""
Outline Agent - Generates structured PPT outlines from user prompts.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class OutlineAgent(BaseAgent):
    """
    Agent responsible for creating structured PPT outlines from user prompts.
    Generates hierarchical outlines with sections, weights, and key points.
    """

    def __init__(self):
        super().__init__()
        self.system_prompt = """
你是一个专业的PPT大纲生成专家。你的任务是根据用户提供的主题和要求，创建一个结构清晰、逻辑严谨的演示文稿大纲。

【严格输出格式要求】
你必须严格按照以下Markdown格式输出，格式必须完全一致：

# [演示文稿标题]

## 第1章：[章节标题] (权重: [1-10])
- 关键点1
- 关键点2
- 关键点3

## 第2章：[章节标题] (权重: [1-10])
- 关键点1
- 关键点2

【格式规范】
1. 标题：使用 # 开头，后跟具体标题
2. 章节：使用 ## 开头，格式为"第X章：[标题] (权重: Y)"，其中X是数字，Y是1-10的权重
3. 关键点：使用 - 开头，每个章节至少2个关键点
4. 章节数量：根据内容需要，合理控制在5-12个章节
5. 权重分配：重要章节权重高(8-10)，次要章节权重低(3-7)

【内容要求】
1. 大纲结构完整，逻辑清晰
2. 章节标题简洁明了
3. 关键点具体可操作
4. 适合目标观众类型
5. 符合演示文稿的篇幅要求

【示例输出】
# 人工智能在医疗健康领域的应用

## 第1章：引言 (权重: 6)
- 人工智能的定义和医疗应用背景
- 当前医疗健康领域的挑战
- 演示文稿结构和目标

## 第2章：AI诊断应用 (权重: 9)
- 医学影像AI分析技术
- 病理学自动诊断系统
- 实时健康监测预警

请确保输出格式完全符合上述规范，不要添加任何额外的说明或注释。
"""

    async def execute(self, user_prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a structured PPT outline from user prompt.

        Args:
            user_prompt: User's description of the PPT topic and requirements

        Returns:
            Dict containing the generated outline in markdown format
        """
        try:
            logger.info(f"Generating outline for prompt: {user_prompt[:100]}...")

            # Validate input
            if not user_prompt or len(user_prompt.strip()) < 10:
                raise ValueError("User prompt must be at least 10 characters long")

            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"请根据以下要求生成PPT大纲：\n\n{user_prompt}"}
            ]

            # Call OpenAI API
            outline_md = await self.call_openai(
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )

            # Parse the outline to extract structured data
            structured_outline = self._parse_outline_md(outline_md)

            # Save outline to file
            file_path = self._save_outline_to_file(outline_md, user_prompt)

            logger.info(f"Outline generation completed successfully, saved to: {file_path}")

            return {
                "outline_markdown": outline_md,
                "structured_outline": structured_outline,
                "file_path": file_path,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Outline generation failed: {str(e)}")
            return {
                "outline_markdown": "",
                "structured_outline": {},
                "status": "error",
                "error": str(e)
            }

    def _parse_outline_md(self, markdown: str) -> Dict[str, Any]:
        """
        Parse markdown outline into structured data.

        Args:
            markdown: The generated markdown outline

        Returns:
            Structured outline data
        """
        try:
            lines = markdown.strip().split('\n')
            structured = {
                "title": "",
                "sections": []
            }

            current_section = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Main title
                if line.startswith('# ') and not structured["title"]:
                    structured["title"] = line[2:].strip()
                    continue

                # Section headers
                if line.startswith('## '):
                    # Save previous section if exists
                    if current_section:
                        structured["sections"].append(current_section)

                    # Extract section title and weight
                    section_text = line[3:].strip()
                    title = section_text
                    weight = 5  # default weight

                    # Try to extract weight from parentheses
                    if '(' in section_text and ')' in section_text:
                        try:
                            weight_part = section_text.split('(')[-1].split(')')[0]
                            if '权重:' in weight_part:
                                weight = int(weight_part.split(':')[1].strip())
                                title = section_text.split('(')[0].strip()
                        except:
                            pass

                    current_section = {
                        "title": title,
                        "weight": weight,
                        "key_points": []
                    }
                    continue

                # Bullet points
                if line.startswith('- ') and current_section:
                    current_section["key_points"].append(line[2:].strip())

            # Add the last section
            if current_section:
                structured["sections"].append(current_section)

            return structured

        except Exception as e:
            logger.error(f"Failed to parse outline markdown: {str(e)}")
            return {"title": "解析失败", "sections": []}

    async def refine_outline(self, original_outline: str, feedback: str) -> Dict[str, Any]:
        """
        Refine an existing outline based on user feedback.

        Args:
            original_outline: The original markdown outline
            feedback: User feedback for improvements

        Returns:
            Refined outline
        """
        try:
            messages = [
                {"role": "system", "content": "你是一个PPT大纲优化专家。请根据用户反馈优化现有大纲。"},
                {"role": "user", "content": f"原始大纲：\n{original_outline}\n\n用户反馈：{feedback}\n\n请优化这个大纲。"}
            ]

            refined_outline = await self.call_openai(
                messages=messages,
                temperature=0.6,
                max_tokens=2000
            )

            return {
                "refined_outline": refined_outline,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Outline refinement failed: {str(e)}")
            return {
                "refined_outline": original_outline,
                "status": "error",
                "error": str(e)
            }

    def _save_outline_to_file(self, outline_md: str, user_prompt: str) -> str:
        """
        Save the generated outline to a markdown file in outputs/outlines directory.

        Args:
            outline_md: The generated markdown outline
            user_prompt: Original user prompt for filename generation

        Returns:
            Path to the saved file
        """
        try:
            # Create outputs/outlines directory if it doesn't exist
            outlines_dir = Path(__file__).resolve().parent.parent.parent / "outputs" / "outlines"
            outlines_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename based on timestamp and prompt preview
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prompt_preview = user_prompt[:30].replace(" ", "_").replace("/", "_")
            filename = f"outline_{timestamp}_{prompt_preview}.md"
            file_path = outlines_dir / filename

            # Add metadata header to the markdown
            metadata_header = f"""---
generated_at: {datetime.now().isoformat()}
user_prompt: {user_prompt.replace(chr(10), ' ').replace(chr(13), ' ')}
model: {self.model}
---

"""

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(metadata_header)
                f.write(outline_md)

            logger.info(f"Outline saved to: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to save outline to file: {str(e)}")
            raise e