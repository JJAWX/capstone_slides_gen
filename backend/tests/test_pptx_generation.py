"""
快速测试：从已有的design JSON生成PPTX
"""
import sys
import os
from pathlib import Path

# 添加backend到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
os.chdir(backend_dir)

from app.workflow.complete_ppt_workflow import PPTWorkflowManager
import json


def test_pptx_generation():
    """测试PPTX生成"""
    
    workflow = PPTWorkflowManager()
    
    # 直接指定最新的design文件
    design_file = Path("/Users/gigg1ty/Documents/GitHub/capstone_slides_gen/backend/outputs/design/design_机器学习基础_20260107_203639.json")
    
    if not design_file.exists():
        print(f"未找到design文件: {design_file}！")
        return
    
    print(f"使用design文件: {design_file}")
    
    # 加载design数据
    with open(design_file, 'r', encoding='utf-8') as f:
        design_data = json.load(f)
    
    # 调用PPTX生成函数
    xml_path = Path("dummy.xml")  # 占位符
    pptx_path = workflow._generate_pptx_from_xml(xml_path, design_data)
    
    print(f"\n✓ 测试完成!")
    print(f"生成的PPTX: {pptx_path}")
    
    # 验证文件存在
    if pptx_path.exists():
        print(f"✓ 文件已成功创建")
        print(f"  大小: {pptx_path.stat().st_size / 1024:.1f} KB")
    else:
        print(f"✗ 文件创建失败")


if __name__ == "__main__":
    test_pptx_generation()
