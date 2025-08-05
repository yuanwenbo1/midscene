# Midscene Playwright

> 🤖 AI-powered Playwright extension for intelligent web automation and testing

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Playwright](https://img.shields.io/badge/playwright-1.40%2B-orange.svg)](https://playwright.dev/)

**Midscene Playwright** 是一个基于 Python 的 AI 驱动的 Playwright 扩展插件，它将强大的视觉语言模型（千问VL）与 Playwright 的稳定性相结合，让您能够使用自然语言描述来编写和执行自动化测试。

## ✨ 特性

### 🧠 AI 驱动的自动化
- **自然语言交互**：使用人类语言描述元素和操作，无需编写复杂的选择器
- **智能元素定位**：AI 视觉分析结合 DOM 检查，提供可靠的元素定位
- **自动测试规划**：基于页面截图自动生成测试步骤和执行策略

### 🎯 智能测试规划
- **AI 测试生成**：根据测试目标自动生成详细的测试计划
- **风险评估**：智能识别潜在失败点并提供缓解策略
- **执行策略优化**：根据复杂度自动调整重试策略和超时配置

### 🛡️ 稳定性增强
- **多重定位策略**：AI 建议 + 智能选择器生成 + DOM 验证
- **自动错误恢复**：智能重试机制和失败恢复策略
- **截图调试**：自动截图记录，便于问题诊断

### 🔧 易于集成
- **Playwright 兼容**：完全兼容现有 Playwright 代码
- **pytest 集成**：开箱即用的 pytest 支持
- **灵活配置**：支持多种 AI 模型和自定义配置

## 🚀 快速开始

### 安装

```bash
# 安装核心依赖
pip install midscene-playwright

# 安装 Playwright 浏览器
playwright install chromium
```

### 配置 API Key

```bash
# 设置千问 VL 模型的 API Key
export DASHSCOPE_API_KEY="your-dashscope-api-key"
```

### 基础使用

```python
import asyncio
from playwright.async_api import async_playwright
from midscene_playwright import QwenVLEngine, MidscenePlaywright

async def main():
    # 初始化 AI 引擎
    ai_engine = QwenVLEngine(
        api_key="your-dashscope-api-key",
        model="qwen-vl-max-latest"
    )
    
    # 创建 Midscene Playwright 实例
    midscene = MidscenePlaywright(
        ai_engine=ai_engine,
        enable_screenshots=True,
        debug_mode=True
    )
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 使用 AI 增强的页面代理
        agent = midscene.wrap_page(page)
        
        # 自然语言导航
        await agent.ai_navigate("https://example.com")
        
        # 智能元素交互
        await agent.ai_click("登录按钮")
        await agent.ai_type("用户名输入框", "admin")
        await agent.ai_type("密码输入框", "password123")
        await agent.ai_click("提交按钮")
        
        # AI 验证
        result = await agent.ai_verify("登录成功")
        print(f"登录验证: {'成功' if result['success'] else '失败'}")
        
        await browser.close()

asyncio.run(main())
```

## 📖 详细功能

### 1. AI 驱动的元素定位

使用自然语言描述即可定位页面元素：

```python
# 传统方式
element = page.locator("#username")

# Midscene 方式
result = await agent.ai_click("用户名输入框")
```

### 2. 智能测试规划

自动生成测试计划：

```python
# 创建测试计划
test_plan = await midscene.create_test_plan(
    page=page,
    test_objective="完成用户注册流程",
    context="电商网站注册页面"
)

# 执行测试计划
execution_result = await midscene.execute_test_plan(
    page=page,
    test_plan=test_plan
)

print(f"测试执行结果: {execution_result['overall_success']}")
print(f"完成步骤: {execution_result['completed_steps']}/{execution_result['total_steps']}")
```

### 3. 页面分析

获取 AI 驱动的页面洞察：

```python
analysis = await midscene.analyze_page(
    page,
    task_description="分析购物车页面的可用操作",
    context="电商购物车页面"
)

print("发现的元素:")
for element in analysis['elements']:
    print(f"- {element['type']}: {element['description']}")

print("推荐操作:")
for action in analysis['recommended_actions']:
    print(f"- {action['action']}: {action['reasoning']}")
```

### 4. Pytest 集成

```python
import pytest
from midscene_playwright import QwenVLEngine, MidscenePlaywright

class TestWebApp:
    @pytest.fixture
    def midscene(self):
        ai_engine = QwenVLEngine(api_key="your-api-key")
        return MidscenePlaywright(ai_engine=ai_engine)
    
    @pytest.mark.asyncio
    async def test_login_flow(self, midscene, page):
        agent = midscene.wrap_page(page)
        
        await agent.ai_navigate("https://app.example.com/login")
        await agent.ai_type("邮箱输入框", "test@example.com")
        await agent.ai_type("密码输入框", "password123")
        await agent.ai_click("登录按钮")
        
        result = await agent.ai_verify("登录成功")
        assert result['success']
```

## 🏗️ 架构设计

```
midscene_playwright/
├── core/                   # 核心组件
│   ├── ai_engine.py       # AI 引擎 (千问VL集成)
│   ├── playwright_extension.py  # Playwright 扩展
│   ├── page_agent.py      # 页面代理
│   └── test_planner.py    # 测试规划器
├── utils/                 # 工具模块
│   ├── screenshot.py      # 截图工具
│   └── element_locator.py # 元素定位器
└── examples/              # 使用示例
    ├── basic_usage.py     # 基础使用
    └── pytest_integration.py  # pytest 集成
```

## ⚙️ 配置选项

### AI 引擎配置

```python
ai_engine = QwenVLEngine(
    api_key="your-api-key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-vl-max-latest",  # 或 "qwen-vl-plus"
    max_tokens=2000,
    temperature=0.1  # 较低的温度确保一致性
)
```

### Midscene 配置

```python
midscene = MidscenePlaywright(
    ai_engine=ai_engine,
    enable_screenshots=True,      # 启用自动截图
    screenshot_on_failure=True,   # 失败时截图
    debug_mode=True              # 调试模式
)
```

## 🔍 高级特性

### 1. 自定义选择器策略

```python
# 配置元素定位器
locator = AIElementLocator(ai_engine, screenshot_taker)

# 自定义定位逻辑
result = await locator.locate_element(
    page=page,
    element_description="红色的提交按钮",
    context="表单底部区域"
)
```

### 2. 批量操作

```python
# 批量填写表单
form_data = {
    "姓名输入框": "张三",
    "邮箱输入框": "zhangsan@example.com",
    "手机号输入框": "13800138000"
}

for field, value in form_data.items():
    await agent.ai_type(field, value)
```

### 3. 条件等待

```python
# 等待元素出现
await agent.ai_wait_for_element("加载完成提示", timeout=30000)

# 等待页面状态
await agent.ai_verify("页面加载完成")
```

## 📊 性能优化

### 缓存机制

```python
# 元素定位缓存
cache_stats = agent.element_locator.get_cache_stats()
print(f"缓存命中率: {cache_stats['cache_size']}")

# 清理缓存
agent.element_locator.clear_cache()
```

### 并行执行

```python
# 并行验证多个元素
tasks = [
    agent.ai_verify("用户名已填写"),
    agent.ai_verify("密码已填写"),
    agent.ai_verify("验证码已填写")
]

results = await asyncio.gather(*tasks)
```

## 🐛 调试和故障排除

### 启用调试模式

```python
midscene = MidscenePlaywright(
    ai_engine=ai_engine,
    debug_mode=True  # 启用详细日志
)
```

### 截图调试

```python
# 手动截图
screenshot_path = await midscene.screenshot_taker.take_screenshot(page)
print(f"截图保存到: {screenshot_path}")

# 获取截图信息
info = midscene.screenshot_taker.get_screenshot_info(screenshot_path)
print(f"截图尺寸: {info['width']}x{info['height']}")
```

### 查看元素定位详情

```python
result = await agent.ai_click("提交按钮")
if not result['success']:
    print(f"定位失败原因: {result['error']}")
    print(f"尝试次数: {result['attempts']}")
    print(f"元素是否找到: {result['element_found']}")
```

## 🧪 测试

运行测试套件：

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_basic_functionality.py

# 运行 AI 集成测试 (需要 API key)
DASHSCOPE_API_KEY="your-key" pytest -m ai_integration
```

## 🤝 贡献

我们欢迎各种形式的贡献！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Playwright](https://playwright.dev/) - 优秀的浏览器自动化框架
- [千问VL](https://help.aliyun.com/zh/dashscope/developer-reference/vl-plus-quick-start) - 强大的视觉语言模型
- [Midscene.js](https://github.com/web-infra-dev/midscene) - 原始灵感来源

## 📞 支持

- 📖 [文档](https://midscene-playwright.readthedocs.io/)
- 🐛 [问题反馈](https://github.com/midscene-ai/midscene-playwright/issues)
- 💬 [讨论区](https://github.com/midscene-ai/midscene-playwright/discussions)

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！
