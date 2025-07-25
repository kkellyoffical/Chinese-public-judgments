#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
裁判文书网爬取项目 - 浏览器模拟器
功能：使用playwright模拟真实浏览器，测试页面访问权限
"""

import asyncio
import time
import random
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import json
import datetime

class WenshuBrowserSimulator:
    """裁判文书网浏览器模拟器 - 使用Playwright"""
    
    def __init__(self):
        """初始化浏览器模拟器"""
        self.base_url = "https://wenshu.court.gov.cn/website/wenshu/181029CR4M5A62CH/index.html?"
        self.playwright = None
        self.browser = None
        self.page = None
        self.cookies = self.parse_cookies()
        self.last_fingerprint_change = datetime.datetime.now()
        self.fingerprint_days = random.randint(1, 3)  # 1~3天切换一次指纹
        self.current_ua = None
        self.current_viewport = None
        self.current_langs = None
        self.ua_pool = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
        ]
        self.viewport_pool = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1536, 'height': 864},
            {'width': 1440, 'height': 900},
            {'width': 1600, 'height': 900}
        ]
        self.langs_pool = [
            ['zh-CN', 'zh', 'en-US', 'en'],
            ['zh-CN', 'zh', 'en'],
            ['zh-CN', 'en-US', 'en'],
            ['zh-CN', 'zh'],
        ]
        
    def random_sleep(self, min_seconds=2, max_seconds=8):
        """随机延时，模拟真实用户操作间隔"""
        sleep_time = random.uniform(min_seconds, max_seconds)
        print(f"等待 {sleep_time:.1f} 秒...")
        time.sleep(sleep_time)
    
    def simulate_human_behavior(self):
        """模拟人类行为：随机鼠标移动、滚动等"""
        try:
            # 随机鼠标移动
            viewport = self.page.viewport_size
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, viewport['width'] - 100)
                y = random.randint(100, viewport['height'] - 100)
                self.page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.3))
            
            # 随机滚动
            scroll_amount = random.randint(-300, 300)
            self.page.mouse.wheel(0, scroll_amount)
            time.sleep(random.uniform(0.5, 1.5))
            
            # 随机等待
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"模拟人类行为时出错: {str(e)}")
    
    def safe_click(self, selector, timeout=30000):
        """安全点击，包含人类行为模拟"""
        try:
            element = self.page.wait_for_selector(selector, timeout=timeout)
            if element:
                # 模拟真实用户行为
                element.scroll_into_view_if_needed()
                time.sleep(random.uniform(0.5, 1.5))
                
                # 移动鼠标到元素
                box = element.bounding_box()
                if box:
                    click_x = box['x'] + box['width'] / 2 + random.randint(-10, 10)
                    click_y = box['y'] + box['height'] / 2 + random.randint(-5, 5)
                    self.page.mouse.move(click_x, click_y)
                    time.sleep(random.uniform(0.2, 0.5))
                
                # 点击
                element.click()
                time.sleep(random.uniform(0.3, 0.8))
                return True
        except Exception as e:
            print(f"安全点击失败: {str(e)}")
            return False
        return False
    
    def safe_fill(self, selector, text, timeout=30000):
        """安全填充文本，模拟真实打字"""
        try:
            element = self.page.wait_for_selector(selector, timeout=timeout)
            if element:
                element.scroll_into_view_if_needed()
                time.sleep(random.uniform(0.3, 0.8))
                
                # 清空现有内容
                element.click()
                time.sleep(random.uniform(0.2, 0.5))
                element.fill('')
                time.sleep(random.uniform(0.2, 0.5))
                
                # 模拟真实打字速度
                for char in text:
                    element.type(char)
                    time.sleep(random.uniform(0.05, 0.15))
                
                time.sleep(random.uniform(0.3, 0.8))
                return True
        except Exception as e:
            print(f"安全填充失败: {str(e)}")
            return False
        return False
        
    def parse_cookies(self):
        """解析身份令牌Cookie"""
        # 使用用户提供的最新Cookie值
        cookie_string = "*"
        
        # 解析Cookie字符串转换为playwright格式
        cookies = []
        for cookie in cookie_string.split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                cookies.append({
                    'name': key,
                    'value': value,
                    'domain': 'wenshu.court.gov.cn',
                    'path': '/'
                })
        
        print("✓ 身份令牌已解析:")
        for cookie in cookies:
            print(f"  {cookie['name']}: {cookie['value'][:50]}{'...' if len(cookie['value']) > 50 else ''}")
        
        return cookies
    
    def night_pause(self):
        """夜间自动暂停（0:00~7:00）"""
        now = datetime.datetime.now()
        if 0 <= now.hour < 7:
            pause_time = (7 - now.hour) * 3600 - now.minute * 60 - now.second
            print(f"夜间暂停，休息 {pause_time//60} 分钟...")
            time.sleep(pause_time)

    def update_fingerprint(self):
        """每隔1~3天自动切换指纹"""
        now = datetime.datetime.now()
        if (now - self.last_fingerprint_change).days >= self.fingerprint_days:
            self.current_ua = random.choice(self.ua_pool)
            self.current_viewport = random.choice(self.viewport_pool)
            self.current_langs = random.choice(self.langs_pool)
            self.last_fingerprint_change = now
            self.fingerprint_days = random.randint(1, 3)
            print(f"[指纹切换] User-Agent: {self.current_ua}, 分辨率: {self.current_viewport}, 语言: {self.current_langs}")
        elif self.current_ua is None:
            self.current_ua = random.choice(self.ua_pool)
            self.current_viewport = random.choice(self.viewport_pool)
            self.current_langs = random.choice(self.langs_pool)

    def extreme_random_sleep(self, min_seconds=15, max_seconds=45):
        """极致安全：极长且不规律的延时"""
        sleep_time = random.uniform(min_seconds, max_seconds)
        print(f"[极致安全] 等待 {sleep_time:.1f} 秒...")
        time.sleep(sleep_time)

    def simulate_extreme_human_behavior(self):
        """极致安全：复杂人类行为模拟"""
        try:
            viewport = self.page.viewport_size
            # 多次鼠标移动
            for _ in range(random.randint(5, 12)):
                x = random.randint(50, viewport['width'] - 50)
                y = random.randint(50, viewport['height'] - 50)
                self.page.mouse.move(x, y)
                time.sleep(random.uniform(0.2, 1.2))
            # 多次滚动
            for _ in range(random.randint(2, 5)):
                scroll_amount = random.randint(-500, 500)
                self.page.mouse.wheel(0, scroll_amount)
                time.sleep(random.uniform(0.5, 2.5))
            # 多次点击空白
            for _ in range(random.randint(1, 3)):
                x = random.randint(10, viewport['width'] - 10)
                y = random.randint(10, viewport['height'] - 10)
                self.page.mouse.click(x, y)
                time.sleep(random.uniform(0.5, 1.5))
            # 偶尔点开无关链接
            if random.random() < 0.2:
                print("[极致安全] 偶尔点开无关链接")
                try:
                    self.page.click('a:has-text("帮助")')
                    time.sleep(random.uniform(2, 5))
                    self.page.go_back()
                except:
                    pass
            # 偶尔刷新页面
            if random.random() < 0.1:
                print("[极致安全] 偶尔刷新页面")
                self.page.reload()
                time.sleep(random.uniform(2, 5))
            # 偶尔输入错误再修正
            if random.random() < 0.1:
                print("[极致安全] 偶尔输入错误再修正")
                try:
                    el = self.page.query_selector('input')
                    if el:
                        el.click()
                        el.type('1234')
                        time.sleep(random.uniform(0.5, 1.5))
                        el.fill('')
                except:
                    pass
            # 偶尔长时间停顿
            if random.random() < 0.05:
                long_pause = random.uniform(300, 1200)
                print(f"[极致安全] 偶尔离开电脑，休息 {long_pause//60} 分钟...")
                time.sleep(long_pause)
        except Exception as e:
            print(f"极致人类行为模拟出错: {str(e)}")

    def check_captcha_or_exception(self):
        """检测验证码或异常页面，遇到则长时间暂停"""
        content = self.page.content()
        if '验证码' in content or '请完成安全验证' in content or '访问过于频繁' in content:
            pause_time = random.uniform(1800, 7200)
            print(f"[极致安全] 检测到验证码/异常，暂停 {pause_time//60} 分钟...")
            time.sleep(pause_time)
            return True
        return False

    def start_browser(self, headless=False):
        self.night_pause()
        self.update_fingerprint()
        print("\n正在启动浏览器...")
        
        try:
            # 启动playwright
            self.playwright = sync_playwright().start()
            
            # 更强的反检测参数
            self.browser = self.playwright.chromium.launch(
                headless=headless,
                slow_mo=1000,  # 每个操作间隔1秒，模拟真实用户
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--exclude-switches=enable-automation',
                    '--disable-extensions-except',
                    '--disable-plugins-discovery',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor,TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--ignore-certificate-errors',
                    '--ignore-ssl-errors',
                    '--ignore-certificate-errors-spki-list',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--hide-scrollbars',
                    '--mute-audio',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows'
                ]
            )
            
            # 随机选择用户代理和分辨率
            import random
            
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
            ]
            
            viewports = [
                {'width': 1920, 'height': 1080},
                {'width': 1366, 'height': 768},
                {'width': 1536, 'height': 864},
                {'width': 1440, 'height': 900},
                {'width': 1600, 'height': 900}
            ]
            
            selected_ua = random.choice(user_agents)
            selected_viewport = random.choice(viewports)
            
            # 创建新页面
            self.page = self.browser.new_page(
                user_agent=self.current_ua,
                viewport=self.current_viewport
            )
            
            # 更强的反检测脚本
            self.page.add_init_script("""
                // 移除webdriver标识
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // 模拟真实的插件
                Object.defineProperty(navigator, 'plugins', {
                    get: () => Array.from({length: 5}, (_, i) => ({
                        description: `Plugin ${i}`,
                        filename: `plugin${i}.dll`,
                        name: `Plugin ${i}`
                    })),
                });
                
                // 模拟语言设置
                Object.defineProperty(navigator, 'languages', {
                    get: () => {self.current_langs},
                });
                
                // 移除Chrome特有的自动化标识
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                });
                
                // 模拟硬件并发
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8,
                });
                
                // 模拟内存信息
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8,
                });
                
                // 覆盖permissions查询
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // 移除自动化相关属性
                delete window.chrome;
                
                // 模拟正常的window.chrome对象
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {
                        return {
                            requestTime: Date.now() * 0.001,
                            startLoadTime: Date.now() * 0.001,
                            commitLoadTime: Date.now() * 0.001,
                            finishDocumentLoadTime: Date.now() * 0.001,
                            finishLoadTime: Date.now() * 0.001,
                            firstPaintTime: Date.now() * 0.001,
                            firstPaintAfterLoadTime: Date.now() * 0.001,
                            navigationType: 'Other',
                            wasFetchedViaSpdy: false,
                            wasNpnNegotiated: false,
                            npnNegotiatedProtocol: '',
                            wasAlternateProtocolAvailable: false,
                            connectionInfo: 'http/1.1'
                        };
                    },
                    csi: function() {
                        return {
                            startE: Date.now(),
                            onloadT: Date.now(),
                            pageT: Date.now(),
                            tran: 15
                        };
                    }
                };
            """)
            
            # 设置额外的HTTP头部
            self.page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-CH-UA': '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
                'Sec-CH-UA-Mobile': '?0',
                'Sec-CH-UA-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Referer': 'https://cn.bing.com/'
            })
            
            print("✓ 浏览器启动成功")
            return True
            
        except Exception as e:
            print(f"✗ 浏览器启动失败: {str(e)}")
            return False
    
    def setup_cookies(self):
        """设置身份令牌Cookie"""
        try:
            print("\n正在设置Cookie...")
            
            # 先访问一次主页面以建立域名上下文
            print("首次访问页面以建立域名上下文...")
            response = self.page.goto(
                self.base_url,
                wait_until='domcontentloaded',
                timeout=30000
            )
            print(f"初次访问响应状态: {response.status}")
            
            # 等待页面完全加载
            self.page.wait_for_load_state('networkidle')
            
            # 获取当前页面的cookies（如果有的话）
            existing_cookies = self.page.context.cookies()
            print(f"页面现有Cookie数量: {len(existing_cookies)}")
            
            # 添加我们的身份令牌cookies
            print("正在添加身份令牌Cookie...")
            self.page.context.add_cookies(self.cookies)
            
            # 验证Cookie是否设置成功
            updated_cookies = self.page.context.cookies()
            print(f"Cookie设置后总数量: {len(updated_cookies)}")
            
            # 显示设置的关键Cookie
            for cookie in updated_cookies:
                if cookie['name'] in ['wzws_sessionid', 'SESSION', 'wzws_cid']:
                    print(f"✓ {cookie['name']}: {cookie['value'][:20]}...")
            
            print("✓ Cookie设置成功")
            return True
            
        except Exception as e:
            print(f"✗ Cookie设置失败: {str(e)}")
            return False
    
    def open_page(self, reload=True):
        """打开裁判文书网页面"""
        print(f"\n正在验证登录状态...")
        
        try:
            if reload:
                # 刷新页面以验证Cookie效果
                print("刷新页面以验证Cookie效果...")
                response = self.page.goto(
                    self.base_url,
                    wait_until='networkidle',  # 等待网络空闲
                    timeout=30000  # 30秒超时
                )
                print(f"✓ 页面响应状态: {response.status}")
            
            # 等待页面加载完成
            self.page.wait_for_load_state('domcontentloaded')
            
            # 模拟真实用户行为
            self.random_sleep(3, 6)
            self.simulate_human_behavior()
            
            # 检查页面标题
            title = self.page.title()
            print(f"✓ 页面标题: {title}")
            
            # 检查页面内容
            content = self.page.content()
            
            if "裁判文书网" in content:
                print("✓ 页面内容验证通过，确认为裁判文书网")
            else:
                print("⚠ 页面内容可能不正确，请检查")
            
            # 详细检查登录状态
            self.check_login_status(content)
            
            # 截图保存
            self.page.screenshot(path='wenshu_page.png')
            print("✓ 页面截图已保存为 wenshu_page.png")
            
            # 再次模拟用户行为
            self.random_sleep(2, 4)
            
            return True
            
        except Exception as e:
            print(f"✗ 页面访问失败: {str(e)}")
            return False
    
    def check_login_status(self, content):
        """检查登录状态"""
        print("\n检查登录状态...")
        
        # 检查多个可能的登录状态指标
        login_indicators = [
            ("登录", "检测到登录按钮"),
            ("注册", "检测到注册按钮"), 
            ("用户名", "检测到用户名输入框"),
            ("密码", "检测到密码输入框"),
            ("验证码", "检测到验证码"),
            ("个人中心", "检测到个人中心（可能已登录）"),
            ("退出", "检测到退出按钮（可能已登录）"),
            ("我的", "检测到我的相关内容（可能已登录）")
        ]
        
        found_indicators = []
        for indicator, description in login_indicators:
            if indicator in content:
                found_indicators.append(description)
        
        if found_indicators:
            print("发现以下登录相关内容:")
            for indicator in found_indicators:
                print(f"  - {indicator}")
        else:
            print("未检测到明显的登录相关内容")
        
        # 尝试查找特定的登录状态元素
        try:
            # 检查是否有登录按钮
            login_button = self.page.query_selector('a[href*="login"], button[class*="login"], .login-btn')
            if login_button:
                print("⚠ 发现登录按钮，当前可能未登录")
            
            # 检查是否有用户信息
            user_info = self.page.query_selector('.user-info, .user-name, .username')
            if user_info:
                print("✓ 发现用户信息元素，可能已登录")
            
        except Exception as e:
            print(f"DOM元素检查时出错: {str(e)}")
        
        # 输出页面URL以供调试
        print(f"当前页面URL: {self.page.url}")
        
        # 检查是否有重定向
        if self.page.url != self.base_url:
            print(f"⚠ 页面发生重定向，从 {self.base_url} 跳转到 {self.page.url}")
        
        return found_indicators
    
    def test_login_access(self):
        """测试登录状态 - 尝试访问需要登录的功能"""
        print("\n测试登录状态...")
        
        try:
            # 测试1：尝试访问我的收藏或个人中心
            test_urls = [
                "https://wenshu.court.gov.cn/website/wenshu/181107ANFZ0BXSK4/index.html?pageId=f89e9d1b-4c8e-4d5e-8e5a-0b5e5e5e5e5e",  # 示例个人中心URL
                "https://wenshu.court.gov.cn/website/wenshu/181107ANFZ0BXSK4/index.html"  # 主页面
            ]
            
            print("正在检查页面中的登录状态指示器...")
            
            # 等待页面完全加载
            self.page.wait_for_load_state('networkidle')
            
            # 检查页面中是否有登录状态的JavaScript变量
            login_status = self.page.evaluate("""
                () => {
                    // 检查常见的登录状态变量
                    const indicators = [];
                    
                    // 检查是否有登录相关的全局变量
                    if (typeof window.userInfo !== 'undefined') {
                        indicators.push('找到userInfo变量');
                    }
                    if (typeof window.isLogin !== 'undefined') {
                        indicators.push('找到isLogin变量: ' + window.isLogin);
                    }
                    if (typeof window.loginStatus !== 'undefined') {
                        indicators.push('找到loginStatus变量: ' + window.loginStatus);
                    }
                    
                    // 检查登录按钮
                    const loginBtn = document.querySelector('a[href*="login"], .login-btn, [class*="login"]');
                    if (loginBtn) {
                        indicators.push('找到登录按钮: ' + loginBtn.textContent);
                    }
                    
                    // 检查用户信息
                    const userInfo = document.querySelector('.user-info, .user-name, [class*="user"]');
                    if (userInfo) {
                        indicators.push('找到用户信息元素: ' + userInfo.textContent);
                    }
                    
                    return indicators;
                }
            """)
            
            if login_status:
                print("JavaScript检查结果:")
                for status in login_status:
                    print(f"  ✓ {status}")
            else:
                print("JavaScript检查未发现明显的登录状态指示器")
            
            # 检查Cookie是否正确设置
            current_cookies = self.page.context.cookies()
            auth_cookies = [c for c in current_cookies if c['name'] in ['wzws_sessionid', 'SESSION', 'wzws_cid']]
            
            print(f"\n认证Cookie检查:")
            if auth_cookies:
                for cookie in auth_cookies:
                    print(f"  ✓ {cookie['name']}: {cookie['value'][:30]}...")
            else:
                print("  ✗ 未找到认证Cookie")
            
            # 尝试查找更具体的登录状态
            try:
                # 检查是否有退出登录的链接
                logout_link = self.page.query_selector('a[href*="logout"], a[href*="exit"]')
                if logout_link:
                    print("  ✓ 找到退出登录链接，可能已登录")
                    return True
                
                # 检查是否能找到用户相关的菜单
                user_menu = self.page.query_selector('.user-menu, .user-dropdown, [class*="user-center"]')
                if user_menu:
                    print("  ✓ 找到用户菜单，可能已登录")
                    return True
                
            except Exception as e:
                print(f"  ⚠ DOM查询时出错: {str(e)}")
            
            return False
            
        except Exception as e:
            print(f"✗ 登录状态测试失败: {str(e)}")
            return False
    
    def try_manual_login_check(self):
        """尝试手动登录检查 - 如果自动登录失败"""
        print("\n尝试手动登录验证...")
        
        try:
            # 查找登录相关的链接或按钮
            login_elements = self.page.query_selector_all('a[href*="login"], button[class*="login"], .login-btn')
            
            if login_elements:
                print(f"找到 {len(login_elements)} 个登录相关元素:")
                for i, elem in enumerate(login_elements):
                    try:
                        text = elem.text_content()
                        href = elem.get_attribute('href') if elem.get_attribute('href') else '无链接'
                        print(f"  {i+1}. 文本: '{text}' | 链接: {href}")
                    except:
                        print(f"  {i+1}. 无法获取元素信息")
                
                # 尝试点击第一个登录按钮（如果存在）
                if login_elements:
                    print("\n尝试点击登录按钮...")
                    try:
                        login_elements[0].click()
                        self.page.wait_for_load_state('networkidle', timeout=10000)
                        
                        # 检查是否跳转到登录页面
                        current_url = self.page.url
                        if 'login' in current_url.lower():
                            print("✓ 成功跳转到登录页面")
                            
                            # 截图保存登录页面
                            self.page.screenshot(path='login_page.png')
                            print("✓ 登录页面截图已保存为 login_page.png")
                            
                            # 检查登录页面元素
                            self.check_login_page_elements()
                            
                        else:
                            print("⚠ 未跳转到登录页面")
                            
                    except Exception as e:
                        print(f"✗ 点击登录按钮失败: {str(e)}")
            else:
                print("未找到登录相关元素")
                
                # 尝试直接访问登录页面
                login_url = "https://wenshu.court.gov.cn/website/wenshu/181107ANFZ0BXSK4/index.html?pageId=login"
                print(f"尝试直接访问登录页面: {login_url}")
                
                try:
                    self.page.goto(login_url, wait_until='networkidle', timeout=30000)
                    self.page.screenshot(path='direct_login_page.png')
                    print("✓ 直接登录页面截图已保存")
                except Exception as e:
                    print(f"✗ 直接访问登录页面失败: {str(e)}")
                    
        except Exception as e:
            print(f"✗ 手动登录检查失败: {str(e)}")
            
    def check_login_page_elements(self):
        """检查登录页面的元素"""
        print("\n检查登录页面元素...")
        
        try:
            # 检查用户名输入框
            username_input = self.page.query_selector('input[type="text"], input[name*="user"], input[id*="user"]')
            if username_input:
                print("✓ 找到用户名输入框")
            
            # 检查密码输入框
            password_input = self.page.query_selector('input[type="password"], input[name*="pass"], input[id*="pass"]')
            if password_input:
                print("✓ 找到密码输入框")
            
            # 检查验证码
            captcha_input = self.page.query_selector('input[name*="captcha"], input[id*="captcha"], input[name*="code"]')
            if captcha_input:
                print("⚠ 找到验证码输入框，可能需要验证码")
            
            # 检查登录按钮
            submit_button = self.page.query_selector('button[type="submit"], input[type="submit"], .submit-btn')
            if submit_button:
                print("✓ 找到提交按钮")
                
            # 检查其他认证方式
            other_auth = self.page.query_selector_all('.auth-method, .login-method, [class*="oauth"]')
            if other_auth:
                print(f"✓ 找到 {len(other_auth)} 个其他认证方式")
                
        except Exception as e:
            print(f"✗ 检查登录页面元素失败: {str(e)}")
    
    def test_connection(self):
        """测试网站连接"""
        print("\n开始测试裁判文书网连接...")
        
        # 启动浏览器
        if not self.start_browser(headless=True):  # 无头模式运行
            return False
        
        # 设置cookies
        if not self.setup_cookies():
            return False
        
        # 打开页面
        if not self.open_page():
            return False
        
        # 测试登录状态
        login_result = self.test_login_access()
        if login_result:
            print("✓ 登录状态验证成功")
        else:
            print("⚠ 登录状态验证未通过，进行手动登录检查...")
            self.try_manual_login_check()
        
        print("✓ 网站连接测试完成")
        return True
    
    def find_advanced_search(self):
        """查找高级检索元素"""
        print("\n正在查找高级检索...")
        
        try:
            # 等待页面完全加载
            self.page.wait_for_load_state('networkidle')
            
            # 尝试多种选择器查找高级检索
            selectors = [
                'div.advenced-search',
                '.advenced-search',
                'div[class*="advenced-search"]',
                'div[class*="advanced-search"]',
                'a[href*="advanced"]',
                'button[class*="advanced"]',
                'span:has-text("高级检索")',
                'a:has-text("高级检索")',
                'div:has-text("高级检索")'
            ]
            
            advanced_element = None
            for selector in selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        advanced_element = element
                        print(f"✓ 找到高级检索元素，选择器: {selector}")
                        break
                except Exception as e:
                    continue
            
            if not advanced_element:
                print("⚠ 未找到高级检索元素，尝试通过文本查找...")
                # 尝试通过文本内容查找
                advanced_element = self.page.query_selector('xpath=//div[contains(text(), "高级检索")] | //a[contains(text(), "高级检索")] | //span[contains(text(), "高级检索")]')
                
            if advanced_element:
                print("✓ 成功找到高级检索元素")
                return advanced_element
            else:
                print("✗ 未找到高级检索元素")
                # 截图以便调试
                self.page.screenshot(path='no_advanced_search.png')
                print("✓ 调试截图已保存为 no_advanced_search.png")
                return None
                
        except Exception as e:
            print(f"✗ 查找高级检索时出错: {str(e)}")
            return None
    
    def click_advanced_search(self):
        """点击高级检索"""
        print("\n正在点击高级检索...")
        
        try:
            # 模拟真实用户浏览行为
            self.simulate_human_behavior()
            self.random_sleep(2, 5)
            
            # 查找高级检索元素
            advanced_element = self.find_advanced_search()
            
            if not advanced_element:
                return False
            
            # 使用安全点击方法
            if not self.safe_click('.advenced-search, div[class*="advenced-search"], a:has-text("高级检索"), div:has-text("高级检索")'):
                # 如果安全点击失败，尝试传统方式
                advanced_element.scroll_into_view_if_needed()
                self.random_sleep(1, 3)
                advanced_element.click()
            
            # 随机等待
            self.random_sleep(3, 6)
            
            # 等待页面响应
            self.page.wait_for_load_state('networkidle', timeout=15000)
            
            print("✓ 成功点击高级检索")
            
            # 再次模拟用户行为
            self.simulate_human_behavior()
            
            # 截图保存点击后的页面
            self.page.screenshot(path='advanced_search_opened.png')
            print("✓ 高级检索打开后的截图已保存为 advanced_search_opened.png")
            
            return True
            
        except Exception as e:
            print(f"✗ 点击高级检索失败: {str(e)}")
            return False
    
    def set_judgment_date(self, date_str="2025-07-21"):
        """设置裁判日期"""
        print(f"\n正在设置裁判日期为: {date_str}")
        
        try:
            # 模拟用户浏览行为
            self.simulate_human_behavior()
            self.random_sleep(2, 4)
            
            # 等待页面加载
            self.page.wait_for_load_state('networkidle')
            
            # 查找日期输入框
            start_date_input = self.page.query_selector('#cprqStart')
            end_date_input = self.page.query_selector('#cprqEnd')
            
            if not start_date_input:
                print("⚠ 未找到开始日期输入框，尝试其他选择器...")
                start_date_input = self.page.query_selector('input[id="cprqStart"]')
            
            if not end_date_input:
                print("⚠ 未找到结束日期输入框，尝试其他选择器...")
                end_date_input = self.page.query_selector('input[id="cprqEnd"]')
            
            if start_date_input and end_date_input:
                print("✓ 找到日期输入框")
                
                # 使用安全填充方法设置开始日期
                if not self.safe_fill('#cprqStart', date_str):
                    # 如果安全填充失败，使用传统方式
                    start_date_input.click()
                    self.random_sleep(0.5, 1.5)
                    start_date_input.fill('')
                    self.random_sleep(0.3, 0.8)
                    start_date_input.fill(date_str)
                print(f"✓ 设置开始日期: {date_str}")
                
                # 随机等待
                self.random_sleep(1, 3)
                
                # 使用安全填充方法设置结束日期
                if not self.safe_fill('#cprqEnd', date_str):
                    # 如果安全填充失败，使用传统方式
                    end_date_input.click()
                    self.random_sleep(0.5, 1.5)
                    end_date_input.fill('')
                    self.random_sleep(0.3, 0.8)
                    end_date_input.fill(date_str)
                print(f"✓ 设置结束日期: {date_str}")
                
                # 随机等待让输入生效
                self.random_sleep(2, 4)
                
                # 截图保存设置后的状态
                self.page.screenshot(path='date_set.png')
                print("✓ 日期设置后的截图已保存为 date_set.png")
                
                return True
                
            else:
                print("✗ 未找到日期输入框")
                # 尝试查找包含日期相关的元素
                date_elements = self.page.query_selector_all('input[class*="laydate"], input[class*="date"], input[title*="裁判"]')
                if date_elements:
                    print(f"找到 {len(date_elements)} 个可能的日期元素:")
                    for i, elem in enumerate(date_elements):
                        try:
                            elem_id = elem.get_attribute('id')
                            elem_class = elem.get_attribute('class')
                            elem_title = elem.get_attribute('title')
                            print(f"  {i+1}. ID: {elem_id}, Class: {elem_class}, Title: {elem_title}")
                        except:
                            pass
                
                return False
                
        except Exception as e:
            print(f"✗ 设置裁判日期失败: {str(e)}")
            return False
    
    def click_search_button(self):
        """点击检索按钮"""
        print("\n正在点击检索按钮...")
        
        try:
            # 查找检索按钮
            search_button = self.page.query_selector('#searchBtn')
            
            if not search_button:
                print("⚠ 未找到检索按钮，尝试其他选择器...")
                search_button = self.page.query_selector('a[id="searchBtn"]')
            
            if not search_button:
                # 尝试通过文本查找
                search_button = self.page.query_selector('xpath=//a[contains(text(), "检索")] | //button[contains(text(), "检索")]')
            
            if search_button:
                print("✓ 找到检索按钮")
                
                # 滚动到按钮位置
                search_button.scroll_into_view_if_needed()
                
                # 点击检索按钮
                search_button.click()
                print("✓ 成功点击检索按钮")
                
                # 等待搜索结果加载
                print("正在等待搜索结果加载...")
                self.page.wait_for_load_state('networkidle', timeout=30000)
                
                # 截图保存搜索结果
                self.page.screenshot(path='search_results.png')
                print("✓ 搜索结果截图已保存为 search_results.png")
                
                return True
                
            else:
                print("✗ 未找到检索按钮")
                # 查找所有可能的搜索按钮
                search_elements = self.page.query_selector_all('a[href*="search"], button[class*="search"], input[type="submit"]')
                if search_elements:
                    print(f"找到 {len(search_elements)} 个可能的搜索按钮:")
                    for i, elem in enumerate(search_elements):
                        try:
                            text = elem.text_content()
                            elem_id = elem.get_attribute('id')
                            elem_class = elem.get_attribute('class')
                            print(f"  {i+1}. 文本: '{text}', ID: {elem_id}, Class: {elem_class}")
                        except:
                            pass
                
                return False
                
        except Exception as e:
            print(f"✗ 点击检索按钮失败: {str(e)}")
            return False
    
    def perform_advanced_search(self, date_str="2025-07-21"):
        """执行高级检索的完整流程"""
        print("=" * 60)
        print("开始执行高级检索流程")
        print("=" * 60)
        
        try:
            # 第一步：点击高级检索
            if not self.click_advanced_search():
                print("✗ 高级检索流程失败：无法打开高级检索")
                return False
            
            # 第二步：设置裁判日期
            if not self.set_judgment_date(date_str):
                print("✗ 高级检索流程失败：无法设置裁判日期")
                return False
            
            # 第三步：点击检索按钮
            if not self.click_search_button():
                print("✗ 高级检索流程失败：无法点击检索按钮")
                return False
            
            print("=" * 60)
            print("✓ 高级检索流程执行完成！")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"✗ 高级检索流程执行失败: {str(e)}")
            return False
    
    def select_region_shanghai(self):
        """选择地域：上海市"""
        print("\n正在选择地域：上海市...")
        
        try:
            # 等待页面加载
            self.page.wait_for_load_state('networkidle')
            
            # 查找地域及法院列表
            region_selectors = [
                'div:has-text("地域及法院")',
                '.region-list',
                'div[class*="region"]',
                'div[class*="area"]',
                'div:has-text("上海市")'
            ]
            
            # 查找上海市选项
            shanghai_element = None
            for selector in region_selectors:
                try:
                    # 查找包含上海市的元素
                    elements = self.page.query_selector_all(f'{selector} >> text="上海市"')
                    if elements:
                        shanghai_element = elements[0]
                        print(f"✓ 找到上海市选项，选择器: {selector}")
                        break
                except:
                    continue
            
            if not shanghai_element:
                # 尝试直接查找上海市
                shanghai_element = self.page.query_selector('text="上海市"')
                if shanghai_element:
                    print("✓ 直接找到上海市选项")
            
            if not shanghai_element:
                # 尝试通过xpath查找
                shanghai_element = self.page.query_selector('xpath=//div[contains(text(), "上海市")] | //a[contains(text(), "上海市")] | //span[contains(text(), "上海市")]')
                if shanghai_element:
                    print("✓ 通过xpath找到上海市选项")
            
            if shanghai_element:
                # 滚动到元素位置
                shanghai_element.scroll_into_view_if_needed()
                
                # 点击上海市
                shanghai_element.click()
                print("✓ 成功选择上海市")
                
                # 等待页面更新
                self.page.wait_for_load_state('networkidle', timeout=10000)
                
                # 截图保存
                self.page.screenshot(path='shanghai_selected.png')
                print("✓ 上海市选择后的截图已保存为 shanghai_selected.png")
                
                return True
            else:
                print("✗ 未找到上海市选项")
                
                # 查找所有可能的地域选项
                region_elements = self.page.query_selector_all('div:has-text("市"), a:has-text("市"), span:has-text("市")')
                if region_elements:
                    print(f"找到 {len(region_elements)} 个地域选项:")
                    for i, elem in enumerate(region_elements[:10]):  # 只显示前10个
                        try:
                            text = elem.text_content()
                            print(f"  {i+1}. {text}")
                        except:
                            pass
                
                return False
                
        except Exception as e:
            print(f"✗ 选择上海市失败: {str(e)}")
            return False
    
    def set_page_size_15(self):
        """设置每页显示15条"""
        print("\n正在设置每页显示15条...")
        
        try:
            # 等待页面加载
            self.page.wait_for_load_state('networkidle')
            
            # 查找页面大小选择下拉框
            page_size_select = self.page.query_selector('select.pageSizeSelect')
            
            if not page_size_select:
                print("⚠ 未找到页面大小选择框，尝试其他选择器...")
                page_size_select = self.page.query_selector('select[class*="pageSize"]')
            
            if page_size_select:
                print("✓ 找到页面大小选择框")
                
                # 滚动到元素位置
                page_size_select.scroll_into_view_if_needed()
                
                # 选择15条
                page_size_select.select_option('15')
                print("✓ 设置每页显示15条")
                
                # 等待页面更新
                self.page.wait_for_load_state('networkidle', timeout=10000)
                
                # 截图保存
                self.page.screenshot(path='pagesize_15_set.png')
                print("✓ 页面大小设置后的截图已保存为 pagesize_15_set.png")
                
                return True
            else:
                print("✗ 未找到页面大小选择框")
                
                # 查找所有select元素
                select_elements = self.page.query_selector_all('select')
                if select_elements:
                    print(f"找到 {len(select_elements)} 个选择框:")
                    for i, elem in enumerate(select_elements):
                        try:
                            class_name = elem.get_attribute('class')
                            print(f"  {i+1}. Class: {class_name}")
                        except:
                            pass
                
                return False
                
        except Exception as e:
            print(f"✗ 设置页面大小失败: {str(e)}")
            return False
    
    def extract_document_links(self):
        """提取当前页面的文书链接"""
        print("\n正在提取当前页面的文书链接...")
        
        try:
            # 等待页面加载
            self.page.wait_for_load_state('networkidle')
            
            # 查找所有h4标签下的a链接
            h4_links = self.page.query_selector_all('h4 a.caseName')
            
            if not h4_links:
                print("⚠ 未找到caseName类的链接，尝试其他选择器...")
                h4_links = self.page.query_selector_all('h4 a[href*="docId"]')
            
            if not h4_links:
                print("⚠ 未找到docId链接，尝试h4下的所有链接...")
                h4_links = self.page.query_selector_all('h4 a')
            
            if h4_links:
                print(f"✓ 找到 {len(h4_links)} 个文书链接")
                
                links = []
                for i, link in enumerate(h4_links):
                    try:
                        href = link.get_attribute('href')
                        title = link.text_content().strip()
                        
                        if href:
                            # 将../替换为完整URL
                            if href.startswith('../'):
                                full_url = href.replace('../', 'https://wenshu.court.gov.cn/website/wenshu/')
                            else:
                                full_url = href
                            
                            links.append({
                                'url': full_url,
                                'title': title
                            })
                            
                            print(f"  {i+1}. {title[:50]}...")
                            
                    except Exception as e:
                        print(f"  ✗ 提取第{i+1}个链接失败: {str(e)}")
                
                return links
            else:
                print("✗ 未找到文书链接")
                
                # 查找所有可能的链接
                all_links = self.page.query_selector_all('a[href*="docId"]')
                if all_links:
                    print(f"找到 {len(all_links)} 个包含docId的链接")
                else:
                    print("未找到任何包含docId的链接")
                
                return []
                
        except Exception as e:
            print(f"✗ 提取文书链接失败: {str(e)}")
            return []
    
    def click_next_page(self):
        """点击下一页"""
        print("\n正在点击下一页...")
        
        try:
            # 等待页面加载
            self.page.wait_for_load_state('networkidle')
            
            # 查找下一页按钮
            next_button = self.page.query_selector('a.pageButton:has-text("下一页")')
            
            if not next_button:
                print("⚠ 未找到下一页按钮，尝试其他选择器...")
                next_button = self.page.query_selector('a[class*="pageButton"]:has-text("下一页")')
            
            if not next_button:
                # 通过文本查找
                next_button = self.page.query_selector('xpath=//a[contains(text(), "下一页")]')
            
            if next_button:
                # 检查按钮是否可点击（非禁用状态）
                is_disabled = next_button.get_attribute('class')
                if 'disabled' in str(is_disabled).lower():
                    print("⚠ 下一页按钮已禁用，可能已到最后一页")
                    return False
                
                # 滚动到按钮位置
                next_button.scroll_into_view_if_needed()
                
                # 点击下一页
                next_button.click()
                print("✓ 成功点击下一页")
                
                # 等待页面更新
                self.page.wait_for_load_state('networkidle', timeout=15000)
                
                return True
            else:
                print("✗ 未找到下一页按钮")
                
                # 查找所有可能的分页按钮
                page_buttons = self.page.query_selector_all('a[class*="page"], button[class*="page"]')
                if page_buttons:
                    print(f"找到 {len(page_buttons)} 个分页按钮:")
                    for i, btn in enumerate(page_buttons):
                        try:
                            text = btn.text_content()
                            print(f"  {i+1}. {text}")
                        except:
                            pass
                
                return False
                
        except Exception as e:
            print(f"✗ 点击下一页失败: {str(e)}")
            return False
    
    def save_links_to_file(self, all_links, date_str, region="上海市"):
        """保存链接到文件"""
        print(f"\n正在保存链接到文件...")
        
        try:
            # 生成文件名
            filename = f"{date_str}{region}文书.txt"
            
            # 保存链接
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# 裁判文书网 - {region} - {date_str}\n")
                f.write(f"# 总共收集到 {len(all_links)} 个文书链接\n\n")
                
                for i, link in enumerate(all_links):
                    f.write(f"{i+1}. {link['title']}\n")
                    f.write(f"   URL: {link['url']}\n\n")
            
            print(f"✓ 成功保存 {len(all_links)} 个链接到文件: {filename}")
            return filename
            
        except Exception as e:
            print(f"✗ 保存链接到文件失败: {str(e)}")
            return None
    
    def collect_all_documents(self, date_str="2025-07-21", max_pages=10):
        """收集所有文书链接的完整流程"""
        print("=" * 60)
        print(f"开始收集 {date_str} 上海市的文书链接")
        print("=" * 60)
        
        all_links = []
        current_page = 1
        
        try:
            # 第一步：选择上海市
            if not self.select_region_shanghai():
                print("✗ 选择上海市失败，继续执行...")
            
            # 第二步：设置每页15条
            if not self.set_page_size_15():
                print("✗ 设置页面大小失败，继续执行...")
            
            # 第三步：循环收集每页的链接
            while current_page <= max_pages:
                print(f"\n--- 第 {current_page} 页 ---")
                
                # 提取当前页面的链接
                page_links = self.extract_document_links()
                
                if page_links:
                    all_links.extend(page_links)
                    print(f"✓ 第 {current_page} 页收集到 {len(page_links)} 个链接")
                else:
                    print(f"⚠ 第 {current_page} 页未收集到链接")
                
                # 尝试点击下一页
                if not self.click_next_page():
                    print("✗ 无法点击下一页，可能已到最后一页")
                    break
                
                current_page += 1
                
                # 等待一下，避免请求过快
                self.page.wait_for_timeout(2000)
            
            # 第四步：保存所有链接到文件
            if all_links:
                filename = self.save_links_to_file(all_links, date_str)
                
                print("=" * 60)
                print(f"✓ 文书链接收集完成！")
                print(f"✓ 总共收集到 {len(all_links)} 个文书链接")
                print(f"✓ 已保存到文件: {filename}")
                print("=" * 60)
                
                return all_links, filename
            else:
                print("✗ 未收集到任何链接")
                return [], None
                
        except Exception as e:
            print(f"✗ 收集文书链接失败: {str(e)}")
            return all_links, None
    
    def get_page_info(self):
        """获取页面信息"""
        if not self.page:
            print("✗ 页面未初始化")
            return None
        
        print("\n当前页面信息:")
        print("-" * 30)
        print(f"URL: {self.page.url}")
        print(f"标题: {self.page.title()}")
        
        # 获取页面cookies
        cookies = self.page.context.cookies()
        print(f"Cookie数量: {len(cookies)}")
        for cookie in cookies:
            print(f"  {cookie['name']}: {cookie['value'][:50]}{'...' if len(cookie['value']) > 50 else ''}")
        
        return self.page
    
    def close_browser(self):
        """关闭浏览器"""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            print("✓ 浏览器已关闭")
        except Exception as e:
            print(f"⚠ 关闭浏览器时出错: {str(e)}")


def main():
    """主函数"""
    print("=" * 60)
    print("裁判文书网爬取项目 - Playwright浏览器模拟器")
    print("=" * 60)
    
    # 创建浏览器模拟器实例
    simulator = WenshuBrowserSimulator()
    
    try:
        # 测试连接
        success = simulator.test_connection()
        
        if success:
            print("\n✓ Playwright浏览器模拟器设置完成，页面访问正常")
            print("✓ 身份令牌已正确嵌入")
            print("✓ 页面截图已保存")
            
            # 显示页面信息
            simulator.get_page_info()
            
            print("\n✓ 准备就绪，等待下一步指令...")
            
            # 询问是否保持浏览器开启
            print("\n浏览器将保持开启状态，按回车键关闭...")
            input()
            
        else:
            print("\n✗ 页面访问失败，请检查网络连接或身份令牌")
            
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"\n✗ 程序运行出错: {str(e)}")
    finally:
        # 确保浏览器被关闭
        simulator.close_browser()
    
    # 返回模拟器对象供后续使用
    return simulator


if __name__ == "__main__":
    # 运行主程序
    browser_simulator = main() 