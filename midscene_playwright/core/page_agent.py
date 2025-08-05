"""
Page Agent for AI-enhanced Playwright page operations
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError
from .ai_engine import QwenVLEngine
from ..utils.screenshot import ScreenshotTaker
from ..utils.element_locator import AIElementLocator

logger = logging.getLogger(__name__)


class PageAgent:
    """
    AI-enhanced page agent that provides intelligent automation capabilities
    
    This class wraps a Playwright page and adds AI-driven functionality:
    - AI-based element location and interaction
    - Smart waiting and error recovery
    - Visual verification of actions
    - Context-aware decision making
    """
    
    def __init__(
        self,
        page: Page,
        ai_engine: QwenVLEngine,
        screenshot_taker: ScreenshotTaker,
        enable_screenshots: bool = True,
        debug_mode: bool = False
    ):
        """
        Initialize PageAgent
        
        Args:
            page: Playwright page instance
            ai_engine: AI engine for intelligent operations
            screenshot_taker: Screenshot utility
            enable_screenshots: Whether to take screenshots
            debug_mode: Enable debug logging
        """
        self.page = page
        self.ai_engine = ai_engine
        self.screenshot_taker = screenshot_taker
        self.enable_screenshots = enable_screenshots
        self.debug_mode = debug_mode
        
        # Initialize element locator
        self.element_locator = AIElementLocator(ai_engine, screenshot_taker)
        
        # Track recent actions for context
        self._action_history: List[Dict[str, Any]] = []
        self._max_history = 10
        
        logger.debug(f"Initialized PageAgent for page: {page.url}")
    
    async def ai_click(
        self,
        element_description: str,
        timeout: int = 30000,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        Click an element using AI-powered location
        
        Args:
            element_description: Human description of element to click
            timeout: Maximum wait time in milliseconds
            retry_count: Number of retry attempts
            
        Returns:
            Dictionary with operation result
        """
        result = {
            "success": False,
            "action": "click",
            "target": element_description,
            "error": None,
            "attempts": 0,
            "element_found": False,
            "screenshot_path": None
        }
        
        for attempt in range(retry_count):
            result["attempts"] = attempt + 1
            
            try:
                # Take screenshot for analysis
                screenshot = None
                if self.enable_screenshots:
                    screenshot = await self.screenshot_taker.take_screenshot(self.page)
                    
                # Locate element using AI
                location_result = await self.element_locator.locate_element(
                    page=self.page,
                    element_description=element_description,
                    screenshot=screenshot,
                    context=self._get_recent_context()
                )
                
                if not location_result.get("found", False):
                    result["error"] = f"Element not found: {element_description}"
                    if attempt < retry_count - 1:
                        await asyncio.sleep(1)  # Wait before retry
                        continue
                    break
                
                result["element_found"] = True
                
                # Try to click using suggested selectors
                element_info = location_result.get("element", {})
                selectors = element_info.get("selector_suggestions", [])
                
                clicked = False
                for selector in selectors:
                    try:
                        # Try to find and click element
                        locator = self.page.locator(selector).first
                        await locator.wait_for(state="visible", timeout=timeout)
                        await locator.click(timeout=timeout)
                        clicked = True
                        break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {str(e)}")
                        continue
                
                if not clicked:
                    # Fallback: try to click using coordinates if available
                    coordinates = location_result.get("coordinates", {})
                    if coordinates and "approximate_x" in coordinates and "approximate_y" in coordinates:
                        await self.page.click(
                            position={
                                "x": coordinates["approximate_x"],
                                "y": coordinates["approximate_y"]
                            },
                            timeout=timeout
                        )
                        clicked = True
                
                if clicked:
                    result["success"] = True
                    self._record_action("click", element_description, True)
                    logger.info(f"Successfully clicked: {element_description}")
                    break
                else:
                    result["error"] = "Could not click element with any available method"
                    
            except PlaywrightTimeoutError:
                result["error"] = f"Timeout waiting for element: {element_description}"
            except Exception as e:
                result["error"] = f"Error clicking element: {str(e)}"
                
            if attempt < retry_count - 1:
                logger.warning(f"Click attempt {attempt + 1} failed, retrying: {result['error']}")
                await asyncio.sleep(1)
        
        if not result["success"]:
            self._record_action("click", element_description, False, result["error"])
            
            # Take failure screenshot
            if self.enable_screenshots:
                try:
                    screenshot_path = await self.screenshot_taker.take_screenshot(
                        self.page,
                        filename=f"failed_click_{element_description.replace(' ', '_')}.png"
                    )
                    result["screenshot_path"] = screenshot_path
                except:
                    pass
        
        return result
    
    async def ai_type(
        self,
        element_description: str,
        text: str,
        timeout: int = 30000,
        clear_first: bool = True
    ) -> Dict[str, Any]:
        """
        Type text into an element using AI-powered location
        
        Args:
            element_description: Description of input element
            text: Text to type
            timeout: Maximum wait time
            clear_first: Whether to clear existing text first
            
        Returns:
            Dictionary with operation result
        """
        result = {
            "success": False,
            "action": "type",
            "target": element_description,
            "value": text,
            "error": None,
            "element_found": False
        }
        
        try:
            # Take screenshot for analysis
            screenshot = None
            if self.enable_screenshots:
                screenshot = await self.screenshot_taker.take_screenshot(self.page)
            
            # Locate input element
            location_result = await self.element_locator.locate_element(
                page=self.page,
                element_description=element_description,
                screenshot=screenshot,
                context=self._get_recent_context()
            )
            
            if not location_result.get("found", False):
                result["error"] = f"Input element not found: {element_description}"
                return result
                
            result["element_found"] = True
            
            # Try to type using suggested selectors
            element_info = location_result.get("element", {})
            selectors = element_info.get("selector_suggestions", [])
            
            typed = False
            for selector in selectors:
                try:
                    locator = self.page.locator(selector).first
                    await locator.wait_for(state="visible", timeout=timeout)
                    
                    if clear_first:
                        await locator.clear(timeout=timeout)
                    
                    await locator.type(text, timeout=timeout)
                    typed = True
                    break
                except Exception as e:
                    logger.debug(f"Typing with selector {selector} failed: {str(e)}")
                    continue
            
            if typed:
                result["success"] = True
                self._record_action("type", element_description, True, f"Typed: {text}")
                logger.info(f"Successfully typed into: {element_description}")
            else:
                result["error"] = "Could not type into element with any available method"
                
        except Exception as e:
            result["error"] = f"Error typing into element: {str(e)}"
        
        if not result["success"]:
            self._record_action("type", element_description, False, result["error"])
        
        return result
    
    async def ai_navigate(self, url: str, timeout: int = 30000) -> Dict[str, Any]:
        """
        Navigate to a URL
        
        Args:
            url: URL to navigate to
            timeout: Maximum wait time
            
        Returns:
            Dictionary with operation result
        """
        result = {
            "success": False,
            "action": "navigate",
            "target": url,
            "error": None
        }
        
        try:
            await self.page.goto(url, timeout=timeout, wait_until="networkidle")
            result["success"] = True
            self._record_action("navigate", url, True)
            logger.info(f"Successfully navigated to: {url}")
            
        except Exception as e:
            result["error"] = f"Error navigating to {url}: {str(e)}"
            self._record_action("navigate", url, False, result["error"])
        
        return result
    
    async def ai_wait_for_element(
        self,
        element_description: str,
        timeout: int = 30000,
        state: str = "visible"
    ) -> Dict[str, Any]:
        """
        Wait for an element to appear using AI-powered location
        
        Args:
            element_description: Description of element to wait for
            timeout: Maximum wait time
            state: Element state to wait for (visible, hidden, attached, detached)
            
        Returns:
            Dictionary with operation result
        """
        result = {
            "success": False,
            "action": "wait",
            "target": element_description,
            "error": None,
            "element_found": False
        }
        
        try:
            # First attempt to locate element
            screenshot = None
            if self.enable_screenshots:
                screenshot = await self.screenshot_taker.take_screenshot(self.page)
            
            location_result = await self.element_locator.locate_element(
                page=self.page,
                element_description=element_description,
                screenshot=screenshot,
                context=self._get_recent_context()
            )
            
            if location_result.get("found", False):
                result["element_found"] = True
                element_info = location_result.get("element", {})
                selectors = element_info.get("selector_suggestions", [])
                
                # Try to wait for element using selectors
                for selector in selectors:
                    try:
                        locator = self.page.locator(selector).first
                        await locator.wait_for(state=state, timeout=timeout)
                        result["success"] = True
                        break
                    except:
                        continue
                        
                if result["success"]:
                    self._record_action("wait", element_description, True)
                    logger.info(f"Successfully waited for element: {element_description}")
                else:
                    result["error"] = f"Element found but failed to wait for state '{state}'"
            else:
                result["error"] = f"Element not found: {element_description}"
                
        except Exception as e:
            result["error"] = f"Error waiting for element: {str(e)}"
        
        if not result["success"]:
            self._record_action("wait", element_description, False, result["error"])
        
        return result
    
    async def ai_scroll(
        self,
        direction_or_element: str,
        amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Scroll the page or to a specific element
        
        Args:
            direction_or_element: "up", "down", "top", "bottom" or element description
            amount: Scroll amount in pixels (for up/down)
            
        Returns:
            Dictionary with operation result
        """
        result = {
            "success": False,
            "action": "scroll",
            "target": direction_or_element,
            "error": None
        }
        
        try:
            direction = direction_or_element.lower()
            
            if direction in ["up", "down", "top", "bottom"]:
                if direction == "up":
                    await self.page.evaluate(f"window.scrollBy(0, -{amount or 500})")
                elif direction == "down":
                    await self.page.evaluate(f"window.scrollBy(0, {amount or 500})")
                elif direction == "top":
                    await self.page.evaluate("window.scrollTo(0, 0)")
                elif direction == "bottom":
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    
                result["success"] = True
                self._record_action("scroll", direction, True)
                
            else:
                # Try to scroll to specific element
                screenshot = None
                if self.enable_screenshots:
                    screenshot = await self.screenshot_taker.take_screenshot(self.page)
                
                location_result = await self.element_locator.locate_element(
                    page=self.page,
                    element_description=direction_or_element,
                    screenshot=screenshot,
                    context=self._get_recent_context()
                )
                
                if location_result.get("found", False):
                    element_info = location_result.get("element", {})
                    selectors = element_info.get("selector_suggestions", [])
                    
                    scrolled = False
                    for selector in selectors:
                        try:
                            locator = self.page.locator(selector).first
                            await locator.scroll_into_view_if_needed()
                            scrolled = True
                            break
                        except:
                            continue
                    
                    if scrolled:
                        result["success"] = True
                        self._record_action("scroll", direction_or_element, True)
                    else:
                        result["error"] = "Could not scroll to element"
                else:
                    result["error"] = f"Element not found for scrolling: {direction_or_element}"
                    
        except Exception as e:
            result["error"] = f"Error scrolling: {str(e)}"
        
        if not result["success"]:
            self._record_action("scroll", direction_or_element, False, result["error"])
        
        return result
    
    async def ai_verify(
        self,
        verification_description: str,
        timeout: int = 10000
    ) -> Dict[str, Any]:
        """
        Verify page state or element presence using AI
        
        Args:
            verification_description: What to verify
            timeout: Maximum wait time
            
        Returns:
            Dictionary with verification result
        """
        result = {
            "success": False,
            "action": "verify",
            "target": verification_description,
            "error": None,
            "verification_details": None
        }
        
        try:
            # Take screenshot for AI analysis
            screenshot = await self.screenshot_taker.take_screenshot(self.page)
            
            # Use AI to analyze current state
            analysis = self.ai_engine.analyze_screenshot(
                screenshot=screenshot,
                task_description=f"Verify: {verification_description}",
                context=self._get_recent_context()
            )
            
            # Check if verification criteria are met
            # This is a simplified verification - in a real implementation,
            # you might want more sophisticated verification logic
            
            verification_text = verification_description.lower()
            analysis_text = analysis.get("analysis", "").lower()
            
            # Simple keyword matching for common verification patterns
            if "success" in verification_text and "success" in analysis_text:
                result["success"] = True
            elif "error" in verification_text and "error" in analysis_text:
                result["success"] = True
            elif "login" in verification_text and ("login" in analysis_text or "signed in" in analysis_text):
                result["success"] = True
            elif "page" in verification_text and "page" in analysis_text:
                result["success"] = True
            else:
                # Use AI recommendations to determine success
                actions = analysis.get("recommended_actions", [])
                if not actions:  # No further actions suggested might mean verification passed
                    result["success"] = True
                    
            result["verification_details"] = analysis
            
            if result["success"]:
                self._record_action("verify", verification_description, True)
                logger.info(f"Verification passed: {verification_description}")
            else:
                result["error"] = f"Verification failed: {verification_description}"
                self._record_action("verify", verification_description, False, result["error"])
                
        except Exception as e:
            result["error"] = f"Error during verification: {str(e)}"
            self._record_action("verify", verification_description, False, result["error"])
        
        return result
    
    def _record_action(
        self,
        action: str,
        target: str,
        success: bool,
        details: Optional[str] = None
    ):
        """Record action in history for context"""
        import time
        
        action_record = {
            "timestamp": time.time(),
            "action": action,
            "target": target,
            "success": success,
            "details": details
        }
        
        self._action_history.append(action_record)
        
        # Keep only recent actions
        if len(self._action_history) > self._max_history:
            self._action_history.pop(0)
    
    def _get_recent_context(self) -> str:
        """Get recent action context for AI"""
        if not self._action_history:
            return "No previous actions"
        
        recent_actions = self._action_history[-3:]  # Last 3 actions
        context_parts = []
        
        for action in recent_actions:
            status = "succeeded" if action["success"] else "failed"
            context_parts.append(f"{action['action']} {action['target']} {status}")
        
        return "Recent actions: " + "; ".join(context_parts)