"""
AI Engine implementation using Qwen Vision Language model
"""

import base64
import json
import logging
from typing import Dict, Any, List, Optional, Union
from io import BytesIO
from PIL import Image
import requests
from openai import OpenAI

logger = logging.getLogger(__name__)


class QwenVLEngine:
    """
    Qwen Vision Language model engine for AI-powered automation tasks
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: str = "qwen-vl-max-latest",
        max_tokens: int = 2000,
        temperature: float = 0.1
    ):
        """
        Initialize Qwen VL engine
        
        Args:
            api_key: DashScope API key for Qwen models
            base_url: API base URL 
            model: Model name (default: qwen-vl-max-latest)
            max_tokens: Maximum tokens in response
            temperature: Model temperature for randomness
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize OpenAI-compatible client for Qwen
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        logger.info(f"Initialized QwenVL engine with model: {model}")
    
    def encode_image(self, image_data: Union[bytes, Image.Image, str]) -> str:
        """
        Encode image to base64 string
        
        Args:
            image_data: Image as bytes, PIL Image, or file path
            
        Returns:
            Base64 encoded image string
        """
        if isinstance(image_data, str):
            # File path
            with open(image_data, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        elif isinstance(image_data, Image.Image):
            # PIL Image
            buffer = BytesIO()
            image_data.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        elif isinstance(image_data, bytes):
            # Bytes
            return base64.b64encode(image_data).decode('utf-8')
        else:
            raise ValueError("Unsupported image data type")
    
    def analyze_screenshot(
        self,
        screenshot: Union[bytes, Image.Image, str],
        task_description: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze screenshot and provide task guidance
        
        Args:
            screenshot: Screenshot image data
            task_description: Description of the task to perform
            context: Additional context about the page
            
        Returns:
            Dictionary containing analysis results and recommendations
        """
        try:
            # Encode image
            image_b64 = self.encode_image(screenshot)
            
            # Construct prompt
            system_prompt = """You are an expert web automation assistant. Analyze the provided screenshot and help plan automation tasks.

Your response should be a valid JSON object with the following structure:
{
    "analysis": "Description of what you see in the screenshot",
    "elements": [
        {
            "type": "button|input|link|text|other",
            "description": "Description of the element",
            "location": "Description of where the element is located",
            "selector_suggestion": "Suggested CSS/XPath selector if possible",
            "confidence": 0.8
        }
    ],
    "recommended_actions": [
        {
            "action": "click|type|wait|scroll|navigate",
            "target": "Description of target element",
            "value": "Value to input (for type actions)",
            "reasoning": "Why this action is recommended"
        }
    ],
    "risks": ["Potential issues or risks"],
    "success_indicators": ["How to verify task completion"]
}

Focus on being practical and actionable. Provide specific element descriptions and locations."""

            user_content = f"Task: {task_description}"
            if context:
                user_content += f"\nAdditional context: {context}"
            user_content += "\n\nPlease analyze this screenshot and provide automation guidance."
            
            # Call Qwen VL API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text",
                                "text": user_content
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                result = json.loads(content)
                logger.info("Successfully analyzed screenshot with AI")
                return result
            except json.JSONDecodeError:
                # Fallback if not valid JSON
                logger.warning("AI response was not valid JSON, using fallback format")
                return {
                    "analysis": content,
                    "elements": [],
                    "recommended_actions": [],
                    "risks": ["AI response was not in expected format"],
                    "success_indicators": []
                }
                
        except Exception as e:
            logger.error(f"Error analyzing screenshot: {str(e)}")
            return {
                "analysis": f"Error occurred during analysis: {str(e)}",
                "elements": [],
                "recommended_actions": [],
                "risks": ["AI analysis failed"],
                "success_indicators": []
            }
    
    def locate_element(
        self,
        screenshot: Union[bytes, Image.Image, str],
        element_description: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Locate specific element in screenshot
        
        Args:
            screenshot: Screenshot image data
            element_description: Description of element to find
            context: Additional context
            
        Returns:
            Dictionary with element location information
        """
        try:
            image_b64 = self.encode_image(screenshot)
            
            system_prompt = """You are an expert at locating web elements in screenshots. Your task is to find and describe the location of specific elements.

Return a JSON object with this structure:
{
    "found": true/false,
    "element": {
        "description": "Detailed description of the found element",
        "location": "Precise description of where it's located",
        "visual_context": "Description of surrounding elements",
        "selector_suggestions": ["CSS selector suggestions"],
        "xpath_suggestions": ["XPath selector suggestions"],
        "confidence": 0.9
    },
    "reasoning": "Explanation of how you identified the element",
    "alternatives": ["Other similar elements found"],
    "coordinates": {
        "approximate_x": 500,
        "approximate_y": 300,
        "region": "top-left|top-right|center|bottom-left|bottom-right"
    }
}

Be very specific about element location and provide actionable selector suggestions."""

            user_content = f"Please locate this element: {element_description}"
            if context:
                user_content += f"\nContext: {context}"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_content},
                            {
                                "type": "image_url", 
                                "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                            }
                        ]
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "found": False,
                    "element": None,
                    "reasoning": content,
                    "alternatives": [],
                    "coordinates": None
                }
                
        except Exception as e:
            logger.error(f"Error locating element: {str(e)}")
            return {
                "found": False,
                "element": None, 
                "reasoning": f"Error: {str(e)}",
                "alternatives": [],
                "coordinates": None
            }
    
    def plan_test_steps(
        self,
        screenshot: Union[bytes, Image.Image, str],
        test_objective: str,
        current_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Plan test execution steps based on screenshot and objective
        
        Args:
            screenshot: Current page screenshot
            test_objective: What the test should accomplish
            current_url: Current page URL
            
        Returns:
            Dictionary with planned test steps
        """
        try:
            image_b64 = self.encode_image(screenshot)
            
            system_prompt = """You are an expert test automation planner. Analyze the screenshot and create a detailed test plan.

Return a JSON object with this structure:
{
    "test_plan": {
        "objective": "Restated test objective",
        "estimated_steps": 5,
        "complexity": "low|medium|high",
        "estimated_time": "30 seconds"
    },
    "steps": [
        {
            "step_number": 1,
            "action": "navigate|click|type|wait|verify|scroll",
            "target": "Element description or URL",
            "value": "Value to input (if applicable)",
            "description": "Human readable description",
            "expected_result": "What should happen",
            "verification": "How to verify success",
            "selectors": ["Suggested selectors"],
            "fallback_options": ["Alternative approaches"]
        }
    ],
    "prerequisites": ["Things that must be true before starting"],
    "success_criteria": ["How to know the test passed"],
    "potential_failures": ["Common failure points"],
    "data_requirements": ["Any test data needed"]
}

Make the plan practical and executable. Focus on robustness and clear verification steps."""

            user_content = f"Test Objective: {test_objective}"
            if current_url:
                user_content += f"\nCurrent URL: {current_url}"
            user_content += "\n\nPlease create a detailed test plan for this objective."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_content},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                            }
                        ]
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "test_plan": {
                        "objective": test_objective,
                        "estimated_steps": 1,
                        "complexity": "unknown",
                        "estimated_time": "unknown"
                    },
                    "steps": [{
                        "step_number": 1,
                        "action": "manual_review",
                        "target": "page", 
                        "description": content,
                        "expected_result": "Manual review completed",
                        "verification": "Human verification required"
                    }],
                    "prerequisites": [],
                    "success_criteria": [],
                    "potential_failures": ["AI response format error"],
                    "data_requirements": []
                }
                
        except Exception as e:
            logger.error(f"Error planning test steps: {str(e)}")
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
                "potential_failures": [f"Planning failed: {str(e)}"],
                "data_requirements": []
            }