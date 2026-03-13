"""
Browser MCP Server for AI Employee Silver Tier.

This module implements browser automation capabilities via MCP pattern.
Uses Playwright for browser automation.

Agent Skills:
    - browser.navigate(url) -> bool
    - browser.click(selector) -> bool
    - browser.fill(selector, text) -> bool
    - browser.screenshot(name) -> str (path)
    - browser.extract(selector) -> str
    - browser.submit_form(form_selector) -> bool
"""

import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from playwright.sync_api import sync_playwright, Browser, Page, Playwright

from ..config.settings import Settings, get_settings
from ..utils.logger import get_logger


class BrowserMCPServer:
    """
    Browser MCP Server providing web automation capabilities via Playwright.
    
    This server exposes browser operations as Agent Skills following
    the MCP (Model Context Protocol) pattern.
    """
    
    def __init__(
        self,
        settings: Optional[Settings] = None,
        logger: Optional[logging.Logger] = None,
        headless: bool = True
    ):
        """
        Initialize Browser MCP Server.
        
        Args:
            settings: Application settings
            logger: Logger instance
            headless: Run browser in headless mode (default: True)
        """
        self.settings = settings if settings else get_settings()
        self.logger = logger if logger else get_logger()
        self.headless = headless
        
        # Browser state
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._initialized = False
        
        # Screenshot directory
        self.screenshot_dir = Path(__file__).parent.parent.parent.parent / "browser_screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize(self) -> bool:
        """
        Initialize Playwright and browser.
        
        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("Initializing Browser MCP Server...")
            
            # Start Playwright
            self.playwright = sync_playwright().start()
            
            # Launch browser
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )
            
            # Create page
            self.page = self.browser.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(30000)
            
            self._initialized = True
            self.logger.info("Browser MCP Server initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Browser initialization failed: {e}")
            return False
    
    def ensure_initialized(self) -> bool:
        """Ensure browser is initialized."""
        if not self._initialized:
            return self.initialize()
        return True
    
    def close(self) -> None:
        """Close browser and cleanup."""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self._initialized = False
            self.logger.info("Browser MCP Server closed")
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")
    
    # =========================================================================
    # Agent Skills - Browser Operations
    # =========================================================================
    
    def navigate(self, url: str, wait_until: str = "load") -> Dict[str, Any]:
        """
        Navigate to URL.
        
        Agent Skill: browser.navigate
        
        Args:
            url: URL to navigate to
            wait_until: When to consider navigation done
                       (load, domcontentloaded, networkidle, commit)
            
        Returns:
            dict with 'success' (bool) and 'url' (str) or 'error' (str)
        """
        try:
            if not self.ensure_initialized():
                return {"success": False, "error": "Not initialized"}
            
            self.logger.info(f"Navigating to: {url}")
            
            response = self.page.goto(url, wait_until=wait_until)
            
            # Wait for page to stabilize
            time.sleep(1)
            
            self.logger.info(f"Navigation successful: {self.page.url}")
            
            return {
                "success": True,
                "url": self.page.url,
                "title": self.page.title(),
                "status": response.status if response else 0
            }
            
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def click(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """
        Click element matching selector.
        
        Agent Skill: browser.click
        
        Args:
            selector: CSS selector for element
            timeout: Timeout in milliseconds
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            if not self.ensure_initialized():
                return {"success": False, "error": "Not initialized"}
            
            self.logger.info(f"Clicking: {selector}")
            
            # Wait for element and click
            self.page.wait_for_selector(selector, timeout=timeout)
            self.page.click(selector, timeout=timeout)
            
            self.logger.info(f"Click successful: {selector}")
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return {"success": False, "error": str(e)}
    
    def fill(
        self,
        selector: str,
        text: str,
        timeout: int = 5000
    ) -> Dict[str, Any]:
        """
        Fill input field with text.
        
        Agent Skill: browser.fill
        
        Args:
            selector: CSS selector for input field
            text: Text to fill
            timeout: Timeout in milliseconds
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            if not self.ensure_initialized():
                return {"success": False, "error": "Not initialized"}
            
            self.logger.info(f"Filling {selector} with text ({len(text)} chars)")
            
            # Wait for element and fill
            self.page.wait_for_selector(selector, timeout=timeout)
            self.page.fill(selector, text, timeout=timeout)
            
            self.logger.info(f"Fill successful: {selector}")
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Fill failed: {e}")
            return {"success": False, "error": str(e)}
    
    def screenshot(
        self,
        name: Optional[str] = None,
        full_page: bool = False
    ) -> Dict[str, Any]:
        """
        Take screenshot of current page.
        
        Agent Skill: browser.screenshot
        
        Args:
            name: Optional name for screenshot file
            full_page: Capture full page (default: False)
            
        Returns:
            dict with 'success' (bool) and 'path' (str) or 'error' (str)
        """
        try:
            if not self.ensure_initialized():
                return {"success": False, "error": "Not initialized"}
            
            # Generate filename
            if name:
                filename = f"{name}.png"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            filepath = self.screenshot_dir / filename
            
            self.logger.info(f"Taking screenshot: {filename}")
            
            # Take screenshot
            self.page.screenshot(
                path=str(filepath),
                full_page=full_page
            )
            
            self.logger.info(f"Screenshot saved: {filepath}")
            
            return {
                "success": True,
                "path": str(filepath),
                "filename": filename
            }
            
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return {"success": False, "error": str(e)}
    
    def extract(self, selector: str, attribute: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract text or attribute from element.
        
        Agent Skill: browser.extract
        
        Args:
            selector: CSS selector for element
            attribute: Optional attribute to extract (None for text content)
            
        Returns:
            dict with 'success' (bool) and 'content' (str) or 'error' (str)
        """
        try:
            if not self.ensure_initialized():
                return {"success": False, "error": "Not initialized"}
            
            self.logger.info(f"Extracting from: {selector}")
            
            # Wait for element
            self.page.wait_for_selector(selector, timeout=5000)
            
            # Extract content
            if attribute:
                content = self.page.get_attribute(selector, attribute)
            else:
                content = self.page.text_content(selector)
            
            self.logger.info(f"Extracted: {content[:100] if content else 'empty'}...")
            
            return {
                "success": True,
                "content": content,
                "selector": selector
            }
            
        except Exception as e:
            self.logger.error(f"Extract failed: {e}")
            return {"success": False, "error": str(e)}
    
    def submit_form(self, form_selector: str) -> Dict[str, Any]:
        """
        Submit form.
        
        Agent Skill: browser.submit_form
        
        Args:
            form_selector: CSS selector for form
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            if not self.ensure_initialized():
                return {"success": False, "error": "Not initialized"}
            
            self.logger.info(f"Submitting form: {form_selector}")
            
            # Find submit button and click
            submit_selector = f"{form_selector} button[type='submit'], {form_selector} input[type='submit']"
            
            self.page.wait_for_selector(submit_selector, timeout=5000)
            self.page.click(submit_selector)
            
            # Wait for navigation
            self.page.wait_for_load_state("networkidle")
            
            self.logger.info("Form submitted successfully")
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Form submit failed: {e}")
            return {"success": False, "error": str(e)}
    
    def press(self, selector: str, key: str) -> Dict[str, Any]:
        """
        Press key on element.
        
        Agent Skill: browser.press
        
        Args:
            selector: CSS selector for element
            key: Key to press (e.g., "Enter", "Tab")
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            if not self.ensure_initialized():
                return {"success": False, "error": "Not initialized"}
            
            self.logger.info(f"Pressing {key} on {selector}")
            
            self.page.press(selector, key)
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Key press failed: {e}")
            return {"success": False, "error": str(e)}
    
    def hover(self, selector: str) -> Dict[str, Any]:
        """
        Hover over element.
        
        Agent Skill: browser.hover
        
        Args:
            selector: CSS selector for element
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            if not self.ensure_initialized():
                return {"success": False, "error": "Not initialized"}
            
            self.logger.info(f"Hovering: {selector}")
            
            self.page.hover(selector)
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Hover failed: {e}")
            return {"success": False, "error": str(e)}
    
    def evaluate(self, javascript: str) -> Dict[str, Any]:
        """
        Execute JavaScript on page.
        
        Agent Skill: browser.evaluate
        
        Args:
            javascript: JavaScript code to execute
            
        Returns:
            dict with 'success' (bool) and 'result' (any) or 'error' (str)
        """
        try:
            if not self.ensure_initialized():
                return {"success": False, "error": "Not initialized"}
            
            self.logger.info(f"Evaluating JavaScript: {javascript[:50]}...")
            
            result = self.page.evaluate(javascript)
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"JavaScript evaluation failed: {e}")
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # MCP Server Interface
    # =========================================================================
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of MCP tools (Agent Skills).
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "browser.navigate",
                "description": "Navigate to URL",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to navigate to"},
                        "wait_until": {"type": "string", "description": "Wait condition"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "browser.click",
                "description": "Click element matching selector",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"},
                        "timeout": {"type": "integer", "description": "Timeout in ms"}
                    },
                    "required": ["selector"]
                }
            },
            {
                "name": "browser.fill",
                "description": "Fill input field with text",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"},
                        "text": {"type": "string", "description": "Text to fill"},
                        "timeout": {"type": "integer", "description": "Timeout in ms"}
                    },
                    "required": ["selector", "text"]
                }
            },
            {
                "name": "browser.screenshot",
                "description": "Take screenshot of current page",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Screenshot name"},
                        "full_page": {"type": "boolean", "description": "Full page screenshot"}
                    }
                }
            },
            {
                "name": "browser.extract",
                "description": "Extract text or attribute from element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"},
                        "attribute": {"type": "string", "description": "Attribute name"}
                    },
                    "required": ["selector"]
                }
            },
            {
                "name": "browser.submit_form",
                "description": "Submit form",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "form_selector": {"type": "string", "description": "Form CSS selector"}
                    },
                    "required": ["form_selector"]
                }
            },
            {
                "name": "browser.press",
                "description": "Press key on element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"},
                        "key": {"type": "string", "description": "Key to press"}
                    },
                    "required": ["selector", "key"]
                }
            },
            {
                "name": "browser.evaluate",
                "description": "Execute JavaScript on page",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "javascript": {"type": "string", "description": "JavaScript code"}
                    },
                    "required": ["javascript"]
                }
            }
        ]
    
    def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool (Agent Skill) by name.
        
        Args:
            name: Tool name
            args: Tool arguments
            
        Returns:
            Tool execution result
        """
        tools = {
            "browser.navigate": lambda **kwargs: self.navigate(**kwargs),
            "browser.click": lambda **kwargs: self.click(**kwargs),
            "browser.fill": lambda **kwargs: self.fill(**kwargs),
            "browser.screenshot": lambda **kwargs: self.screenshot(**kwargs),
            "browser.extract": lambda **kwargs: self.extract(**kwargs),
            "browser.submit_form": lambda **kwargs: self.submit_form(**kwargs),
            "browser.press": lambda **kwargs: self.press(**kwargs),
            "browser.hover": lambda **kwargs: self.hover(**kwargs),
            "browser.evaluate": lambda **kwargs: self.evaluate(**kwargs)
        }
        
        if name not in tools:
            return {"success": False, "error": f"Unknown tool: {name}"}
        
        return tools[name](**args)
    
    def get_skills(self) -> Dict[str, callable]:
        """
        Get all Agent Skills exposed by this server.
        
        Returns:
            Dictionary of skill names to callables
        """
        return {
            "browser.navigate": self.navigate,
            "browser.click": self.click,
            "browser.fill": self.fill,
            "browser.screenshot": self.screenshot,
            "browser.extract": self.extract,
            "browser.submit_form": self.submit_form,
            "browser.press": self.press,
            "browser.hover": self.hover,
            "browser.evaluate": self.evaluate,
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global instance
_browser_server: Optional[BrowserMCPServer] = None


def get_browser_server() -> BrowserMCPServer:
    """Get or create global Browser MCP Server instance."""
    global _browser_server
    if _browser_server is None:
        _browser_server = BrowserMCPServer()
    return _browser_server


if __name__ == "__main__":
    # Test Browser MCP Server
    print("=== Browser MCP Server Test ===\n")
    
    with BrowserMCPServer(headless=False) as server:
        # Test navigate
        result = server.navigate("https://www.example.com")
        if result["success"]:
            print(f"✓ Navigation successful: {result['title']}")
        
        # Test screenshot
        result = server.screenshot(name="test_example")
        if result["success"]:
            print(f"✓ Screenshot saved: {result['path']}")
        
        # Test extract
        result = server.extract("h1")
        if result["success"]:
            print(f"✓ Extracted: {result['content']}")
        
        # Get tools
        tools = server.get_tools()
        print(f"\n✓ Available tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
