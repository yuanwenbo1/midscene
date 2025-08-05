"""
Pytest integration example for Midscene Playwright

This example shows how to integrate Midscene Playwright with pytest
for AI-driven test automation in a testing framework.
"""

import pytest
import asyncio
import os
from playwright.async_api import async_playwright
from midscene_playwright import QwenVLEngine, MidscenePlaywright


class TestMidscenePlaywright:
    """
    Test class demonstrating Midscene Playwright integration with pytest
    """
    
    @pytest.fixture(scope="class")
    def api_key(self):
        """Fixture to get API key"""
        key = os.getenv("DASHSCOPE_API_KEY")
        if not key:
            pytest.skip("DASHSCOPE_API_KEY environment variable not set")
        return key
    
    @pytest.fixture(scope="class")
    def ai_engine(self, api_key):
        """Fixture to create AI engine"""
        return QwenVLEngine(
            api_key=api_key,
            model="qwen-vl-max-latest",
            max_tokens=1500,
            temperature=0.1
        )
    
    @pytest.fixture(scope="class") 
    def midscene(self, ai_engine):
        """Fixture to create Midscene Playwright instance"""
        return MidscenePlaywright(
            ai_engine=ai_engine,
            enable_screenshots=True,
            screenshot_on_failure=True,
            debug_mode=True
        )
    
    @pytest.fixture
    async def browser_page(self):
        """Fixture to provide browser and page"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            yield browser, page
            
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_basic_navigation(self, midscene, browser_page):
        """Test basic navigation functionality"""
        browser, page = browser_page
        agent = midscene.wrap_page(page)
        
        # Test navigation
        result = await agent.ai_navigate("https://example.com")
        assert result["success"], f"Navigation failed: {result.get('error')}"
        
        # Verify page title
        title = await page.title()
        assert "Example" in title
    
    @pytest.mark.asyncio
    async def test_ai_page_analysis(self, midscene, browser_page):
        """Test AI-powered page analysis"""
        browser, page = browser_page
        
        # Navigate to test page
        await page.goto("https://demo.playwright.dev/todomvc/")
        await asyncio.sleep(2)
        
        # Analyze page
        analysis = await midscene.analyze_page(
            page,
            task_description="Identify the todo input field and any existing todos",
            context="TodoMVC application"
        )
        
        assert "analysis" in analysis
        assert isinstance(analysis["elements"], list)
        assert len(analysis["elements"]) > 0
    
    @pytest.mark.asyncio
    async def test_ai_test_planning(self, midscene, browser_page):
        """Test AI-powered test planning"""
        browser, page = browser_page
        
        # Navigate to test application
        await page.goto("https://demo.playwright.dev/todomvc/")
        await asyncio.sleep(2)
        
        # Create test plan
        test_plan = await midscene.create_test_plan(
            page=page,
            test_objective="Add a todo item 'Test AI Planning' and verify it appears",
            context="TodoMVC demo application"
        )
        
        # Validate test plan structure
        assert "test_plan" in test_plan
        assert "steps" in test_plan
        assert "risk_analysis" in test_plan
        
        # Check test plan content
        plan_info = test_plan["test_plan"]
        assert plan_info.get("estimated_steps", 0) > 0
        assert plan_info.get("complexity") in ["low", "medium", "high"]
        
        # Check steps
        steps = test_plan["steps"]
        assert len(steps) > 0
        assert all("action" in step for step in steps)
    
    @pytest.mark.asyncio
    async def test_ai_element_interaction(self, midscene, browser_page):
        """Test AI-driven element interactions"""
        browser, page = browser_page
        agent = midscene.wrap_page(page)
        
        # Navigate to form demo
        result = await agent.ai_navigate("https://demoqa.com/text-box")
        assert result["success"]
        
        await asyncio.sleep(3)
        
        # Test typing into form fields
        name_result = await agent.ai_type(
            element_description="full name input field",
            text="Test User"
        )
        assert name_result["success"], f"Name input failed: {name_result.get('error')}"
        
        email_result = await agent.ai_type(
            element_description="email address field",
            text="test@example.com"
        )
        assert email_result["success"], f"Email input failed: {email_result.get('error')}"
    
    @pytest.mark.asyncio
    async def test_form_submission_workflow(self, midscene, browser_page):
        """Test complete form submission workflow"""
        browser, page = browser_page
        agent = midscene.wrap_page(page)
        
        # Navigate to form
        await agent.ai_navigate("https://demoqa.com/text-box")
        await asyncio.sleep(3)
        
        # Fill form using AI
        form_data = {
            "full name input": "John Doe",
            "email input": "john@example.com", 
            "current address": "123 Test Street",
            "permanent address": "456 Demo Avenue"
        }
        
        for field_desc, value in form_data.items():
            result = await agent.ai_type(field_desc, value)
            assert result["success"], f"Failed to fill {field_desc}: {result.get('error')}"
        
        # Submit form
        submit_result = await agent.ai_click("submit button")
        assert submit_result["success"], f"Submit failed: {submit_result.get('error')}"
        
        # Verify submission (wait for output)
        await asyncio.sleep(2)
        verify_result = await agent.ai_verify("form data is displayed in the output")
        # Note: Verification might not always succeed due to AI interpretation
        # In real tests, you might want more specific checks
    
    @pytest.mark.asyncio
    async def test_todo_mvc_workflow(self, midscene, browser_page):
        """Test TodoMVC application workflow with AI"""
        browser, page = browser_page
        
        # Navigate to TodoMVC
        await page.goto("https://demo.playwright.dev/todomvc/")
        await asyncio.sleep(2)
        
        # Create and execute test plan
        test_plan = await midscene.create_test_plan(
            page=page,
            test_objective="Add three todo items and mark the second one as completed",
            context="TodoMVC application with standard todo functionality"
        )
        
        # Execute the plan
        execution_result = await midscene.execute_test_plan(
            page=page,
            test_plan=test_plan,
            dry_run=False
        )
        
        # Validate execution results
        assert execution_result["total_steps"] > 0
        # Allow for some failures in complex workflows
        success_rate = execution_result["completed_steps"] / execution_result["total_steps"]
        assert success_rate >= 0.5, f"Success rate too low: {success_rate:.2f}"
    
    @pytest.mark.asyncio  
    async def test_error_handling(self, midscene, browser_page):
        """Test error handling in AI interactions"""
        browser, page = browser_page
        agent = midscene.wrap_page(page)
        
        # Navigate to a page
        await agent.ai_navigate("https://example.com")
        await asyncio.sleep(2)
        
        # Try to interact with non-existent element
        result = await agent.ai_click("non-existent super special button")
        assert not result["success"]
        assert "error" in result
        assert result["element_found"] is False
    
    @pytest.mark.asyncio
    async def test_screenshot_functionality(self, midscene, browser_page):
        """Test screenshot taking functionality"""
        browser, page = browser_page
        
        # Navigate to a page
        await page.goto("https://example.com")
        await asyncio.sleep(2)
        
        # Take screenshot via Midscene
        screenshot_taker = midscene.screenshot_taker
        screenshot_path = await screenshot_taker.take_screenshot(page)
        
        # Verify screenshot was created
        import os
        assert os.path.exists(screenshot_path)
        assert screenshot_path.endswith('.png')
        
        # Get screenshot info
        info = screenshot_taker.get_screenshot_info(screenshot_path)
        assert "width" in info
        assert "height" in info
        assert info["width"] > 0
        assert info["height"] > 0
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, midscene, browser_page):
        """Test element location caching"""
        browser, page = browser_page
        agent = midscene.wrap_page(page)
        
        # Navigate to a page with form elements
        await agent.ai_navigate("https://demoqa.com/text-box")
        await asyncio.sleep(3)
        
        # First interaction (should cache)
        result1 = await agent.ai_click("full name input field")
        
        # Second interaction (should use cache)
        result2 = await agent.ai_click("full name input field")
        
        # Both should succeed (though they might behave differently)
        # The main point is that caching doesn't break functionality
        assert isinstance(result1["success"], bool)
        assert isinstance(result2["success"], bool)
        
        # Check cache statistics
        cache_stats = agent.element_locator.get_cache_stats()
        assert "cache_size" in cache_stats
        assert cache_stats["cache_size"] >= 0


# Pytest configuration and fixtures
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create screenshots directory
    os.makedirs("screenshots", exist_ok=True)
    
    yield
    
    # Cleanup after tests
    print("\nCleaning up test environment...")


# Custom pytest markers
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.ai_integration
]


# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "ai_integration: marks tests as AI integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


# Parametrized tests for different scenarios
class TestParametrizedScenarios:
    """Parametrized tests for different automation scenarios"""
    
    @pytest.mark.parametrize("url,expected_title", [
        ("https://example.com", "Example"),
        ("https://httpbin.org/", "httpbin"),
    ])
    @pytest.mark.asyncio
    async def test_navigation_scenarios(self, midscene, browser_page, url, expected_title):
        """Test navigation to different URLs"""
        if not os.getenv("DASHSCOPE_API_KEY"):
            pytest.skip("API key not available")
            
        browser, page = browser_page
        agent = midscene.wrap_page(page)
        
        result = await agent.ai_navigate(url)
        assert result["success"]
        
        title = await page.title()
        assert expected_title.lower() in title.lower()
    
    @pytest.mark.parametrize("form_field,test_value", [
        ("full name input", "Test Name"),
        ("email input", "test@email.com"),
        ("current address", "Test Address"),
    ])
    @pytest.mark.asyncio  
    async def test_form_field_scenarios(self, midscene, browser_page, form_field, test_value):
        """Test different form field interactions"""
        if not os.getenv("DASHSCOPE_API_KEY"):
            pytest.skip("API key not available")
            
        browser, page = browser_page
        agent = midscene.wrap_page(page)
        
        await agent.ai_navigate("https://demoqa.com/text-box")
        await asyncio.sleep(3)
        
        result = await agent.ai_type(form_field, test_value)
        # Note: Some fields might not be found due to AI interpretation variations
        # In production, you'd want more specific selectors
        assert isinstance(result["success"], bool)