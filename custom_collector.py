#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高度个性化裁判文书采集脚本
支持自定义地区、案由（案件类型）、日期范围
"""
import sys
import os
import time
import datetime
import random
from browser_simulator import WenshuBrowserSimulator
from document_cleaner import DocumentCleaner

def generate_date_range(start_date, end_date):
    """生成自定义日期范围的日期列表"""
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += datetime.timedelta(days=1)
    return dates

class CustomDocumentCollector:
    def __init__(self, region, case_reason, start_date, end_date, max_pages=40):
        self.region = region
        self.case_reason = case_reason
        self.start_date = start_date
        self.end_date = end_date
        self.max_pages = max_pages
        self.simulator = WenshuBrowserSimulator()
        self.cleaner = DocumentCleaner()
        self.collected_urls = set()
        self.url_folder = "URL列表"
        self.doc_folder = "文书"
        self.init_folders()

    def init_folders(self):
        if not os.path.exists(self.url_folder):
            os.makedirs(self.url_folder)
        if not os.path.exists(self.doc_folder):
            os.makedirs(self.doc_folder)

    def collect_urls_for_date(self, date_str):
        try:
            if not self.simulator.perform_advanced_search(date_str):
                print(f"✗ {date_str} 高级检索失败")
                return []
            if not self.simulator.select_region(self.region):
                print(f"⚠ {date_str} 选择地区失败，继续执行...")
            if self.case_reason and not self.simulator.select_case_reason(self.case_reason):
                print(f"⚠ {date_str} 选择案由失败，继续执行...")
            if not self.simulator.set_page_size_15():
                print(f"⚠ {date_str} 设置页面大小失败，继续执行...")
            all_links = set()
            current_page = 1
            while current_page <= self.max_pages:
                self.simulator.night_pause()
                self.simulator.extreme_random_sleep(20, 60)
                self.simulator.simulate_extreme_human_behavior()
                self.simulator.check_captcha_or_exception()
                print(f"\n--- 第 {current_page} 页 ---")
                page_links = self.simulator.extract_document_links()
                if page_links:
                    new_links = []
                    for link in page_links:
                        if link['url'] not in self.collected_urls:
                            new_links.append(link)
                            self.collected_urls.add(link['url'])
                    all_links.update(new_links)
                    print(f"✓ 第 {current_page} 页收集到 {len(page_links)} 个链接，去重后新增 {len(new_links)} 个")
                else:
                    print(f"⚠ 第 {current_page} 页未收集到链接")
                if not self.simulator.click_next_page():
                    print("✗ 无法点击下一页，可能已到最后一页")
                    break
                current_page += 1
                self.simulator.extreme_random_sleep(20, 60)
                self.simulator.simulate_extreme_human_behavior()
            print(f"✓ {date_str} 共收集到 {len(all_links)} 个新链接")
            return list(all_links)
        except Exception as e:
            print(f"✗ {date_str} 收集URL失败: {str(e)}")
            return []

    def save_urls_to_file(self, date_str, links):
        if not links:
            print(f"⚠ {date_str} 没有链接需要保存")
            return None
        try:
            filename = os.path.join(self.url_folder, f"{date_str}_{self.region}_文书.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# 裁判文书网 - {self.region} - {self.case_reason} - {date_str}\n")
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
        if not url_list:
            print(f"⚠ {date_str} 没有文档需要下载")
            return
        print(f"\n开始下载和清洗 {date_str} 的文档...")
        date_folder = os.path.join(self.doc_folder, date_str)
        if not os.path.exists(date_folder):
            os.makedirs(date_folder)
        success_count = 0
        fail_count = 0
        for idx, url in enumerate(url_list):
            self.simulator.night_pause()
            self.simulator.extreme_random_sleep(30, 90)
            self.simulator.simulate_extreme_human_behavior()
            self.simulator.check_captcha_or_exception()
            if random.random() < 0.02:
                print(f"[极致安全] 偶尔跳过第{idx+1}篇文书，模拟人类疏漏")
                continue
            try:
                print(f"\n处理文档 {idx+1}/{len(url_list)}: {url['title'][:50]}...")
                response = self.simulator.page.goto(
                    url['url'],
                    wait_until='networkidle',
                    timeout=30000
                )
                if response.status != 200:
                    print(f"✗ 页面响应状态异常: {response.status}")
                    fail_count += 1
                    continue
                html_content = self.simulator.page.content()
                cleaned_text = self.cleaner.clean_document_to_text(html_content)
                if cleaned_text == "未找到文档内容":
                    print(f"✗ 未找到文档内容")
                    fail_count += 1
                    continue
                doc_info = self.cleaner.extract_document_info(html_content)
                case_number = doc_info.get('case_number', '未知案件')
                case_reason = doc_info.get('case_reason', '未知案由')
                safe_title = self.clean_filename(url['title'])
                filename = f"{safe_title}.txt"
                if len(filename) > 100:
                    filename = f"{case_number}_{case_reason}.txt"
                    filename = self.clean_filename(filename)
                file_path = os.path.join(date_folder, filename)
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
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        if len(filename) > 100:
            filename = filename[:100]
        return filename

    def process_date(self, date_str):
        try:
            links = self.collect_urls_for_date(date_str)
            url_file = self.save_urls_to_file(date_str, links)
            if links:
                self.download_and_clean_documents(links, date_str)
            return len(links)
        except Exception as e:
            print(f"✗ 处理日期 {date_str} 失败: {str(e)}")
            return 0

    def run_collection(self):
        print("=" * 80)
        print(f"{self.region} - {self.case_reason} 裁判文书自动化收集系统")
        print("=" * 80)
        dates = generate_date_range(self.start_date, self.end_date)
        total_dates = len(dates)
        processed_dates = 0
        total_documents = 0
        print(f"\n开始收集文档...\n总共需要处理 {total_dates} 个日期")
        for i, date_str in enumerate(dates):
            self.simulator.night_pause()
            self.simulator.extreme_random_sleep(180, 600)
            self.simulator.simulate_extreme_human_behavior()
            self.simulator.check_captcha_or_exception()
            if random.random() < 0.01:
                print(f"[极致安全] 偶尔跳过日期 {date_str}，模拟人类疏漏")
                continue
            print(f"\n{'='*100}")
            print(f"进度: {i+1}/{total_dates} ({(i+1)/total_dates*100:.1f}%) - 处理日期: {date_str}")
            print(f"{'='*100}")
            try:
                self.simulator = WenshuBrowserSimulator()
                if not self.simulator.start_browser(headless=True):
                    print(f"✗ {date_str} 浏览器启动失败，跳过")
                    continue
                if not self.simulator.setup_cookies():
                    print(f"✗ {date_str} Cookie设置失败，跳过")
                    self.simulator.close_browser()
                    continue
                if not self.simulator.open_page():
                    print(f"✗ {date_str} 页面打开失败，跳过")
                    self.simulator.close_browser()
                    continue
                doc_count = self.process_date(date_str)
                total_documents += doc_count
                processed_dates += 1
                print(f"✓ {date_str} 处理完成，收集到 {doc_count} 个文档")
            except Exception as e:
                print(f"✗ 处理日期 {date_str} 时出错: {str(e)}")
            finally:
                try:
                    self.simulator.close_browser()
                    print(f"✓ 关闭 {date_str} 的浏览器进程")
                except:
                    pass
            if processed_dates % 10 == 0:
                print(f"\n--- 阶段统计 ---")
                print(f"已处理日期: {processed_dates}/{total_dates}")
                print(f"累计收集文档: {total_documents}")
                print(f"平均每日文档: {total_documents/processed_dates:.1f}")
            self.simulator.extreme_random_sleep(180, 600)
            self.simulator.simulate_extreme_human_behavior()
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
    print("高度个性化裁判文书采集系统")
    print("=" * 60)
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
    region = input("请输入采集地区（如 上海市、北京市、广东省 等）: ").strip() or "上海市"
    case_reason = input("请输入案由/案件类型（如 知识产权权属、合同纠纷、刑事案件 等，留空为全部）: ").strip()
    start_date_str = input("请输入起始日期 (YYYY-MM-DD，默认三年前): ").strip()
    end_date_str = input("请输入结束日期 (YYYY-MM-DD，默认今天): ").strip()
    today = datetime.date.today()
    default_start = today - datetime.timedelta(days=3*365)
    try:
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else default_start
    except:
        start_date = default_start
    try:
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else today
    except:
        end_date = today
    print(f"\n将采集 {region} - {case_reason or '全部案由'}，日期范围: {start_date} ~ {end_date}")
    collector = CustomDocumentCollector(region, case_reason, start_date, end_date)
    success = collector.run_collection()
    if success:
        print("\n✓ 自动化收集完成！\n所有文件已按日期分类保存")
    else:
        print("\n✗ 收集过程中出现问题")
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)