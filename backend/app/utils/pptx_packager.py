"""
PPTX打包工具 - 将XML文件打包成标准PPTX文件

PPTX文件本质上是一个ZIP压缩包，包含：
- [Content_Types].xml
- _rels/.rels  
- ppt/presentation.xml
- ppt/slides/slide1.xml, slide2.xml, ...
- ppt/slides/_rels/*.xml.rels
- ppt/slideLayouts/
- ppt/slideMasters/
- ppt/theme/
"""

import os
import zipfile
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class PPTXPackager:
    """将XML文件打包成标准PPTX文件"""
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent.parent / "templates"
    
    def package_pptx(
        self,
        slide_xml_files: List[Path],
        output_path: Path,
        title: str = "Presentation"
    ) -> Path:
        """
        将幻灯片XML文件打包成PPTX
        
        Args:
            slide_xml_files: 幻灯片XML文件列表（按顺序）
            output_path: 输出PPTX文件路径
            title: 演示文稿标题
        
        Returns:
            生成的PPTX文件路径
        """
        
        print(f"\n开始打包PPTX...")
        print(f"  - 幻灯片数量: {len(slide_xml_files)}")
        print(f"  - 输出路径: {output_path}")
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as pptx_zip:
            # 1. [Content_Types].xml
            self._add_content_types(pptx_zip, len(slide_xml_files))
            
            # 2. _rels/.rels
            self._add_root_rels(pptx_zip)
            
            # 3. ppt/presentation.xml
            self._add_presentation_xml(pptx_zip, len(slide_xml_files), title)
            
            # 4. ppt/_rels/presentation.xml.rels
            self._add_presentation_rels(pptx_zip, len(slide_xml_files))
            
            # 5. 添加每个幻灯片
            for idx, slide_file in enumerate(slide_xml_files, 1):
                self._add_slide(pptx_zip, slide_file, idx)
            
            # 6. 添加基础模板文件（slideMasters, slideLayouts, theme）
            self._add_base_templates(pptx_zip)
        
        print(f"✓ PPTX打包完成!")
        print(f"  - 文件大小: {output_path.stat().st_size / 1024:.1f} KB")
        
        return output_path
    
    def _add_content_types(self, zip_file: zipfile.ZipFile, slide_count: int):
        """添加[Content_Types].xml"""
        
        # 基础内容类型
        content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
'''
        
        # 为每个幻灯片添加类型
        for i in range(1, slide_count + 1):
            content += f'  <Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>\n'
        
        content += '</Types>'
        
        zip_file.writestr('[Content_Types].xml', content)
    
    def _add_root_rels(self, zip_file: zipfile.ZipFile):
        """添加_rels/.rels"""
        
        content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>'''
        
        zip_file.writestr('_rels/.rels', content)
    
    def _add_presentation_xml(self, zip_file: zipfile.ZipFile, slide_count: int, title: str):
        """添加ppt/presentation.xml"""
        
        content = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                saveSubsetFonts="1">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
'''
        
        # 为每张幻灯片添加引用
        for i in range(1, slide_count + 1):
            content += f'    <p:sldId id="{255 + i}" r:id="rId{i + 1}"/>\n'
        
        content += '''  </p:sldIdLst>
  <p:sldSz cx="9144000" cy="5143500" type="screen4x3"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle>
    <a:defPPr>
      <a:defRPr lang="zh-CN"/>
    </a:defPPr>
  </p:defaultTextStyle>
</p:presentation>'''
        
        zip_file.writestr('ppt/presentation.xml', content)
    
    def _add_presentation_rels(self, zip_file: zipfile.ZipFile, slide_count: int):
        """添加ppt/_rels/presentation.xml.rels"""
        
        content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
'''
        
        # 为每张幻灯片添加关系
        for i in range(1, slide_count + 1):
            content += f'  <Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>\n'
        
        content += '</Relationships>'
        
        zip_file.writestr('ppt/_rels/presentation.xml.rels', content)
    
    def _add_slide(self, zip_file: zipfile.ZipFile, slide_file: Path, slide_number: int):
        """添加单个幻灯片"""
        
        # 读取生成的XML内容
        with open(slide_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # 需要将sldLayout转换为slide格式
        # 简单的方式：替换标签名称
        slide_xml = xml_content.replace('<p:sldLayout', '<p:sld')
        slide_xml = slide_xml.replace('</p:sldLayout>', '</p:sld>')
        
        # 写入ZIP
        zip_file.writestr(f'ppt/slides/slide{slide_number}.xml', slide_xml)
        
        # 添加幻灯片关系文件
        rels_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>'''
        
        zip_file.writestr(f'ppt/slides/_rels/slide{slide_number}.xml.rels', rels_content)
    
    def _add_base_templates(self, zip_file: zipfile.ZipFile):
        """添加基础模板文件"""
        
        # slideMaster1.xml - 简化版
        slide_master = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rId1"/>
  </p:sldLayoutIdLst>
</p:sldMaster>'''
        
        zip_file.writestr('ppt/slideMasters/slideMaster1.xml', slide_master)
        
        # slideLayout1.xml - 简化版
        slide_layout = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             type="blank" preserve="1">
  <p:cSld name="Blank">
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
</p:sldLayout>'''
        
        zip_file.writestr('ppt/slideLayouts/slideLayout1.xml', slide_layout)
        
        # theme1.xml - 简化版
        theme = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="1F497D"/></a:dk2>
      <a:lt2><a:srgbClr val="EEECE1"/></a:lt2>
      <a:accent1><a:srgbClr val="4F81BD"/></a:accent1>
      <a:accent2><a:srgbClr val="C0504D"/></a:accent2>
      <a:accent3><a:srgbClr val="9BBB59"/></a:accent3>
      <a:accent4><a:srgbClr val="8064A2"/></a:accent4>
      <a:accent5><a:srgbClr val="4BACC6"/></a:accent5>
      <a:accent6><a:srgbClr val="F79646"/></a:accent6>
      <a:hlink><a:srgbClr val="0000FF"/></a:hlink>
      <a:folHlink><a:srgbClr val="800080"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Office">
      <a:majorFont>
        <a:latin typeface="Calibri"/>
        <a:ea typeface=""/>
        <a:cs typeface=""/>
      </a:majorFont>
      <a:minorFont>
        <a:latin typeface="Calibri"/>
        <a:ea typeface=""/>
        <a:cs typeface=""/>
      </a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:fillStyleLst>
      <a:lnStyleLst>
        <a:ln w="9525" cap="flat" cmpd="sng" algn="ctr">
          <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        </a:ln>
      </a:lnStyleLst>
      <a:effectStyleLst>
        <a:effectStyle><a:effectLst/></a:effectStyle>
      </a:effectStyleLst>
      <a:bgFillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>'''
        
        zip_file.writestr('ppt/theme/theme1.xml', theme)
        
        # 关系文件
        master_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>'''
        
        zip_file.writestr('ppt/slideMasters/_rels/slideMaster1.xml.rels', master_rels)
        
        layout_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>'''
        
        zip_file.writestr('ppt/slideLayouts/_rels/slideLayout1.xml.rels', layout_rels)


if __name__ == "__main__":
    """测试打包功能"""
    
    packager = PPTXPackager()
    
    # 查找最新生成的XML幻灯片
    xml_slides_dir = Path(__file__).parent.parent / "outputs" / "xml_slides"
    slide_files = sorted(xml_slides_dir.glob("slide_*.xml"))
    
    if not slide_files:
        print("未找到XML幻灯片文件!")
        exit(1)
    
    print(f"找到 {len(slide_files)} 个XML幻灯片")
    
    # 打包成PPTX
    output_dir = Path(__file__).parent.parent / "outputs"
    output_path = output_dir / f"test_packaged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
    
    packager.package_pptx(slide_files, output_path, "Test Presentation")
    
    print(f"\n测试完成! 文件: {output_path}")
