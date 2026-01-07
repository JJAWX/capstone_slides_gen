import os
import json
import time
from typing import Dict, Any, List
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class SearchAgent:
    """
    搜索代理 - 使用OpenAI的Web Search功能进行网络搜索

    功能：
    - 使用OpenAI官方Web Search API进行联网搜索
    - 获取实时的、带引用的搜索结果
    - 返回结构化的JSON格式结果
    """

    def __init__(self):
        """初始化搜索代理"""
        # 从环境变量获取API密钥
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("未找到OPENAI_API_KEY环境变量")
        
        self.client = OpenAI(api_key=api_key)

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行搜索任务

        Args:
            input_data: 包含 'keywords' 键的字典

        Returns:
            包含搜索结果的JSON格式字典
        """
        try:
            keywords = input_data['keywords'].strip()
            max_results = input_data.get('max_results', 10)

            print(f"开始使用OpenAI Web Search搜索: {keywords}")

            # 使用OpenAI的Responses API进行web search
            response = self.client.responses.create(
                model="gpt-4o-mini",  # 使用支持web search的模型
                tools=[
                    {"type": "web_search"}
                ],
                tool_choice="auto",
                input=f"请搜索关于'{keywords}'的相关信息，并提供详细的搜索结果。"
            )

            # 提取搜索结果
            search_results = self._extract_results(response, keywords)

            # 整理结果
            result = {
                'keywords': keywords,
                'total_results': len(search_results),
                'results': search_results,
                'timestamp': time.time(),
                'search_method': 'openai_web_search'
            }

            # 保存结果到文件
            saved_path = self.save_results(result)
            result['saved_path'] = saved_path

            return result

        except Exception as e:
            print(f"搜索失败: {e}")
            return {
                'error': f'搜索失败: {str(e)}',
                'keywords': input_data.get('keywords', ''),
                'results': [],
                'timestamp': time.time()
            }

    def _extract_results(self, response, keywords: str) -> List[Dict[str, Any]]:
        """
        从OpenAI的response中提取搜索结果

        Args:
            response: OpenAI API的响应对象
            keywords: 搜索关键词

        Returns:
            搜索结果列表
        """
        results = []
        output_text = ""
        
        try:
            # 获取响应文本
            output_text = response.output_text if hasattr(response, 'output_text') else ""
            
            # 提取引用的URL
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    # 查找message类型的输出
                    if hasattr(item, 'type') and item.type == 'message':
                        if hasattr(item, 'content') and item.content:
                            for content in item.content:
                                # 提取annotations中的URL引用
                                if hasattr(content, 'annotations') and content.annotations:
                                    for annotation in content.annotations:
                                        if hasattr(annotation, 'type') and annotation.type == 'url_citation':
                                            url = getattr(annotation, 'url', '')
                                            title = getattr(annotation, 'title', '')
                                            
                                            # 提取相关文本片段作为摘要
                                            start_index = getattr(annotation, 'start_index', 0)
                                            end_index = getattr(annotation, 'end_index', 0)
                                            snippet = ""
                                            if hasattr(content, 'text') and content.text:
                                                text = content.text
                                                # 提取引用前后的文本作为摘要
                                                snippet = text[max(0, start_index-50):min(len(text), end_index+50)].strip()
                                            
                                            if url:
                                                # 避免重复
                                                if not any(r['url'] == url for r in results):
                                                    results.append({
                                                        'rank': len(results) + 1,
                                                        'title': title or url,
                                                        'url': url,
                                                        'snippet': snippet[:200] if snippet else "",
                                                        'domain': self._extract_domain(url)
                                                    })
            
            # 如果没有提取到引用但有文本，创建一个汇总结果
            if not results and output_text:
                results.append({
                    'rank': 1,
                    'title': f'关于"{keywords}"的搜索摘要',
                    'url': '',
                    'snippet': output_text[:500] + '...' if len(output_text) > 500 else output_text,
                    'domain': 'openai_web_search'
                })

        except Exception as e:
            print(f"提取结果时出错: {e}")
            import traceback
            traceback.print_exc()
        
        return results

    def _extract_domain(self, url: str) -> str:
        """
        从URL中提取域名

        Args:
            url: 完整的URL

        Returns:
            域名
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""

    def save_results(self, result: Dict[str, Any], filename: str = None) -> str:
        """
        保存搜索结果到JSON文件

        Args:
            result: 搜索结果字典
            filename: 文件名，如果不提供则自动生成

        Returns:
            保存的文件路径
        """
        # 创建输出目录
        output_dir = Path('outputs/search_results')
        output_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        if filename is None:
            keywords = result.get('keywords', 'unknown').replace(' ', '_').replace('/', '_')
            timestamp = int(result.get('timestamp', 0))
            filename = f"{keywords}_{timestamp}.json"

        # 保存文件
        file_path = output_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return str(file_path)


# 测试函数
if __name__ == "__main__":
    agent = SearchAgent()

    # 测试搜索
    test_input = {'keywords': 'Python编程最新发展'}
    result = agent.execute(test_input)

    print(json.dumps(result, ensure_ascii=False, indent=2))
