import re
from bs4 import BeautifulSoup
import os

class DocumentCleaner:
    """法律文档数据清洗器 - 提取完整文本内容"""
    
    def __init__(self):
        pass
    
    def clean_document_to_text(self, html_content):
        """
        清洗单个法律文档，提取完整的文本内容
        
        Args:
            html_content (str): HTML源代码
            
        Returns:
            str: 清洗后的完整文本内容
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 查找PDF_pox div，这里包含完整的文档内容
        pdf_box = soup.find('div', class_='PDF_pox')
        if not pdf_box:
            return "未找到文档内容"
        
        # 提取所有文本内容
        raw_text = pdf_box.get_text(separator='\n', strip=True)
        
        # 进行文本清洗
        cleaned_text = self._clean_text(raw_text)
        
        return cleaned_text
    
    def _clean_text(self, text):
        """
        清洗文本内容，去除多余的空白和格式化
        
        Args:
            text (str): 原始文本
            
        Returns:
            str: 清洗后的文本
        """
        # 去除多余的空白行
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # 去除行首行尾的空白
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # 重新组合文本
        cleaned_text = '\n'.join(lines)
        
        # 添加适当的分段
        cleaned_text = self._format_paragraphs(cleaned_text)
        
        return cleaned_text
    
    def _format_paragraphs(self, text):
        """
        格式化段落，使文本更易读
        
        Args:
            text (str): 原始文本
            
        Returns:
            str: 格式化后的文本
        """
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            # 如果是标题行（包含法院名称、文书类型等），前后加空行
            if any(keyword in line for keyword in ['人民法院', '裁定书', '判决书', '决定书']):
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')
                formatted_lines.append(line)
                formatted_lines.append('')
            
            # 如果是案件编号，前后加空行
            elif re.match(r'^\（\d{4}\）.*号$', line):
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')
                formatted_lines.append(line)
                formatted_lines.append('')
            
            # 如果是重要的开始段落，前面加空行
            elif any(line.startswith(keyword) for keyword in ['原告', '被告', '本院认为', '判决如下', '裁定如下']):
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')
                formatted_lines.append(line)
            
            # 如果是法官信息和日期，前面加空行
            elif any(keyword in line for keyword in ['审判员', '审判长', '书记员']) or re.search(r'[一二三四五六七八九十○〇]{4}年.*[一二三四五六七八九十○〇]月.*[一二三四五六七八九十○〇]日', line):
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')
                formatted_lines.append(line)
            
            # 普通内容行
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def save_to_txt(self, filename, text_content):
        """
        保存文本内容到txt文件
        
        Args:
            filename (str): 文件名
            text_content (str): 文本内容
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text_content)
        print(f"文档内容已保存到: {filename}")
    
    def extract_document_info(self, html_content):
        """
        提取文档基本信息用于命名文件
        
        Args:
            html_content (str): HTML源代码
            
        Returns:
            dict: 包含案件编号、案由等信息
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        info = {}
        
        # 尝试从PDF_pox中提取案件编号
        pdf_box = soup.find('div', class_='PDF_pox')
        if pdf_box:
            # 查找案件编号
            case_number_match = re.search(r'\（\d{4}\）.*?号', pdf_box.get_text())
            if case_number_match:
                info['case_number'] = case_number_match.group()
        
        # 从概要区域提取案由
        basic_info_section = soup.find('div', class_='gaiyao_center')
        if basic_info_section:
            case_reason = basic_info_section.find('h4', string=re.compile(r'案由：'))
            if case_reason:
                reason_a = case_reason.find('a')
                if reason_a:
                    info['case_reason'] = reason_a.text.strip()
        
        return info

def main():
    """主函数，用于测试数据清洗功能"""
    # 读取之前保存的HTML文件
    try:
        with open('single_document_source.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 创建清洗器实例
        cleaner = DocumentCleaner()
        
        # 提取文档信息
        doc_info = cleaner.extract_document_info(html_content)
        
        # 清洗文档内容
        print("正在清洗文档数据...")
        cleaned_text = cleaner.clean_document_to_text(html_content)
        
        # 生成文件名
        case_number = doc_info.get('case_number', '未知案件')
        case_reason = doc_info.get('case_reason', '未知案由')
        filename = f"{case_number}_{case_reason}.txt"
        
        # 清理文件名中的特殊字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # 保存到txt文件
        cleaner.save_to_txt(filename, cleaned_text)
        
        print(f"\n=== 文档信息 ===")
        print(f"案件编号: {case_number}")
        print(f"案由: {case_reason}")
        print(f"文件名: {filename}")
        
        print(f"\n=== 文档内容预览（前500字符）===")
        print(cleaned_text[:500] + '...')
        
        print(f"\n=== 文档统计 ===")
        print(f"总字符数: {len(cleaned_text)}")
        print(f"总行数: {len(cleaned_text.split(chr(10)))}")
        
    except FileNotFoundError:
        print("找不到single_document_source.html文件，请先运行文档抓取脚本")
    except Exception as e:
        print(f"处理过程中出现错误: {e}")

if __name__ == "__main__":
    main() 