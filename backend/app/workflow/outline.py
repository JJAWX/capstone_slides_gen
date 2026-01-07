#!/usr/bin/env python3
"""
Outline Generation Script
Input: user prompt string
Output: markdown file saved to outputs/outlines/
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from agents.outline_agent import OutlineAgent

async def generate_outline(user_prompt: str):
    """
    Generate PPT outline from user prompt and save to markdown file.

    Args:
        user_prompt: User's description of the PPT topic and requirements

    Returns:
        Path to the generated markdown file
    """
    try:
        # Initialize the agent
        agent = OutlineAgent()

        # Generate outline
        result = await agent.execute(user_prompt=user_prompt)

        if result["status"] == "success":
            file_path = result["file_path"]
            print(f"✅ 大纲生成成功!")
            print(f"📄 文件保存路径: {file_path}")
            print(f"📊 章节数量: {len(result['structured_outline'].get('sections', []))}")
            return file_path
        else:
            print(f"❌ 生成失败: {result.get('error', '未知错误')}")
            return None

    except Exception as e:
        print(f"❌ 运行出错: {str(e)}")
        return None

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("❌ 请提供用户提示参数")
        print("用法: python outline.py \"你的PPT主题描述\"")
        print("示例: python outline.py \"创建一个关于AI在医疗领域的PPT演示文稿\"")
        sys.exit(1)

    user_prompt = sys.argv[1]

    print("🤖 PPT大纲生成器")
    print("=" * 40)
    print(f"📝 输入提示: {user_prompt}")
    print()

    # Run async function
    file_path = asyncio.run(generate_outline(user_prompt))

    if file_path:
        print(f"\n✅ 完成! 大纲已保存到: {file_path}")
    else:
        print("\n❌ 生成失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()