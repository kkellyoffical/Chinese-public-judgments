#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
裁判文书网爬取项目 - 上海市近三年文书自动化收集
整合所有现有功能，实现完整的自动化收集和处理流程
"""

import sys
import os
import time
import datetime
import json
import re
from browser_simulator import WenshuBrowserSimulator
from document_cleaner import DocumentCleaner
import random

class ShanghaiDocumentCollector:
    """上海市裁判文书自动化收集器"""
    
    def __init__(self):
        self.simulator = WenshuBrowserSimulator()
        self.cleaner = DocumentCleaner()
        self.max_pages = 40
        self.collected_urls = set()  # 用于去重
        self.url_folder = "URL列表"
        self.doc_folder = "文书"
        self.init_folders()
    
    def init_folders(self):
        """初始化文件夹结构"""
        print("正在初始化文件夹结构...")
        
        # 创建URL列表文件夹
        if not os.path.exists(self.url_folder):
            os.makedirs(self.url_folder)
            print(f"✓ 创建文件夹: {self.url_folder}")
        
        # 创建文书文件夹
        if not os.path.exists(self.doc_folder):
            os.makedirs(self.doc_folder)
            print(f"✓ 创建文件夹: {self.doc_folder}")
    
    def generate_date_range(self, years_back=3):
        """生成近三年的日期列表"""
        print(f"正在生成近{years_back}年的日期列表...")
        
        dates = []
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=years_back * 365)
        
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += datetime.timedelta(days=1)
        
        print(f"✓ 生成了 {len(dates)} 个日期，从 {dates[0]} 到 {dates[-1]}")
        return dates
    
    def collect_urls_for_date(self, date_str, max_pages=40):
        """收集指定日期的URL"""
        try:
            # 执行高级检索
            if not self.simulator.perform_advanced_search(date_str):
                print(f"✗ {date_str} 高级检索失败")
                return []
            
            # 选择上海市
            if not self.simulator.select_region_shanghai():
                print(f"⚠ {date_str} 选择上海市失败，继续执行...")
            
            # 设置每页15条
            if not self.simulator.set_page_size_15():
                print(f"⚠ {date_str} 设置页面大小失败，继续执行...")
            
            # 收集所有页面的链接
            all_links = set()
            current_page = 1
            
            while current_page <= max_pages:
                # 极致安全：夜间暂停、长延时、复杂行为模拟、异常检测
                self.simulator.night_pause()
                self.simulator.extreme_random_sleep(20, 60)
                self.simulator.simulate_extreme_human_behavior()
                self.simulator.check_captcha_or_exception()

                print(f"\n--- 第 {current_page} 页 ---")
                
                # 提取当前页面的链接
                page_links = self.simulator.extract_document_links()
                
                if page_links:
                    # 去重处理
                    new_links = []
                    for link in page_links:
                        if link['url'] not in self.collected_urls:
                            new_links.append(link)
                            self.collected_urls.add(link['url'])
                    
                    all_links.update(new_links)
                    print(f"✓ 第 {current_page} 页收集到 {len(page_links)} 个链接，去重后新增 {len(new_links)} 个")
                else:
                    print(f"⚠ 第 {current_page} 页未收集到链接")
                
                # 尝试点击下一页
                if not self.simulator.click_next_page():
                    print("✗ 无法点击下一页，可能已到最后一页")
                    break
                
                current_page += 1
                
                # 每页后极致延时
                self.simulator.extreme_random_sleep(20, 60)
                self.simulator.simulate_extreme_human_behavior()
                
            print(f"✓ {date_str} 共收集到 {len(all_links)} 个新链接")
            return list(all_links)
            
        except Exception as e:
            print(f"✗ {date_str} 收集URL失败: {str(e)}")
            return []
    
    def is_date_processed(self, date_str):
        """检查日期是否已经处理过"""
        url_file = os.path.join(self.url_folder, f"{date_str}_上海市文书.txt")
        doc_folder = os.path.join(self.doc_folder, date_str)
        
        # 如果URL文件和文档文件夹都存在，认为已处理
        if os.path.exists(url_file) and os.path.exists(doc_folder):
            return True
        return False
    
    def save_urls_to_file(self, date_str, links):
        """保存URL到文件"""
        if not links:
            print(f"⚠ {date_str} 没有链接需要保存")
            return None
        
        try:
            filename = os.path.join(self.url_folder, f"{date_str}_上海市文书.txt")
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# 裁判文书网 - 上海市 - {date_str}\n")
                f.write(f"# 收集时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 总共收集到 {len(links)} 个文书链接\n\n")
                
                for i, link in enumerate(links):
                    f.write(f"{i+1}. {link['title']}\n")
                    f.write(f"   URL: {link['url']}\n\n")
            
            print(f"✓ 保存 {len(links)} 个链接到: {filename}")
            return filename
            
        except Exception as e:
            print(f"✗ 保存URL文件失败: {str(e)}")
            return None
    
    def download_and_clean_documents(self, url_list, date_str):
        """下载并清洗文档"""
        if not url_list:
            print(f"⚠ {date_str} 没有文档需要下载")
            return
        
        print(f"\n开始下载和清洗 {date_str} 的文档...")
        
        # 创建日期文件夹
        date_folder = os.path.join(self.doc_folder, date_str)
        if not os.path.exists(date_folder):
            os.makedirs(date_folder)
            print(f"✓ 创建日期文件夹: {date_folder}")
        
        success_count = 0
        fail_count = 0
        
        for idx, url in enumerate(url_list):
            # 极致安全：夜间暂停、长延时、复杂行为模拟、异常检测
            self.simulator.night_pause()
            self.simulator.extreme_random_sleep(30, 90)
            self.simulator.simulate_extreme_human_behavior()
            self.simulator.check_captcha_or_exception()
            # 偶尔跳过某一文书，模拟人类疏漏
            if random.random() < 0.02:
                print(f"[极致安全] 偶尔跳过第{idx+1}篇文书，模拟人类疏漏")
                continue

            try:
                print(f"\n处理文档 {idx+1}/{len(url_list)}: {url['title'][:50]}...")
                
                # 访问文档页面
                response = self.simulator.page.goto(
                    url['url'],
                    wait_until='networkidle',
                    timeout=30000
                )
                
                if response.status != 200:
                    print(f"✗ 页面响应状态异常: {response.status}")
                    fail_count += 1
                    continue
                
                # 等待页面加载
                self.simulator.page.wait_for_load_state('domcontentloaded')
                
                # 获取页面内容
                html_content = self.simulator.page.content()
                
                # 清洗文档内容
                cleaned_text = self.cleaner.clean_document_to_text(html_content)
                
                if cleaned_text == "未找到文档内容":
                    print(f"✗ 未找到文档内容")
                    fail_count += 1
                    continue
                
                # 提取文档信息用于命名
                doc_info = self.cleaner.extract_document_info(html_content)
                case_number = doc_info.get('case_number', '未知案件')
                case_reason = doc_info.get('case_reason', '未知案由')
                
                # 生成文件名（使用文档标题）
                safe_title = self.clean_filename(url['title'])
                filename = f"{safe_title}.txt"
                
                # 如果文件名太长，使用案件编号
                if len(filename) > 100:
                    filename = f"{case_number}_{case_reason}.txt"
                    filename = self.clean_filename(filename)
                
                # 保存文件
                file_path = os.path.join(date_folder, filename)
                
                # 检查文件是否已存在（避免重复）
                if os.path.exists(file_path):
                    print(f"⚠ 文件已存在，跳过: {filename}")
                    continue
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"# 文档标题: {url['title']}\n")
                    f.write(f"# 案件编号: {case_number}\n")
                    f.write(f"# 案由: {case_reason}\n")
                    f.write(f"# 收集时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# 原始URL: {url['url']}\n\n")
                    f.write(cleaned_text)
                
                print(f"✓ 保存文档: {filename}")
                success_count += 1
                
                # 每文书后极致延时
                self.simulator.extreme_random_sleep(30, 90)
                self.simulator.simulate_extreme_human_behavior()
                
            except Exception as e:
                print(f"✗ 处理文档失败: {str(e)}")
                fail_count += 1
                continue
        
        print(f"\n{date_str} 文档处理完成:")
        print(f"  ✓ 成功: {success_count}")
        print(f"  ✗ 失败: {fail_count}")
    
    def clean_filename(self, filename):
        """清理文件名中的特殊字符"""
        # 移除或替换特殊字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制文件名长度
        if len(filename) > 100:
            filename = filename[:100]
        return filename
    
    def process_date(self, date_str):
        """处理单个日期的完整流程"""
        try:
            # 步骤1：收集URL
            links = self.collect_urls_for_date(date_str)
            
            # 步骤2：保存URL到文件
            url_file = self.save_urls_to_file(date_str, links)
            
            # 步骤3：下载并清洗文档
            if links:
                self.download_and_clean_documents(links, date_str)
            
            return len(links)
            
        except Exception as e:
            print(f"✗ 处理日期 {date_str} 失败: {str(e)}")
            return 0
    
    def run_collection(self, years_back=3):
        """运行完整的收集流程"""
        print("=" * 80)
        print("上海市裁判文书自动化收集系统")
        print("=" * 80)
        
        # 生成日期列表
        print("\n第一步：生成日期列表...")
        dates = self.generate_date_range(years_back)
        
        # 统计信息
        total_dates = len(dates)
        processed_dates = 0
        total_documents = 0
        
        print(f"\n第二步：开始收集文档...")
        print(f"总共需要处理 {total_dates} 个日期")
        print("每个日期都会重新启动浏览器进程（无头模式）")
        
        # 询问用户是否继续
        confirm = input(f"\n即将开始收集上海市近{years_back}年的裁判文书，预计需要很长时间。\n是否继续？(y/n): ")
        if confirm.lower() != 'y':
            print("用户取消操作")
            return False
        
        # 按日期遍历收集，每个日期重新启动浏览器
        for i, date_str in enumerate(dates):
            # 极致安全：夜间暂停、长延时、复杂行为模拟、异常检测
            self.simulator.night_pause()
            self.simulator.extreme_random_sleep(180, 600)  # 3~10分钟
            self.simulator.simulate_extreme_human_behavior()
            self.simulator.check_captcha_or_exception()
            # 偶尔跳过某一天，模拟人类疏漏
            if random.random() < 0.01:
                print(f"[极致安全] 偶尔跳过日期 {date_str}，模拟人类疏漏")
                continue

            print(f"\n{'='*100}")
            print(f"进度: {i+1}/{total_dates} ({(i+1)/total_dates*100:.1f}%) - 处理日期: {date_str}")
            print(f"{'='*100}")
            
            # 检查是否已经处理过
            if self.is_date_processed(date_str):
                print(f"⚠ {date_str} 已经处理过，跳过")
                processed_dates += 1
                continue
            
            try:
                # 重新创建浏览器模拟器
                self.simulator = WenshuBrowserSimulator()
                
                # 初始化浏览器（无头模式）
                print("启动浏览器...")
                if not self.simulator.start_browser(headless=True):
                    print(f"✗ {date_str} 浏览器启动失败，跳过")
                    continue
                
                # 设置cookies
                if not self.simulator.setup_cookies():
                    print(f"✗ {date_str} Cookie设置失败，跳过")
                    self.simulator.close_browser()
                    continue
                
                # 打开页面
                if not self.simulator.open_page():
                    print(f"✗ {date_str} 页面打开失败，跳过")
                    self.simulator.close_browser()
                    continue
                
                # 处理当前日期
                doc_count = self.process_date(date_str)
                total_documents += doc_count
                processed_dates += 1
                
                print(f"✓ {date_str} 处理完成，收集到 {doc_count} 个文档")
                
            except Exception as e:
                print(f"✗ 处理日期 {date_str} 时出错: {str(e)}")
            finally:
                # 关闭当前日期的浏览器
                try:
                    self.simulator.close_browser()
                    print(f"✓ 关闭 {date_str} 的浏览器进程")
                except:
                    pass
            
            # 每处理10个日期显示一次统计
            if processed_dates % 10 == 0:
                print(f"\n--- 阶段统计 ---")
                print(f"已处理日期: {processed_dates}/{total_dates}")
                print(f"累计收集文档: {total_documents}")
                print(f"平均每日文档: {total_documents/processed_dates:.1f}")
            
            # 每天后极致延时
            self.simulator.extreme_random_sleep(180, 600)
            self.simulator.simulate_extreme_human_behavior()
        
        # 最终统计
        print(f"\n{'='*80}")
        print("收集完成！")
        print(f"{'='*80}")
        print(f"处理日期数: {processed_dates}")
        print(f"总收集文档数: {total_documents}")
        if processed_dates > 0:
            print(f"平均每日文档: {total_documents/processed_dates:.1f}")
        print(f"URL文件保存位置: {self.url_folder}")
        print(f"文书文件保存位置: {self.doc_folder}")
        
        return True

def main():
    """主函数"""
    print("上海市裁判文书自动化收集系统")
    print("=" * 60)
    
    # 检查依赖
    try:
        from playwright.sync_api import sync_playwright
        print("✓ Playwright 已安装")
    except ImportError:
        print("✗ Playwright 未安装，请先运行:")
        print("  pip install playwright")
        print("  playwright install")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✓ BeautifulSoup 已安装")
    except ImportError:
        print("✗ BeautifulSoup 未安装，请先运行:")
        print("  pip install beautifulsoup4")
        return False
    
    # 创建收集器实例
    collector = ShanghaiDocumentCollector()
    
    # 询问收集年限
    years_input = input("\n请输入要收集的年限 (1-5年，默认3年): ").strip()
    if years_input and years_input.isdigit():
        years_back = int(years_input)
        if years_back < 1 or years_back > 5:
            print("年限设置为默认值: 3年")
            years_back = 3
    else:
        years_back = 3
    
    print(f"\n将收集上海市近{years_back}年的裁判文书")
    
    # 运行收集流程
    success = collector.run_collection(years_back)
    
    if success:
        print("\n✓ 自动化收集完成！")
        print("所有文件已按日期分类保存")
    else:
        print("\n✗ 收集过程中出现问题")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 