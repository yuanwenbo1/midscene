"""
Basic usage example for Midscene Playwright

This example demonstrates how to use the AI-enhanced Playwright extension
for automated testing with natural language descriptions.
"""

import asyncio
import os
import logging
from playwright.async_api import async_playwright
from midscene_playwright import QwenVLEngine, MidscenePlaywright

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_automation_example():
    """
    Basic example showing AI-driven browser automation
    """
    # Initialize AI engine with Qwen VL model
    # You need to set your DashScope API key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error("Please set DASHSCOPE_API_KEY environment variable")
        return
    
    ai_engine = QwenVLEngine(
        api_key=api_key,
        model="qwen-vl-max-latest",
        max_tokens=2000
    )
    
    # Initialize Midscene Playwright extension
    midscene = MidscenePlaywright(
        ai_engine=ai_engine,
        enable_screenshots=True,
        debug_mode=True
    )
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Wrap page with AI capabilities
            agent = midscene.wrap_page(page)
            
            logger.info("Starting basic automation example...")
            
            # Navigate to a test website
            result = await agent.ai_navigate("https://example.com")
            logger.info(f"Navigation result: {result['success']}")
            
            # Wait a moment for page to load
            await asyncio.sleep(2)
            
            # Analyze the page using AI
            analysis = await midscene.analyze_page(
                page,
                task_description="Find all clickable elements on this page",
                context="This is a simple example website"
            )
            
            logger.info("Page analysis results:")
            logger.info(f"Found {len(analysis.get('elements', []))} elements")
            for element in analysis.get('elements', [])[:3]:  # Show first 3
                logger.info(f"- {element.get('type')}: {element.get('description')}")
            
            # Example of AI-driven interaction
            if analysis.get('elements'):
                logger.info("Demonstrating AI click...")
                click_result = await agent.ai_click("any link on the page")
                logger.info(f"Click result: {click_result['success']}")
                
                if not click_result['success']:
                    logger.info(f"Click failed: {click_result['error']}")
            
            logger.info("Basic automation example completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during automation: {str(e)}")
        
        finally:
            await browser.close()
            midscene.cleanup()


async def test_planning_example():
    """
    Example showing AI-powered test planning capabilities
    """
    # Initialize components
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error("Please set DASHSCOPE_API_KEY environment variable")
        return
    
    ai_engine = QwenVLEngine(api_key=api_key)
    midscene = MidscenePlaywright(ai_engine=ai_engine, debug_mode=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            logger.info("Starting test planning example...")
            
            # Navigate to a demo application
            await page.goto("https://demo.playwright.dev/todomvc/")
            await asyncio.sleep(3)
            
            # Create an AI-generated test plan
            test_plan = await midscene.create_test_plan(
                page=page,
                test_objective="Add a new todo item and mark it as completed",
                context="This is a TodoMVC application demo"
            )
            
            logger.info("Generated test plan:")
            plan_info = test_plan.get("test_plan", {})
            logger.info(f"- Objective: {plan_info.get('objective')}")
            logger.info(f"- Estimated steps: {plan_info.get('estimated_steps')}")
            logger.info(f"- Complexity: {plan_info.get('complexity')}")
            logger.info(f"- Risk level: {test_plan.get('risk_analysis', {}).get('overall_risk_level')}")
            
            logger.info("\nTest steps:")
            for i, step in enumerate(test_plan.get("steps", [])[:5]):  # Show first 5 steps
                logger.info(f"{i+1}. {step.get('action')}: {step.get('description')}")
            
            # Execute the test plan
            logger.info("\nExecuting test plan...")
            execution_result = await midscene.execute_test_plan(
                page=page,
                test_plan=test_plan,
                dry_run=False  # Set to True to just validate without executing
            )
            
            logger.info("Execution results:")
            logger.info(f"- Overall success: {execution_result['overall_success']}")
            logger.info(f"- Completed steps: {execution_result['completed_steps']}/{execution_result['total_steps']}")
            logger.info(f"- Execution time: {execution_result['execution_time']:.2f} seconds")
            
            if execution_result['error_messages']:
                logger.info("Errors encountered:")
                for error in execution_result['error_messages']:
                    logger.info(f"- {error}")
            
            logger.info("Test planning example completed!")
            
        except Exception as e:
            logger.error(f"Error during test planning: {str(e)}")
        
        finally:
            await browser.close()
            midscene.cleanup()


async def advanced_interaction_example():
    """
    Example showing advanced AI interactions
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error("Please set DASHSCOPE_API_KEY environment variable")
        return
    
    ai_engine = QwenVLEngine(api_key=api_key)
    midscene = MidscenePlaywright(ai_engine=ai_engine, debug_mode=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            logger.info("Starting advanced interaction example...")
            
            # Navigate to a form demo
            await page.goto("https://demoqa.com/text-box")
            await asyncio.sleep(3)
            
            # Get page agent
            agent = midscene.wrap_page(page)
            
            # Example 1: AI form filling
            logger.info("Filling form using AI...")
            
            # Fill full name
            name_result = await agent.ai_type(
                element_description="full name input field",
                text="John Doe"
            )
            logger.info(f"Name input: {name_result['success']}")
            
            # Fill email
            email_result = await agent.ai_type(
                element_description="email input field", 
                text="john.doe@example.com"
            )
            logger.info(f"Email input: {email_result['success']}")
            
            # Fill current address
            address_result = await agent.ai_type(
                element_description="current address text area",
                text="123 Main Street, Anytown, USA"
            )
            logger.info(f"Address input: {address_result['success']}")
            
            # Submit form
            submit_result = await agent.ai_click("submit button")
            logger.info(f"Form submission: {submit_result['success']}")
            
            # Wait for results and verify
            await asyncio.sleep(2)
            verify_result = await agent.ai_verify("form submission was successful")
            logger.info(f"Verification: {verify_result['success']}")
            
            logger.info("Advanced interaction example completed!")
            
        except Exception as e:
            logger.error(f"Error during advanced interaction: {str(e)}")
        
        finally:
            await browser.close()
            midscene.cleanup()


async def main():
    """
    Main function to run all examples
    """
    print("Midscene Playwright Examples")
    print("=" * 50)
    
    # Check if API key is set
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("\n❌ Error: DASHSCOPE_API_KEY environment variable not set")
        print("Please set your DashScope API key:")
        print("export DASHSCOPE_API_KEY='your-api-key-here'")
        return
    
    examples = [
        ("Basic Usage", basic_automation_example),
        ("Test Planning", test_planning_example), 
        ("Advanced Interactions", advanced_interaction_example)
    ]
    
    for name, example_func in examples:
        print(f"\n🚀 Running {name} Example...")
        print("-" * 30)
        
        try:
            await example_func()
            print(f"✅ {name} example completed successfully!")
        except Exception as e:
            print(f"❌ {name} example failed: {str(e)}")
        
        print("\nPress Enter to continue to next example...")
        input()
    
    print("\n🎉 All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())