"""
完整工作流测试 - 简化版

只生成少量幻灯片以快速验证
"""
import sys
import os
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
os.chdir(backend_dir)

import asyncio
from app.workflow.complete_ppt_workflow import PPTWorkflowManager


async def quick_test():
    """快速测试完整工作流"""
    
    workflow = PPTWorkflowManager()
    
    # 简单的测试提示
    test_prompt = "创建一个关于Python编程基础的PPT，包含3个章节：变量和数据类型、控制流程、函数"
    
    print("开始快速测试工作流...\n")
    
    result = await workflow.generate_ppt_from_prompt(test_prompt)
    
    if result.get("status") == "success":
        print("\n✅ 工作流测试成功！")
        print(f"最终PPTX: {result.get('final_output')}")
    else:
        print("\n❌ 工作流测试失败")
        print(f"错误: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(quick_test())
