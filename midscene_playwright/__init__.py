"""
Midscene Playwright - AI-powered test automation framework

A Python implementation of Midscene.js as a Playwright extension plugin,
featuring AI-driven element location, test planning, and execution with
Qwen Vision Language model integration.
"""

__version__ = "0.1.0"
__author__ = "Midscene Team"
__description__ = "AI-powered Playwright extension for automated testing"

from .core.ai_engine import QwenVLEngine
from .core.playwright_extension import MidscenePlaywright
from .core.page_agent import PageAgent
from .core.test_planner import TestPlanner
from .utils.screenshot import ScreenshotTaker
from .utils.element_locator import AIElementLocator

__all__ = [
    "QwenVLEngine",
    "MidscenePlaywright", 
    "PageAgent",
    "TestPlanner",
    "ScreenshotTaker",
    "AIElementLocator",
]