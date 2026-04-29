# -*- coding: utf-8 -*-
import random
from screeninfo import get_monitors
from playwright.sync_api import sync_playwright, TimeoutError
from Common.Deal import get_config_value

class Playwright(object):
    """playwright登录实例"""
    def __init__(self):
        # 初始化playwright相关对象
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        self.browser_type = 'msedge'  # 浏览器类型
        self.user_agent = get_config_value('login', 'user-agent')
        self.width = get_monitors()[0].width  # 当前屏幕分辨率width
        self.height = get_monitors()[0].height  # 当前屏幕分辨率height
        self.timeout = 10 * 1000  # 超时时间

    def start_borwser(self):
        """打开浏览器"""
        self.playwright = sync_playwright().start()
        browser_args = [
            # 禁用自动化检测（核心）
            '--disable-blink-features=AutomationControlled',
            # 禁用扩展/插件
            '--disable-extensions',
            '--disable-plugins',
            # 禁用GPU/WebGL指纹
            '--disable-gpu',
            '--disable-webgl',
            '--disable-webgl-image-chromium',
            # 禁用隐私模式提示
            '--no-pings',
            # 禁用弹窗拦截（模拟真实用户）
            '--disable-popup-blocking',
            # 禁用默认浏览器检查
            '--no-default-browser-check',
            # 禁用首次运行提示
            '--no-first-run',
            # 随机窗口尺寸（避免固定值）
            '--start-maximized'
            # '--window-size={},{}'.format(
            #     self.width + random.randint(-20, 20),
            #     self.height + random.randint(-20, 20)
            # ),
            # 模拟真实语言/地区
            '--lang=zh-CN,zh',
            # 禁用日志（减少特征）
            '--log-level=3',
            '--disable-logging',
            # 禁用密码保存提示
            '--disable-save-password-bubble',
            # 禁用自动填充
            '--disable-autofill',
        ]

        # 2. 启动浏览器（隐藏自动化标识）
        self.browser = self.playwright.chromium.launch(
            channel=self.browser_type,
            headless=False,
            args=browser_args,
            # 移除Playwright默认的自动化参数
            ignore_default_args=["--enable-automation"],
            # 随机放慢操作（模拟人类速度）
            slow_mo=random.randint(100, 300),
            # 禁用自动化相关日志
            env={"GOOGLE_CHROME_BIN": ""}
        )
        # 创建上下文
        self.context = self.browser.new_context(
            # viewport=ViewportSize(width=self.width, height=self.height),
            user_agent=self.user_agent)
        # 创建页面
        self.page = self.context.new_page()
        js_code = """
        () => {
            // 唯一需要的核心操作：覆盖 getter
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true, // 确保可以被重新定义（虽然通常不需要再次定义）
                enumerable: false
            });

            // 其他伪装逻辑... (plugins, chrome object 等)
        }
        """
        self.page.add_init_script(js_code)

    def close(self):
        """关闭浏览器"""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def goto(self, url):
        if not self.playwright:
            self.start_borwser()
        for i in range(3):
            try:
                self.page.goto(url, timeout=self.timeout)
                return True
            except Exception as e:
                print('%s地址访问失败：%s' % (url, e))
                continue
        return False

    def click(self, location):
        self.page.click(location, timeout=self.timeout)

    def input(self, location, text):
        self.page.fill(location, text)

    def wait_for_selector(self, location, state='visible', timeout=5*1000):
        try:
            self.page.wait_for_selector(f'xpath={location}', state=state, timeout=timeout)
            return True
        except TimeoutError:
            return False

    def reload(self):
        self.page.reload()

    def add_cookie(self, cookie):
        if not self.playwright:
            self.start_borwser()
        if self.context.cookies() != cookie:
            self.context.add_cookies(cookie)

Playwright_ = Playwright()