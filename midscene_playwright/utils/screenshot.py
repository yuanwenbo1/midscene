"""
Screenshot utility for AI analysis and debugging
"""

import os
import logging
from typing import Optional, Union
from datetime import datetime
from playwright.async_api import Page
from PIL import Image
import asyncio

logger = logging.getLogger(__name__)


class ScreenshotTaker:
    """
    Utility class for taking and managing screenshots for AI analysis
    
    Features:
    - High-quality screenshot capture
    - Automatic file management
    - Multiple format support
    - Viewport optimization for AI analysis
    """
    
    def __init__(
        self,
        output_dir: str = "screenshots",
        quality: int = 90,
        format: str = "PNG",
        full_page: bool = True,
        create_dir: bool = True
    ):
        """
        Initialize ScreenshotTaker
        
        Args:
            output_dir: Directory to save screenshots
            quality: Image quality (1-100, only for JPEG)
            format: Image format (PNG, JPEG)
            full_page: Whether to capture full page or just viewport
            create_dir: Whether to create output directory if it doesn't exist
        """
        self.output_dir = output_dir
        self.quality = quality
        self.format = format.upper()
        self.full_page = full_page
        
        if create_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created screenshot directory: {output_dir}")
        
        self._screenshot_counter = 0
    
    async def take_screenshot(
        self,
        page: Page,
        filename: Optional[str] = None,
        save_to_disk: bool = True,
        optimize_for_ai: bool = True
    ) -> Union[str, bytes]:
        """
        Take a screenshot of the current page
        
        Args:
            page: Playwright page instance
            filename: Custom filename (auto-generated if None)
            save_to_disk: Whether to save screenshot to disk
            optimize_for_ai: Whether to optimize screenshot for AI analysis
            
        Returns:
            File path if saved to disk, or bytes if not saved
        """
        try:
            # Generate filename if not provided
            if not filename and save_to_disk:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self._screenshot_counter += 1
                filename = f"screenshot_{timestamp}_{self._screenshot_counter:03d}.{self.format.lower()}"
            
            # Configure screenshot options
            screenshot_options = {
                "full_page": self.full_page,
                "type": self.format.lower()
            }
            
            if self.format == "JPEG":
                screenshot_options["quality"] = self.quality
            
            # Take screenshot
            screenshot_bytes = await page.screenshot(**screenshot_options)
            
            if optimize_for_ai:
                screenshot_bytes = self._optimize_for_ai(screenshot_bytes)
            
            if save_to_disk and filename:
                # Save to disk
                file_path = os.path.join(self.output_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(screenshot_bytes)
                
                logger.debug(f"Screenshot saved: {file_path}")
                return file_path
            else:
                return screenshot_bytes
                
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            raise
    
    def _optimize_for_ai(self, screenshot_bytes: bytes) -> bytes:
        """
        Optimize screenshot for AI analysis
        
        Args:
            screenshot_bytes: Original screenshot bytes
            
        Returns:
            Optimized screenshot bytes
        """
        try:
            # Open image with PIL
            from io import BytesIO
            image = Image.open(BytesIO(screenshot_bytes))
            
            # Optimization strategies for AI analysis
            
            # 1. Ensure reasonable size (AI models often have size limits)
            max_width = 1920
            max_height = 1080
            
            if image.width > max_width or image.height > max_height:
                # Calculate resize ratio to maintain aspect ratio
                width_ratio = max_width / image.width
                height_ratio = max_height / image.height
                resize_ratio = min(width_ratio, height_ratio)
                
                new_width = int(image.width * resize_ratio)
                new_height = int(image.height * resize_ratio)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.debug(f"Resized screenshot from {screenshot_bytes.__len__()} to {new_width}x{new_height}")
            
            # 2. Convert to RGB if necessary (some AI models prefer RGB)
            if image.mode in ['RGBA', 'LA']:
                # Create white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
                else:
                    background.paste(image)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 3. Apply slight sharpening for better text recognition
            try:
                from PIL import ImageFilter
                image = image.filter(ImageFilter.UnsharpMask(radius=0.5, percent=50, threshold=2))
            except ImportError:
                # PIL might not have ImageFilter in some installations
                pass
            
            # Save optimized image to bytes
            output_buffer = BytesIO()
            save_format = "PNG" if self.format == "PNG" else "JPEG"
            save_kwargs = {"format": save_format}
            
            if save_format == "JPEG":
                save_kwargs["quality"] = min(self.quality, 95)  # Cap quality for AI analysis
                save_kwargs["optimize"] = True
            else:
                save_kwargs["optimize"] = True
            
            image.save(output_buffer, **save_kwargs)
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"Error optimizing screenshot for AI: {str(e)}, using original")
            return screenshot_bytes
    
    async def take_element_screenshot(
        self,
        page: Page,
        selector: str,
        filename: Optional[str] = None,
        padding: int = 10
    ) -> Union[str, bytes]:
        """
        Take a screenshot of a specific element
        
        Args:
            page: Playwright page instance
            selector: CSS selector for the element
            filename: Custom filename
            padding: Padding around element in pixels
            
        Returns:
            File path if saved to disk, or bytes
        """
        try:
            # Wait for element to be visible
            element = page.locator(selector).first
            await element.wait_for(state="visible", timeout=10000)
            
            # Get element bounding box
            bounding_box = await element.bounding_box()
            if not bounding_box:
                raise ValueError(f"Could not get bounding box for element: {selector}")
            
            # Add padding
            clip = {
                "x": max(0, bounding_box["x"] - padding),
                "y": max(0, bounding_box["y"] - padding),
                "width": bounding_box["width"] + (2 * padding),
                "height": bounding_box["height"] + (2 * padding)
            }
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self._screenshot_counter += 1
                filename = f"element_{timestamp}_{self._screenshot_counter:03d}.{self.format.lower()}"
            
            # Take screenshot with clipping
            screenshot_bytes = await page.screenshot(
                clip=clip,
                type=self.format.lower(),
                quality=self.quality if self.format == "JPEG" else None
            )
            
            # Save to disk
            file_path = os.path.join(self.output_dir, filename)
            with open(file_path, "wb") as f:
                f.write(screenshot_bytes)
            
            logger.debug(f"Element screenshot saved: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error taking element screenshot: {str(e)}")
            raise
    
    async def take_comparison_screenshots(
        self,
        page: Page,
        actions: list,
        delay_between: float = 1.0
    ) -> list:
        """
        Take a series of screenshots before and after actions for comparison
        
        Args:
            page: Playwright page instance
            actions: List of action descriptions
            delay_between: Delay between screenshots in seconds
            
        Returns:
            List of screenshot file paths
        """
        screenshots = []
        
        try:
            for i, action in enumerate(actions):
                # Take before screenshot
                before_filename = f"before_action_{i:02d}_{action.replace(' ', '_')[:20]}.{self.format.lower()}"
                before_path = await self.take_screenshot(page, before_filename)
                screenshots.append(("before", action, before_path))
                
                # Wait for any dynamic content to settle
                await asyncio.sleep(delay_between)
                
                # Take after screenshot (this would be done after performing the action)
                after_filename = f"after_action_{i:02d}_{action.replace(' ', '_')[:20]}.{self.format.lower()}"
                after_path = await self.take_screenshot(page, after_filename)
                screenshots.append(("after", action, after_path))
                
                logger.debug(f"Captured comparison screenshots for action: {action}")
            
            return screenshots
            
        except Exception as e:
            logger.error(f"Error taking comparison screenshots: {str(e)}")
            raise
    
    def cleanup_old_screenshots(self, keep_days: int = 7):
        """
        Clean up old screenshots to manage disk space
        
        Args:
            keep_days: Number of days to keep screenshots
        """
        try:
            import time
            from pathlib import Path
            
            current_time = time.time()
            cutoff_time = current_time - (keep_days * 24 * 60 * 60)
            
            screenshots_dir = Path(self.output_dir)
            deleted_count = 0
            
            for file_path in screenshots_dir.glob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old screenshots older than {keep_days} days")
            
        except Exception as e:
            logger.warning(f"Error cleaning up old screenshots: {str(e)}")
    
    def get_screenshot_info(self, file_path: str) -> dict:
        """
        Get information about a screenshot file
        
        Args:
            file_path: Path to screenshot file
            
        Returns:
            Dictionary with screenshot information
        """
        try:
            from PIL import Image
            import os
            
            if not os.path.exists(file_path):
                return {"error": "File not found"}
            
            # Get file stats
            stat = os.stat(file_path)
            
            # Get image info
            with Image.open(file_path) as img:
                info = {
                    "filename": os.path.basename(file_path),
                    "full_path": file_path,
                    "size_bytes": stat.st_size,
                    "created_time": datetime.fromtimestamp(stat.st_ctime),
                    "modified_time": datetime.fromtimestamp(stat.st_mtime),
                    "image_format": img.format,
                    "image_mode": img.mode,
                    "image_size": img.size,
                    "width": img.width,
                    "height": img.height
                }
                
                return info
                
        except Exception as e:
            return {"error": f"Error getting screenshot info: {str(e)}"}
    
    @property
    def screenshot_count(self) -> int:
        """Get the current screenshot counter"""
        return self._screenshot_counter