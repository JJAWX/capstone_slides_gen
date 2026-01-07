"""
完整的PPT生成工作流 - 新版本

工作流程：
1. Outline Agent - 生成大纲
2. Structure Agent - 设计详细PPT结构（分配页数、模板）
3. 并发处理每个章节：
   - Search Agent - 搜索相关资料
   - Content Agent - 生成文案内容
4. XML Agent - 异步生成每张幻灯片的XML
5. 合并所有XML
6. PPTX Generator - 生成最终PPTX文件
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.agents.outline_agent import OutlineAgent
from app.agents.structure_agent import StructureAgent
from app.agents.search_agent import SearchAgent
from app.agents.content_agent import ContentAgent
from app.agents.xml_agent import XMLAgent
from app.utils.pptx_packager import PPTXPackager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PPTWorkflowManager:
    """完整的PPT生成工作流管理器"""
    
    def __init__(self):
        """初始化所有agents"""
        self.outline_agent = OutlineAgent()
        self.structure_agent = StructureAgent()
        self.search_agent = SearchAgent()
        self.content_agent = ContentAgent()
        self.xml_agent = XMLAgent()
        self.packager = PPTXPackager()
        
        # 输出目录 - 统一到backend/outputs/下
        self.backend_dir = Path(__file__).parent.parent.parent
        self.outputs_dir = self.backend_dir / "outputs"
        self.outlines_dir = self.outputs_dir / "outlines"
        self.design_dir = self.outputs_dir / "design"
        self.search_results_dir = self.outputs_dir / "search_results"
        self.contents_dir = self.outputs_dir / "contents"
        self.xml_slides_dir = self.outputs_dir / "xml_slides"
        self.pptx_dir = self.outputs_dir / "pptx"
        
        # 确保目录存在
        for dir_path in [self.outlines_dir, self.design_dir, self.search_results_dir, 
                         self.contents_dir, self.xml_slides_dir, self.pptx_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    async def generate_ppt_from_prompt(
        self,
        user_prompt: str,
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从用户提示生成完整的PPT
        
        Args:
            user_prompt: 用户输入的PPT主题和要求
            output_filename: 输出文件名（可选）
        
        Returns:
            包含所有生成文件路径的结果字典
        """
        
        print("=" * 80)
        print("开始PPT生成工作流")
        print("=" * 80)
        print(f"\n用户提示: {user_prompt}\n")
        
        result = {
            "user_prompt": user_prompt,
            "start_time": datetime.now().isoformat(),
            "steps": {}
        }
        
        try:
            # ==================== 步骤 1: 生成大纲 ====================
            print("\n" + "▶" * 40)
            print("步骤 1/6: 生成PPT大纲")
            print("▶" * 40)
            
            outline_result = await self.outline_agent.execute(user_prompt)
            outline_file = Path(outline_result.get("file_path", ""))
            
            if not outline_file.exists():
                raise FileNotFoundError(f"大纲文件未找到: {outline_file}")
            
            print(f"✓ 大纲已保存: {outline_file.name}")
            result["steps"]["outline"] = {
                "file": str(outline_file),
                "status": "completed"
            }
            
            # ==================== 步骤 2: 设计PPT结构 ====================
            print("\n" + "▶" * 40)
            print("步骤 2/6: 设计PPT结构（分配页数和模板）")
            print("▶" * 40)
            
            structure_result = self.structure_agent.execute({"outline_path": str(outline_file)})
            design_data = structure_result.get("design", {})
            design_file = Path(structure_result.get("saved_path", ""))
            
            if not design_file.exists():
                raise FileNotFoundError(f"设计文件未找到: {design_file}")
            
            print(f"✓ 设计已保存: {design_file.name}")
            print(f"  - 总页数: {design_data.get('total_slides', 0)}")
            print(f"  - 章节数: {len(design_data.get('sections', []))}")
            
            result["steps"]["structure"] = {
                "file": str(design_file),
                "total_slides": design_data.get('total_slides', 0),
                "sections_count": len(design_data.get('sections', [])),
                "status": "completed"
            }
            
            # ==================== 步骤 3: 并发搜索和内容生成 ====================
            print("\n" + "▶" * 40)
            print("步骤 3/6: 并发处理 - 搜索资料 + 生成文案")
            print("▶" * 40)
            
            sections = design_data.get("sections", [])
            search_content_results = await self._process_sections_concurrently(sections)
            
            print(f"\n✓ 完成 {len(search_content_results)} 个章节的搜索和内容生成")
            
            result["steps"]["search_and_content"] = {
                "sections_processed": len(search_content_results),
                "status": "completed",
                "details": search_content_results
            }
            
            # ==================== 步骤 4: 异步生成XML ====================
            print("\n" + "▶" * 40)
            print("步骤 4/6: 异步生成所有幻灯片的XML")
            print("▶" * 40)
            
            xml_list = await self._generate_xml_for_all_slides(
                design_data,
                search_content_results
            )
            
            print(f"\n✓ 生成 {len(xml_list)} 张幻灯片的XML")
            
            result["steps"]["xml_generation"] = {
                "slides_count": len(xml_list),
                "status": "completed"
            }
            
            # ==================== 步骤 5: 打包成PPTX ====================
            print("\n" + "▶" * 40)
            print("步骤 5/5: 将XML文件打包成PPTX")
            print("▶" * 40)
            
            # 获取所有已生成的XML幻灯片文件（按顺序）
            slide_xml_files = sorted(self.xml_slides_dir.glob("slide_*.xml"))
            
            # 使用打包工具生成PPTX
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pptx_filename = f"ppt_{design_data['title']}_{timestamp}.pptx"
            pptx_path = self.pptx_dir / pptx_filename
            
            self.packager.package_pptx(
                slide_xml_files=slide_xml_files,
                output_path=pptx_path,
                title=design_data["title"]
            )
            
            print(f"✓ PPTX已生成: {pptx_path.name}")
            
            result["steps"]["pptx_generation"] = {
                "file": str(pptx_path),
                "status": "completed"
            }
            
            # ==================== 完成 ====================
            result["end_time"] = datetime.now().isoformat()
            result["status"] = "success"
            result["final_output"] = str(pptx_path)
            
            print("\n" + "=" * 80)
            print("✓ PPT生成工作流完成！")
            print("=" * 80)
            print(f"\n最终输出: {pptx_path}")
            print(f"\n所有生成的文件:")
            print(f"  1. 大纲: {outline_file}")
            print(f"  2. 设计: {design_file}")
            print(f"  3. XML幻灯片: {len(slide_xml_files)} 个文件")
            print(f"  4. 最终PPTX: {pptx_path}")
            print()
            
            return result
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.now().isoformat()
            
            import traceback
            traceback.print_exc()
            
            return result
    
    async def _process_sections_concurrently(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        并发处理所有章节：搜索 + 内容生成
        
        Args:
            sections: 章节列表（来自design JSON）
        
        Returns:
            每个章节的搜索和内容结果
        """
        
        print(f"\n开始处理 {len(sections)} 个章节...")
        
        # 创建所有章节的任务
        tasks = []
        for section in sections:
            task = self._process_single_section(section)
            tasks.append(task)
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤掉异常
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"章节 {i+1} 处理失败: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def _process_single_section(
        self,
        section: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理单个章节：搜索 + 内容生成
        
        Args:
            section: 章节信息
        
        Returns:
            章节的搜索和内容结果
        """
        
        section_title = section.get("section_title", "")
        section_number = section.get("section_number", 0)
        slides = section.get("slides", [])
        
        print(f"\n处理章节 {section_number}: {section_title}")
        
        # 1. 搜索相关资料
        search_input = {"keywords": section_title}
        search_result = self.search_agent.execute(search_input)
        
        print(f"  ✓ 搜索完成，找到 {search_result.get('total_results', 0)} 条结果")
        
        # 2. 为每张幻灯片生成内容
        content_results = []
        for slide in slides:
            slide_title = slide.get("slide_title", "")
            content_type = slide.get("content_type", "")
            
            # 跳过特殊页面（标题页、章节页、结束页）
            if content_type in ["title_page", "section_intro"]:
                print(f"  • 跳过 {content_type}: {slide_title}")
                continue
            
            # 生成内容
            content_result = self.content_agent.execute({
                "section_title": slide_title,
                "section_content": "\n".join(slide.get("key_points", [])),
                "section_weight": section.get("section_weight", 5),
                "search_results": search_result
            })
            
            content_results.append({
                "slide_number": slide.get("slide_number", 0),
                "slide_title": slide_title,
                "content_file": content_result.get("saved_path", "")
            })
            
            print(f"  ✓ 内容生成: {slide_title}")
        
        return {
            "section_number": section_number,
            "section_title": section_title,
            "search_result": search_result,
            "content_results": content_results
        }
    
    async def _generate_xml_for_all_slides(
        self,
        design_data: Dict[str, Any],
        search_content_results: List[Dict[str, Any]]
    ) -> List[str]:
        """
        异步生成所有幻灯片的XML
        
        Args:
            design_data: design JSON数据
            search_content_results: 搜索和内容生成结果
        
        Returns:
            所有幻灯片的XML列表（按slide_number排序）
        """
        
        sections = design_data.get("sections", [])
        
        # 创建章节号到内容结果的映射
        section_content_map = {}
        for result in search_content_results:
            section_num = result.get("section_number", 0)
            section_content_map[section_num] = result
        
        all_xml_tasks = []
        
        # 为每张幻灯片创建XML生成任务
        for section in sections:
            section_num = section.get("section_number", 0)
            section_title = section.get("section_title", "")
            slides = section.get("slides", [])
            
            # 获取该章节的内容结果
            section_result = section_content_map.get(section_num, {})
            content_results = section_result.get("content_results", [])
            
            # 创建slide_number到content的映射
            content_map = {}
            for cr in content_results:
                slide_num = cr.get("slide_number", 0)
                content_file = cr.get("content_file", "")
                if content_file and Path(content_file).exists():
                    with open(content_file, 'r', encoding='utf-8') as f:
                        content_map[slide_num] = f.read()
            
            # 为每张幻灯片创建任务
            for slide in slides:
                slide_number = slide.get("slide_number", 0)
                content_text = content_map.get(slide_number, None)
                
                task = self._generate_single_slide_xml_async(
                    slide_info=slide,
                    content_text=content_text,
                    section_title=section_title
                )
                
                all_xml_tasks.append((slide_number, task))
        
        # 并发执行所有XML生成任务
        print(f"\n并发生成 {len(all_xml_tasks)} 张幻灯片的XML...")
        
        xml_results = await asyncio.gather(*[task for _, task in all_xml_tasks])
        
        # 按slide_number排序
        sorted_results = sorted(
            zip([sn for sn, _ in all_xml_tasks], xml_results),
            key=lambda x: x[0]
        )
        
        return [xml for _, xml in sorted_results]
    
    async def _generate_single_slide_xml_async(
        self,
        slide_info: Dict[str, Any],
        content_text: Optional[str],
        section_title: str
    ) -> str:
        """异步生成单张幻灯片的XML"""
        # xml_agent.execute是同步方法，但可以在async函数中调用
        return self.xml_agent.execute(
            slide_info=slide_info,
            content_text=content_text,
            section_title=section_title
        )
    
    def get_latest_design_file(self) -> Optional[Path]:
        """获取最新的design文件"""
        design_files = list(self.design_dir.glob("design_*.json"))
        if not design_files:
            return None
        return max(design_files, key=lambda p: p.stat().st_mtime)


async def main():
    """测试完整工作流"""
    
    # 创建工作流管理器
    workflow = PPTWorkflowManager()
    
    # 测试提示
    test_prompt = "创建一个关于王者荣耀游戏介绍的PPT演示文稿，面向游戏玩家，包含游戏背景、英雄系统、对战模式、电竞赛事等内容"
    
    # 执行工作流
    result = await workflow.generate_ppt_from_prompt(test_prompt)
    
    # 保存工作流结果
    result_file = workflow.outputs_dir / f"workflow_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n工作流结果已保存: {result_file}")


if __name__ == "__main__":
    asyncio.run(main())
