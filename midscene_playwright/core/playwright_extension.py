"""
Playwright extension with AI capabilities integration
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from playwright.async_api import Page, Browser, BrowserContext
from .ai_engine import QwenVLEngine
from .page_agent import PageAgent
from .test_planner import TestPlanner
from ..utils.screenshot import ScreenshotTaker

logger = logging.getLogger(__name__)


class MidscenePlaywright:
    """
    AI-enhanced Playwright extension for intelligent automation
    
    This class extends Playwright with AI capabilities including:
    - AI-driven element location
    - Intelligent test planning  
    - Visual analysis and guidance
    - Automated screenshot analysis
    """
    
    def __init__(
        self,
        ai_engine: QwenVLEngine,
        enable_screenshots: bool = True,
        screenshot_on_failure: bool = True,
        debug_mode: bool = False
    ):
        """
        Initialize Midscene Playwright extension
        
        Args:
            ai_engine: QwenVL AI engine instance
            enable_screenshots: Whether to take screenshots automatically
            screenshot_on_failure: Take screenshots when operations fail
            debug_mode: Enable debug logging and enhanced error info
        """
        self.ai_engine = ai_engine
        self.enable_screenshots = enable_screenshots
        self.screenshot_on_failure = screenshot_on_failure
        self.debug_mode = debug_mode
        
        # Initialize components
        self.screenshot_taker = ScreenshotTaker()
        self.test_planner = TestPlanner(ai_engine)
        
        # Track created page agents
        self._page_agents: Dict[str, PageAgent] = {}
        
        if debug_mode:
            logging.basicConfig(level=logging.DEBUG)
            
        logger.info("Initialized MidscenePlaywright extension")
    
    def wrap_page(self, page: Page) -> PageAgent:
        """
        Wrap a Playwright page with AI capabilities
        
        Args:
            page: Playwright page instance
            
        Returns:
            PageAgent with AI-enhanced functionality
        """
        page_id = str(id(page))
        
        if page_id not in self._page_agents:
            agent = PageAgent(
                page=page,
                ai_engine=self.ai_engine,
                screenshot_taker=self.screenshot_taker,
                enable_screenshots=self.enable_screenshots,
                debug_mode=self.debug_mode
            )
            self._page_agents[page_id] = agent
            logger.debug(f"Created new PageAgent for page {page_id}")
        
        return self._page_agents[page_id]
    
    async def create_test_plan(
        self,
        page: Page,
        test_objective: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an AI-generated test plan based on current page
        
        Args:
            page: Playwright page to analyze
            test_objective: What the test should accomplish
            context: Additional context about the test scenario
            
        Returns:
            Dictionary containing the test plan
        """
        try:
            # Take screenshot for analysis
            screenshot = await self.screenshot_taker.take_screenshot(page)
            current_url = page.url
            
            # Generate test plan using AI
            test_plan = await self.test_planner.create_plan(
                screenshot=screenshot,
                objective=test_objective,
                current_url=current_url,
                context=context
            )
            
            logger.info(f"Created test plan with {len(test_plan.get('steps', []))} steps")
            return test_plan
            
        except Exception as e:
            logger.error(f"Error creating test plan: {str(e)}")
            return {
                "test_plan": {
                    "objective": test_objective,
                    "estimated_steps": 0,
                    "complexity": "error",
                    "estimated_time": "unknown"
                },
                "steps": [],
                "prerequisites": [],
                "success_criteria": [],
                "potential_failures": [f"Test planning failed: {str(e)}"],
                "data_requirements": []
            }
    
    async def execute_test_plan(
        self,
        page: Page,
        test_plan: Dict[str, Any],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a test plan on the given page
        
        Args:
            page: Playwright page to run test on
            test_plan: Test plan dictionary from create_test_plan
            dry_run: If True, only validate steps without executing
            
        Returns:
            Dictionary with execution results
        """
        agent = self.wrap_page(page)
        
        results = {
            "test_plan": test_plan.get("test_plan", {}),
            "execution_results": [],
            "overall_success": True,
            "total_steps": len(test_plan.get("steps", [])),
            "completed_steps": 0,
            "failed_steps": 0,
            "execution_time": 0,
            "error_messages": []
        }
        
        steps = test_plan.get("steps", [])
        
        try:
            import time
            start_time = time.time()
            
            for step in steps:
                step_result = await self._execute_test_step(
                    agent=agent,
                    step=step,
                    dry_run=dry_run
                )
                
                results["execution_results"].append(step_result)
                
                if step_result["success"]:
                    results["completed_steps"] += 1
                else:
                    results["failed_steps"] += 1
                    results["overall_success"] = False
                    results["error_messages"].append(step_result.get("error", "Unknown error"))
                    
                    # Stop execution on failure unless it's a verification step
                    if step.get("action") != "verify" and not dry_run:
                        logger.warning(f"Test execution stopped at step {step.get('step_number')} due to failure")
                        break
            
            results["execution_time"] = time.time() - start_time
            
            logger.info(f"Test execution completed: {results['completed_steps']}/{results['total_steps']} steps successful")
            
        except Exception as e:
            logger.error(f"Error during test execution: {str(e)}")
            results["overall_success"] = False
            results["error_messages"].append(f"Execution error: {str(e)}")
        
        return results
    
    async def _execute_test_step(
        self,
        agent: PageAgent,
        step: Dict[str, Any],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a single test step
        
        Args:
            agent: PageAgent to use for execution
            step: Step dictionary from test plan
            dry_run: If True, validate but don't execute
            
        Returns:
            Dictionary with step execution result
        """
        step_result = {
            "step_number": step.get("step_number"),
            "action": step.get("action"),
            "description": step.get("description"),
            "success": False,
            "error": None,
            "execution_time": 0,
            "screenshot_path": None
        }
        
        if dry_run:
            step_result["success"] = True
            step_result["error"] = "Dry run - step not executed"
            return step_result
        
        try:
            import time
            start_time = time.time()
            
            action = step.get("action", "").lower()
            target = step.get("target", "")
            value = step.get("value", "")
            
            if action == "navigate":
                await agent.ai_navigate(target)
                
            elif action == "click":
                await agent.ai_click(target)
                
            elif action == "type":
                await agent.ai_type(target, value)
                
            elif action == "wait":
                if target.isdigit():
                    await asyncio.sleep(int(target))
                else:
                    await agent.ai_wait_for_element(target, timeout=30000)
                    
            elif action == "scroll":
                await agent.ai_scroll(target)
                
            elif action == "verify":
                verification_result = await agent.ai_verify(target)
                if not verification_result.get("success", False):
                    step_result["error"] = f"Verification failed: {verification_result.get('message', 'Unknown')}"
                    return step_result
                    
            else:
                step_result["error"] = f"Unknown action: {action}"
                return step_result
            
            step_result["success"] = True
            step_result["execution_time"] = time.time() - start_time
            
        except Exception as e:
            step_result["error"] = str(e)
            step_result["execution_time"] = time.time() - start_time if 'start_time' in locals() else 0
            
            # Take screenshot on failure if enabled
            if self.screenshot_on_failure:
                try:
                    screenshot_path = await self.screenshot_taker.take_screenshot(
                        agent.page, 
                        filename=f"failure_step_{step.get('step_number', 'unknown')}.png"
                    )
                    step_result["screenshot_path"] = screenshot_path
                except:
                    pass
        
        return step_result
    
    async def analyze_page(
        self,
        page: Page,
        task_description: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze current page state and provide AI insights
        
        Args:
            page: Playwright page to analyze
            task_description: Description of what you want to accomplish
            context: Additional context for analysis
            
        Returns:
            Dictionary with analysis results
        """
        try:
            screenshot = await self.screenshot_taker.take_screenshot(page)
            
            analysis = self.ai_engine.analyze_screenshot(
                screenshot=screenshot,
                task_description=task_description,
                context=context
            )
            
            # Add page metadata
            analysis["page_metadata"] = {
                "url": page.url,
                "title": await page.title(),
                "viewport": page.viewport_size
            }
            
            logger.info("Completed page analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing page: {str(e)}")
            return {
                "analysis": f"Error during analysis: {str(e)}",
                "elements": [],
                "recommended_actions": [],
                "risks": ["Analysis failed"],
                "success_indicators": [],
                "page_metadata": {"url": page.url if page else "unknown"}
            }
    
    def cleanup(self):
        """Clean up resources and cached agents"""
        self._page_agents.clear()
        logger.info("Cleaned up MidscenePlaywright resources")