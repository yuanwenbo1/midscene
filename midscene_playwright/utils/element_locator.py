"""
AI-powered element locator for intelligent UI automation
"""

import logging
from typing import Dict, Any, List, Optional, Union
from playwright.async_api import Page, Locator
from .screenshot import ScreenshotTaker
from ..core.ai_engine import QwenVLEngine

logger = logging.getLogger(__name__)


class AIElementLocator:
    """
    AI-powered element locator that combines visual analysis with DOM inspection
    
    Features:
    - Visual element identification using AI
    - Smart selector generation
    - Fallback strategies for element location
    - Context-aware element matching
    """
    
    def __init__(
        self,
        ai_engine: QwenVLEngine,
        screenshot_taker: ScreenshotTaker
    ):
        """
        Initialize AIElementLocator
        
        Args:
            ai_engine: AI engine for visual analysis
            screenshot_taker: Screenshot utility for capturing page state
        """
        self.ai_engine = ai_engine
        self.screenshot_taker = screenshot_taker
        
        # Cache for recently located elements to improve performance
        self._element_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_max_size = 50
        
        logger.debug("Initialized AIElementLocator")
    
    async def locate_element(
        self,
        page: Page,
        element_description: str,
        screenshot: Optional[Union[str, bytes]] = None,
        context: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Locate an element using AI-powered visual analysis
        
        Args:
            page: Playwright page instance
            element_description: Human description of element to find
            screenshot: Screenshot for analysis (taken if not provided)
            context: Additional context about the search
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with location results
        """
        # Create cache key
        cache_key = f"{page.url}_{element_description}_{context or ''}"
        
        # Check cache first
        if use_cache and cache_key in self._element_cache:
            cached_result = self._element_cache[cache_key]
            logger.debug(f"Using cached result for element: {element_description}")
            return cached_result
        
        try:
            # Take screenshot if not provided
            if screenshot is None:
                screenshot = await self.screenshot_taker.take_screenshot(
                    page, save_to_disk=False, optimize_for_ai=True
                )
            
            # Get AI analysis of the element location
            ai_result = self.ai_engine.locate_element(
                screenshot=screenshot,
                element_description=element_description,
                context=context
            )
            
            if not ai_result.get("found", False):
                logger.warning(f"AI could not locate element: {element_description}")
                return ai_result
            
            # Enhance AI result with DOM-based selectors
            enhanced_result = await self._enhance_with_dom_analysis(
                page, element_description, ai_result
            )
            
            # Validate suggested selectors
            validated_result = await self._validate_selectors(page, enhanced_result)
            
            # Cache the result
            if use_cache:
                self._cache_result(cache_key, validated_result)
            
            logger.info(f"Successfully located element: {element_description}")
            return validated_result
            
        except Exception as e:
            logger.error(f"Error locating element '{element_description}': {str(e)}")
            return {
                "found": False,
                "element": None,
                "reasoning": f"Error during location: {str(e)}",
                "alternatives": [],
                "coordinates": None,
                "selector_suggestions": [],
                "validation_results": []
            }
    
    async def _enhance_with_dom_analysis(
        self,
        page: Page,
        element_description: str,
        ai_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance AI results with DOM-based analysis
        
        Args:
            page: Playwright page instance
            element_description: Element description
            ai_result: Result from AI analysis
            
        Returns:
            Enhanced result with additional selectors
        """
        try:
            element_info = ai_result.get("element", {})
            ai_selectors = element_info.get("selector_suggestions", [])
            
            # Generate additional selectors based on common patterns
            additional_selectors = await self._generate_smart_selectors(
                page, element_description, ai_result
            )
            
            # Combine AI and generated selectors
            all_selectors = ai_selectors + additional_selectors
            
            # Remove duplicates while preserving order
            unique_selectors = []
            seen = set()
            for selector in all_selectors:
                if selector not in seen:
                    unique_selectors.append(selector)
                    seen.add(selector)
            
            # Update the result
            enhanced_result = ai_result.copy()
            if "element" in enhanced_result:
                enhanced_result["element"]["selector_suggestions"] = unique_selectors
            
            return enhanced_result
            
        except Exception as e:
            logger.warning(f"Error enhancing with DOM analysis: {str(e)}")
            return ai_result
    
    async def _generate_smart_selectors(
        self,
        page: Page,
        element_description: str,
        ai_result: Dict[str, Any]
    ) -> List[str]:
        """
        Generate smart selectors based on element description and page content
        
        Args:
            page: Playwright page instance
            element_description: Element description
            ai_result: AI analysis result
            
        Returns:
            List of generated selectors
        """
        selectors = []
        
        try:
            description_lower = element_description.lower()
            
            # Extract keywords from description
            keywords = self._extract_keywords(description_lower)
            
            # Generate selectors based on common UI patterns
            
            # 1. Button selectors
            if any(word in description_lower for word in ["button", "click", "submit", "send"]):
                selectors.extend([
                    "button",
                    "input[type='submit']",
                    "input[type='button']",
                    "[role='button']",
                    ".btn",
                    ".button",
                    "a[href]"
                ])
                
                # Add text-based button selectors
                for keyword in keywords:
                    if len(keyword) > 2:
                        selectors.extend([
                            f"button:has-text('{keyword}')",
                            f"[role='button']:has-text('{keyword}')",
                            f"text='{keyword}'"
                        ])
            
            # 2. Input field selectors
            if any(word in description_lower for word in ["input", "field", "text", "email", "password", "search"]):
                selectors.extend([
                    "input",
                    "textarea",
                    "[contenteditable]",
                    "[role='textbox']"
                ])
                
                # Add specific input type selectors
                if "email" in description_lower:
                    selectors.append("input[type='email']")
                if "password" in description_lower:
                    selectors.append("input[type='password']")
                if "search" in description_lower:
                    selectors.append("input[type='search']")
                
                # Add placeholder and label-based selectors
                for keyword in keywords:
                    if len(keyword) > 2:
                        selectors.extend([
                            f"input[placeholder*='{keyword}' i]",
                            f"input[name*='{keyword}' i]",
                            f"label:has-text('{keyword}') + input",
                            f"label:has-text('{keyword}') input"
                        ])
            
            # 3. Link selectors
            if any(word in description_lower for word in ["link", "navigate", "go to"]):
                selectors.extend([
                    "a[href]",
                    "[role='link']"
                ])
                
                for keyword in keywords:
                    if len(keyword) > 2:
                        selectors.extend([
                            f"a:has-text('{keyword}')",
                            f"a[href*='{keyword}' i]"
                        ])
            
            # 4. Menu and navigation selectors
            if any(word in description_lower for word in ["menu", "nav", "dropdown"]):
                selectors.extend([
                    "nav",
                    "[role='navigation']",
                    "[role='menu']",
                    ".menu",
                    ".nav",
                    ".dropdown"
                ])
            
            # 5. Form selectors
            if any(word in description_lower for word in ["form", "signup", "login", "register"]):
                selectors.extend([
                    "form",
                    "[role='form']"
                ])
            
            # 6. Content selectors based on text
            for keyword in keywords:
                if len(keyword) > 2:
                    selectors.extend([
                        f"text='{keyword}'",
                        f":has-text('{keyword}')",
                        f"[title*='{keyword}' i]",
                        f"[aria-label*='{keyword}' i]",
                        f"[data-testid*='{keyword}' i]",
                        f"#{keyword}",
                        f".{keyword}"
                    ])
            
            # 7. Position-based selectors from AI coordinates
            coordinates = ai_result.get("coordinates", {})
            if coordinates and "region" in coordinates:
                region = coordinates["region"]
                if region in ["top-left", "top-right", "bottom-left", "bottom-right"]:
                    # Add region-specific selectors (this is a simplified approach)
                    if "top" in region:
                        selectors.append("header *")
                    if "bottom" in region:
                        selectors.append("footer *")
            
            # Remove overly generic selectors
            filtered_selectors = [s for s in selectors if not s in ["*", "div", "span"]]
            
            return filtered_selectors[:20]  # Limit to top 20 selectors
            
        except Exception as e:
            logger.warning(f"Error generating smart selectors: {str(e)}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract meaningful keywords from element description
        
        Args:
            text: Input text to extract keywords from
            
        Returns:
            List of keywords
        """
        # Remove common stop words and extract meaningful terms
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
            "by", "from", "up", "about", "into", "through", "during", "before", "after",
            "above", "below", "between", "among", "this", "that", "these", "those", "is", "are",
            "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "can"
        }
        
        # Split and clean words
        words = []
        for word in text.split():
            # Remove punctuation and convert to lowercase
            clean_word = ''.join(c for c in word if c.isalnum()).lower()
            if len(clean_word) > 2 and clean_word not in stop_words:
                words.append(clean_word)
        
        return words
    
    async def _validate_selectors(
        self,
        page: Page,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate suggested selectors against the actual page
        
        Args:
            page: Playwright page instance
            result: Result dictionary with selectors to validate
            
        Returns:
            Result with validation information
        """
        try:
            element_info = result.get("element", {})
            selectors = element_info.get("selector_suggestions", [])
            
            validation_results = []
            working_selectors = []
            
            for selector in selectors:
                try:
                    # Test if selector finds any elements
                    locator = page.locator(selector)
                    count = await locator.count()
                    
                    if count > 0:
                        # Check if element is visible
                        try:
                            first_element = locator.first
                            is_visible = await first_element.is_visible()
                            is_enabled = await first_element.is_enabled()
                            
                            validation_info = {
                                "selector": selector,
                                "count": count,
                                "visible": is_visible,
                                "enabled": is_enabled,
                                "score": self._calculate_selector_score(count, is_visible, is_enabled)
                            }
                            
                            validation_results.append(validation_info)
                            
                            if is_visible and is_enabled:
                                working_selectors.append(selector)
                                
                        except Exception:
                            # Element found but can't check properties
                            validation_results.append({
                                "selector": selector,
                                "count": count,
                                "visible": False,
                                "enabled": False,
                                "score": 0.1
                            })
                    else:
                        validation_results.append({
                            "selector": selector,
                            "count": 0,
                            "visible": False,
                            "enabled": False,
                            "score": 0
                        })
                        
                except Exception as e:
                    validation_results.append({
                        "selector": selector,
                        "count": 0,
                        "visible": False,
                        "enabled": False,
                        "score": 0,
                        "error": str(e)
                    })
            
            # Sort selectors by score (best first)
            validation_results.sort(key=lambda x: x["score"], reverse=True)
            working_selectors = [vr["selector"] for vr in validation_results if vr["score"] > 0.5]
            
            # Update result with validation info
            validated_result = result.copy()
            validated_result["validation_results"] = validation_results
            validated_result["working_selectors"] = working_selectors
            
            if "element" in validated_result:
                validated_result["element"]["selector_suggestions"] = working_selectors
            
            return validated_result
            
        except Exception as e:
            logger.warning(f"Error validating selectors: {str(e)}")
            result["validation_error"] = str(e)
            return result
    
    def _calculate_selector_score(
        self,
        count: int,
        is_visible: bool,
        is_enabled: bool
    ) -> float:
        """
        Calculate a score for a selector based on its properties
        
        Args:
            count: Number of elements found
            is_visible: Whether element is visible
            is_enabled: Whether element is enabled
            
        Returns:
            Score between 0 and 1
        """
        score = 0.0
        
        # Prefer selectors that find exactly one element
        if count == 1:
            score += 0.5
        elif count > 1:
            score += 0.3  # Multiple matches are okay but less preferred
        # count == 0 gets score 0
        
        # Visible elements are much better
        if is_visible:
            score += 0.3
        
        # Enabled elements are better for interaction
        if is_enabled:
            score += 0.2
        
        return min(score, 1.0)
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """
        Cache a location result
        
        Args:
            cache_key: Key for caching
            result: Result to cache
        """
        try:
            # Manage cache size
            if len(self._element_cache) >= self._cache_max_size:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(self._element_cache))
                del self._element_cache[oldest_key]
            
            self._element_cache[cache_key] = result
            logger.debug(f"Cached element location result for key: {cache_key}")
            
        except Exception as e:
            logger.warning(f"Error caching result: {str(e)}")
    
    def clear_cache(self):
        """Clear the element location cache"""
        self._element_cache.clear()
        logger.debug("Cleared element location cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_size": len(self._element_cache),
            "max_cache_size": self._cache_max_size,
            "cache_keys": list(self._element_cache.keys())
        }