"""
测试完整的XML生成工作流

从design JSON -> 生成所有幻灯片XML -> 合并成完整结构
"""

import sys
from pathlib import Path

# 添加backend到Python路径
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
from app.workflow.workflow_manager import WorkflowManager


async def main():
    """测试XML生成工作流"""
    
    print("=" * 70)
    print("测试 XML 生成工作流")
    print("=" * 70)
    
    # 创建workflow manager
    workflow = WorkflowManager()
    
    # 执行完整的XML生成工作流
    try:
        merged_xml_path = await workflow.execute_xml_generation_workflow()
        
        print("\n" + "=" * 70)
        print("测试完成！")
        print("=" * 70)
        print(f"\n生成的文件:")
        print(f"  • 合并的presentation.xml: {merged_xml_path}")
        print(f"  • 各幻灯片XML: {workflow.xml_slides_dir}")
        
        # 读取并显示presentation.xml的前几行
        with open(merged_xml_path, 'r', encoding='utf-8') as f:
            preview = f.read(500)
        
        print(f"\nPresentation.xml 预览:")
        print("-" * 70)
        print(preview)
        print("...")
        print("-" * 70)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
