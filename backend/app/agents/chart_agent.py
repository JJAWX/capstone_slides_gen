import logging
import json
import os
import base64
from typing import List, Dict, Optional
from openai import AsyncOpenAI
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class ChartAgent:
    """
    Agent responsible for generating data visualization charts for slides.

    Capabilities:
    1. Analyze slide content to identify data suitable for visualization
    2. Generate appropriate chart types: bar, line, pie, area, scatter
    3. Use matplotlib to create professional charts
    4. Save charts as PNG images for embedding in slides

    Charts help audience understand data trends and comparisons quickly.
    """

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Create charts directory
        self.charts_dir = Path(__file__).resolve().parent.parent.parent / "output" / "charts"
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    async def suggest_charts_for_slides(
        self,
        slides: List[Dict],
        template: str,
        audience: str
    ) -> List[Dict]:
        """
        Analyze slides and generate appropriate charts for data-heavy slides.
        确保每个PPT至少有1个图表。

        Returns:
            List of slides with added chart information
        """
        logger.info(f"ChartAgent: Analyzing {len(slides)} slides for chart opportunities")

        charts_generated = 0
        best_candidate_idx = None
        best_candidate_score = 0

        for i, slide in enumerate(slides):
            # Skip title slides
            if slide.get("slideType") == "title":
                logger.info(f"Skipping title slide {i}: {slide.get('title')}")
                continue

            logger.info(f"Analyzing slide {i}: {slide.get('title')}")

            # Check if slide has data suitable for visualization
            chart_data = await self._extract_chart_data(slide, audience)

            if chart_data:
                logger.info(f"Found chart data for slide {i}: {chart_data.get('chart_type')}")
                # Generate chart image
                chart_path = await self._generate_chart(
                    chart_data,
                    slide.get("title", f"Slide {i+1}"),
                    template,
                    slide_index=i
                )

                if chart_path:
                    slide["chart_url"] = chart_path
                    slide["chart_type"] = chart_data.get("chart_type")
                    charts_generated += 1
                    logger.info(f"Generated {chart_data.get('chart_type')} chart for slide: {slide.get('title')}")
                else:
                    logger.warning(f"Failed to generate chart for slide {i}")
            else:
                logger.info(f"No chart data found for slide {i}: {slide.get('title')}")
                # 记录最佳候选幻灯片（用于保底生成图表）
                title = slide.get("title", "").lower()
                content = slide.get("content", [])
                score = 0
                # 根据标题和内容评估适合生成图表的程度
                chart_keywords = ["data", "statistics", "market", "growth", "trend", "comparison", 
                                  "analysis", "result", "performance", "overview", "summary",
                                  "数据", "统计", "市场", "增长", "趋势", "对比", "分析", "结果", "表现"]
                for kw in chart_keywords:
                    if kw in title:
                        score += 2
                    for c in content:
                        if kw in c.lower():
                            score += 1
                if score > best_candidate_score:
                    best_candidate_score = score
                    best_candidate_idx = i

        # 如果没有生成任何图表，强制为最佳候选生成一个
        if charts_generated == 0 and best_candidate_idx is not None:
            logger.info(f"No charts generated, forcing chart for slide {best_candidate_idx}")
            slide = slides[best_candidate_idx]
            forced_chart = await self._generate_forced_chart(slide, template, best_candidate_idx)
            if forced_chart:
                slide["chart_url"] = forced_chart
                slide["chart_type"] = "bar"
                charts_generated += 1
                logger.info(f"Forced chart generated for slide {best_candidate_idx}")
        
        # 如果还是没有图表，为第2-3张幻灯片生成一个
        if charts_generated == 0 and len(slides) > 2:
            target_idx = 2  # 第三张幻灯片
            slide = slides[target_idx]
            if slide.get("slideType") != "title":
                logger.info(f"Forcing fallback chart for slide {target_idx}")
                forced_chart = await self._generate_forced_chart(slide, template, target_idx)
                if forced_chart:
                    slide["chart_url"] = forced_chart
                    slide["chart_type"] = "bar"
                    logger.info(f"Fallback chart generated for slide {target_idx}")

        logger.info(f"ChartAgent: Generated {charts_generated} charts total")
        return slides
    
    async def _generate_forced_chart(self, slide: Dict, template: str, slide_index: int) -> Optional[str]:
        """为幻灯片强制生成一个图表"""
        title = slide.get("title", "Data Overview")
        content = slide.get("content", [])
        
        # 根据标题生成相关数据
        sample_data = {
            "has_data": True,
            "chart_type": "bar",
            "title": title,
            "data": {
                "labels": ["Category A", "Category B", "Category C", "Category D"],
                "values": [65, 78, 52, 89]
            }
        }
        
        # 如果有content，用content作为标签
        if content and len(content) >= 2:
            labels = [c[:20] for c in content[:4]]  # 最多4个，每个最多20字符
            values = [45 + i * 15 for i in range(len(labels))]  # 生成递增数据
            sample_data["data"]["labels"] = labels
            sample_data["data"]["values"] = values
        
        return await self._generate_chart(sample_data, title, template, slide_index)

    async def _extract_chart_data(
        self,
        slide: Dict,
        audience: str
    ) -> Optional[Dict]:
        """
        Analyze slide content and extract data suitable for chart visualization.
        """
        title = slide.get("title", "")
        content = slide.get("content", [])
        paragraph = slide.get("paragraph", "")
        table = slide.get("table")

        # If there's already a table, we can visualize it
        if table:
            return await self._table_to_chart_data(table, title)

        # Build context for LLM
        slide_text = f"Title: {title}\n"
        if content:
            slide_text += "Points:\n" + "\n".join(f"- {point}" for point in content)
        if paragraph:
            slide_text += f"\nDetails: {paragraph}"

        system_prompt = f"""You are an expert at identifying data visualization opportunities in slide content.

Analyze the slide content and determine if it would benefit from a chart visualization.

**IMPORTANT:** If the slide topic suggests data visualization (like "market share", "trends", "comparison", "statistics")
but doesn't contain actual numbers, you should GENERATE realistic sample data to illustrate the concept.

Return JSON in this format:
{{
    "has_data": true/false,
    "chart_type": "bar" | "line" | "pie" | "area" | "scatter",
    "title": "Chart title",
    "data": {{
        "labels": ["Label 1", "Label 2", ...],
        "values": [10, 20, ...],
        "series": [{{"name": "Series 1", "values": [...]}}]  // For multi-series charts
    }},
    "reasoning": "Why this chart type is appropriate"
}}

Chart type guidelines:
- **bar**: Comparing categories, rankings, discrete comparisons
- **line**: Trends over time, continuous progression
- **pie**: Part-to-whole relationships, percentages, market share
- **area**: Cumulative totals over time
- **scatter**: Correlation between two variables

**When to generate sample data:**
- Slide mentions "market share", "占比", "percentage" → Generate pie chart with sample percentages
- Slide mentions "trends", "growth", "趋势" → Generate line chart with time series
- Slide mentions "comparison", "对比" → Generate bar chart with comparative values
- Slide mentions "statistics", "数据" → Generate appropriate chart with sample numbers

Consider the {audience} audience when deciding complexity.

If the topic has NO relation to data or visualization, return: {{"has_data": false}}
"""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": slide_text}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            logger.info(f"LLM analysis result: has_data={result.get('has_data')}, chart_type={result.get('chart_type')}")

            if result.get("has_data"):
                logger.info(f"Found chart data: {result.get('chart_type')} - {result.get('reasoning')}")
                logger.info(f"Data: {result.get('data')}")
                return result
            else:
                logger.info(f"No data visualization needed for this slide")
                return None

        except Exception as e:
            logger.error(f"Error extracting chart data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def _table_to_chart_data(self, table: Dict, title: str) -> Optional[Dict]:
        """
        Convert table data to chart data format.
        """
        headers = table.get("headers", [])
        rows = table.get("rows", [])

        if not headers or not rows:
            return None

        # Simple heuristic: first column as labels, remaining columns as data series
        labels = [row[0] for row in rows if row]

        # Check if we have numeric data
        try:
            if len(headers) == 2:
                # Single series
                values = [float(row[1]) for row in rows if len(row) > 1]
                return {
                    "has_data": True,
                    "chart_type": "bar",
                    "title": title,
                    "data": {
                        "labels": labels,
                        "values": values
                    }
                }
            else:
                # Multiple series
                series = []
                for col_idx in range(1, len(headers)):
                    series.append({
                        "name": headers[col_idx],
                        "values": [float(row[col_idx]) for row in rows if len(row) > col_idx]
                    })
                return {
                    "has_data": True,
                    "chart_type": "bar",
                    "title": title,
                    "data": {
                        "labels": labels,
                        "series": series
                    }
                }
        except (ValueError, IndexError):
            # Not numeric data
            return None

    async def _generate_chart(
        self,
        chart_data: Dict,
        slide_title: str,
        template: str,
        slide_index: int
    ) -> Optional[str]:
        """
        Generate chart image using matplotlib.
        """
        chart_type = chart_data.get("chart_type", "bar")
        data = chart_data.get("data", {})
        chart_title = chart_data.get("title", slide_title)

        # Get template colors
        colors = self._get_template_colors(template)

        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            # Set style (try modern seaborn style, fallback to default)
            try:
                plt.style.use('seaborn-v0_8-darkgrid')
            except:
                try:
                    plt.style.use('seaborn-darkgrid')
                except:
                    pass  # Use default style

            if chart_type == "bar":
                self._create_bar_chart(ax, data, chart_title, colors)
            elif chart_type == "line":
                self._create_line_chart(ax, data, chart_title, colors)
            elif chart_type == "pie":
                self._create_pie_chart(ax, data, chart_title, colors)
            elif chart_type == "area":
                self._create_area_chart(ax, data, chart_title, colors)
            elif chart_type == "scatter":
                self._create_scatter_chart(ax, data, chart_title, colors)
            else:
                # Default to bar
                self._create_bar_chart(ax, data, chart_title, colors)

            # Save chart
            chart_filename = f"chart_slide_{slide_index}_{chart_type}.png"
            chart_path = self.charts_dir / chart_filename
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)

            logger.info(f"Chart saved: {chart_path}")
            return str(chart_path)

        except Exception as e:
            logger.error(f"Failed to generate chart: {e}")
            plt.close('all')  # Clean up
            return None

    def _create_bar_chart(self, ax, data: Dict, title: str, colors: Dict):
        """Create bar chart."""
        labels = data.get("labels", [])

        if "series" in data:
            # Multiple series (grouped bar chart)
            series = data["series"]
            x = np.arange(len(labels))
            width = 0.8 / len(series)

            for i, s in enumerate(series):
                offset = width * i - (width * len(series) / 2 - width / 2)
                ax.bar(x + offset, s["values"], width, label=s["name"],
                       color=colors["series"][i % len(colors["series"])])

            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.legend()
        else:
            # Single series
            values = data.get("values", [])
            ax.bar(labels, values, color=colors["primary"])
            plt.xticks(rotation=45, ha='right')

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

    def _create_line_chart(self, ax, data: Dict, title: str, colors: Dict):
        """Create line chart."""
        labels = data.get("labels", [])

        if "series" in data:
            # Multiple series
            for i, s in enumerate(data["series"]):
                ax.plot(labels, s["values"], marker='o', label=s["name"],
                       color=colors["series"][i % len(colors["series"])], linewidth=2)
            ax.legend()
        else:
            # Single series
            values = data.get("values", [])
            ax.plot(labels, values, marker='o', color=colors["primary"], linewidth=2)

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')

    def _create_pie_chart(self, ax, data: Dict, title: str, colors: Dict):
        """Create pie chart."""
        labels = data.get("labels", [])
        values = data.get("values", [])

        # Use series colors
        pie_colors = colors["series"][:len(values)]

        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90,
               colors=pie_colors)
        ax.set_title(title, fontsize=14, fontweight='bold')

    def _create_area_chart(self, ax, data: Dict, title: str, colors: Dict):
        """Create area chart."""
        labels = data.get("labels", [])

        if "series" in data:
            # Stacked area chart
            values_matrix = [s["values"] for s in data["series"]]
            ax.stackplot(range(len(labels)), *values_matrix,
                        labels=[s["name"] for s in data["series"]],
                        colors=colors["series"][:len(data["series"])],
                        alpha=0.7)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.legend(loc='upper left')
        else:
            # Single area
            values = data.get("values", [])
            ax.fill_between(range(len(labels)), values, alpha=0.7, color=colors["primary"])
            ax.plot(range(len(labels)), values, color=colors["primary"], linewidth=2)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha='right')

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

    def _create_scatter_chart(self, ax, data: Dict, title: str, colors: Dict):
        """Create scatter chart."""
        # Assume data has x_values and y_values
        x_values = data.get("x_values", data.get("values", []))
        y_values = data.get("y_values", data.get("values", []))

        ax.scatter(x_values, y_values, color=colors["primary"], s=100, alpha=0.6)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

    def _get_template_colors(self, template: str) -> Dict:
        """Get color scheme for template."""
        color_schemes = {
            "corporate": {
                "primary": "#0066CC",
                "series": ["#0066CC", "#4CAF50", "#FF9800", "#E91E63", "#9C27B0"]
            },
            "academic": {
                "primary": "#333333",
                "series": ["#333333", "#666666", "#999999", "#2196F3", "#4CAF50"]
            },
            "startup": {
                "primary": "#9B59B6",
                "series": ["#9B59B6", "#3498DB", "#E74C3C", "#F39C12", "#1ABC9C"]
            },
            "minimal": {
                "primary": "#000000",
                "series": ["#000000", "#555555", "#888888", "#AAAAAA", "#CCCCCC"]
            },
            "creative": {
                "primary": "#FF6B6B",
                "series": ["#FF6B6B", "#4ECDC4", "#FFE66D", "#A8E6CF", "#FFB6B9"]
            },
            "nature": {
                "primary": "#27AE60",
                "series": ["#27AE60", "#2ECC71", "#16A085", "#1ABC9C", "#52BE80"]
            },
            "futuristic": {
                "primary": "#3498DB",
                "series": ["#3498DB", "#9B59B6", "#E74C3C", "#1ABC9C", "#F39C12"]
            },
            "luxury": {
                "primary": "#D4AF37",
                "series": ["#D4AF37", "#C0C0C0", "#CD7F32", "#000000", "#4A4A4A"]
            }
        }

        return color_schemes.get(template, color_schemes["corporate"])
