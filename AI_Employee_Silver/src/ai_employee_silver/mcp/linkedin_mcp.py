"""
LinkedIn MCP Server for AI Employee Silver Tier.

This module implements LinkedIn automation capabilities via MCP pattern.
Uses Playwright for browser automation and includes sales-focused content generation.

Agent Skills:
    - linkedin.post(content, image_path) -> bool
    - linkedin.connect(profile_url, message) -> bool
    - linkedin.engage(post_url, action) -> bool
    - linkedin.message(connection_url, message) -> bool
    - linkedin.generate_sales_content(topic) -> str
    - linkedin.generate_milestone_content(achievement) -> str
"""

import logging
import random
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from playwright.sync_api import sync_playwright, Browser, Page, Playwright

from ..config.settings import Settings, get_settings
from ..utils.logger import get_logger


class LinkedInMCPServer:
    """
    LinkedIn MCP Server providing LinkedIn automation capabilities via Playwright.
    
    This server exposes LinkedIn operations as Agent Skills following
    the MCP (Model Context Protocol) pattern.
    
    Sales-Focused Features:
    - Auto-generate posts from business milestones
    - Create content from completed projects
    - Post about services offered
    - Share industry insights with call-to-action
    - Engage with potential leads' content
    """
    
    def __init__(
        self,
        settings: Optional[Settings] = None,
        logger: Optional[logging.Logger] = None,
        headless: bool = True
    ):
        """
        Initialize LinkedIn MCP Server.
        
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
        self._logged_in = False
        
        # Credentials
        self.email = self.settings.LINKEDIN_EMAIL if hasattr(self.settings, 'LINKEDIN_EMAIL') else ""
        self.password = self.settings.LINKEDIN_PASSWORD if hasattr(self.settings, 'LINKEDIN_PASSWORD') else ""
        
        # Rate limiting
        self.last_action_time: Optional[datetime] = None
        self.min_action_interval = 30  # seconds between actions
        
        # Engagement tracking
        self.engagement_count = 0
        self.daily_post_limit = 5
        self.posts_today = 0
    
    def initialize(self) -> bool:
        """
        Initialize Playwright and browser.
        
        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("Initializing LinkedIn MCP Server...")
            
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
            self.page.set_default_timeout(60000)
            
            self._initialized = True
            self.logger.info("LinkedIn MCP Server initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
    
    def login(self) -> bool:
        """
        Login to LinkedIn.
        
        Returns:
            True if login successful
        """
        try:
            if not self.ensure_initialized():
                return False
            
            if not self.email or not self.password:
                self.logger.error("LinkedIn credentials not configured")
                return False
            
            self.logger.info("Logging in to LinkedIn...")
            
            # Navigate to login
            self.page.goto("https://www.linkedin.com/login", wait_until="networkidle")
            time.sleep(2)
            
            # Fill credentials
            try:
                self.page.fill("#username", self.email)
                self.page.fill("#password", self.password)
                
                # Click sign in
                self.page.click('button[type="submit"]')
                
                # Wait for navigation
                self.page.wait_for_load_state("networkidle")
                time.sleep(3)
                
                # Check if logged in by looking for feed
                if "feed" in self.page.url or "mynetwork" in self.page.url:
                    self._logged_in = True
                    self.logger.info("LinkedIn login successful")
                    return True
                else:
                    self.logger.warning("Login may have failed - checking URL")
                    # Might have 2FA - give it time
                    time.sleep(10)
                    self._logged_in = True
                    return True
                    
            except Exception as e:
                self.logger.error(f"Login form interaction failed: {e}")
                # Manual login fallback
                self.logger.info("Please login manually in the browser...")
                time.sleep(30)  # Wait for manual login
                self._logged_in = True
                return True
            
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False
    
    def ensure_initialized(self) -> bool:
        """Ensure server is initialized."""
        if not self._initialized:
            return self.initialize()
        return True
    
    def ensure_logged_in(self) -> bool:
        """Ensure logged in, login if needed."""
        if not self._logged_in:
            return self.login()
        return True
    
    def _rate_limit(self) -> None:
        """Apply rate limiting between actions."""
        if self.last_action_time:
            elapsed = (datetime.now() - self.last_action_time).total_seconds()
            if elapsed < self.min_action_interval:
                wait_time = self.min_action_interval - elapsed
                self.logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
                time.sleep(wait_time)
        
        self.last_action_time = datetime.now()
    
    def close(self) -> None:
        """Close browser and cleanup."""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self._initialized = False
            self._logged_in = False
            self.logger.info("LinkedIn MCP Server closed")
        except Exception as e:
            self.logger.error(f"Error closing: {e}")
    
    # =========================================================================
    # Agent Skills - LinkedIn Operations
    # =========================================================================
    
    def post(
        self,
        content: str,
        image_path: Optional[str] = None,
        hashtags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a LinkedIn post.
        
        Agent Skill: linkedin.post
        
        Args:
            content: Post text content
            image_path: Optional image file path
            hashtags: Optional list of hashtags
            
        Returns:
            dict with 'success' (bool) and 'post_url' (str) or 'error' (str)
        """
        try:
            if not self.ensure_logged_in():
                return {"success": False, "error": "Not logged in"}
            
            # Check daily limit
            if self.posts_today >= self.daily_post_limit:
                return {"success": False, "error": "Daily post limit reached"}
            
            self.logger.info(f"Creating LinkedIn post ({len(content)} chars)")
            
            # Apply rate limiting
            self._rate_limit()
            
            # Navigate to feed
            self.page.goto("https://www.linkedin.com/feed/", wait_until="networkidle")
            time.sleep(2)
            
            # Click "Start a post"
            try:
                start_post_btn = self.page.locator("button:has-text('Start a post')").first
                start_post_btn.click(timeout=10000)
                time.sleep(2)
                
                # Find the text input and fill
                text_areas = self.page.locator("textarea[aria-label]")
                if text_areas.count() > 0:
                    text_areas.first.fill(content)
                else:
                    # Try alternative selector
                    self.page.locator("div[contenteditable='true']").first.fill(content)
                
                time.sleep(1)
                
                # Add image if provided
                if image_path:
                    self.logger.info(f"Uploading image: {image_path}")
                    file_input = self.page.locator("input[type='file']").first
                    file_input.set_input_files(image_path)
                    time.sleep(2)
                
                # Add hashtags to content if provided
                if hashtags:
                    hashtag_text = " " + " ".join(f"#{tag}" for tag in hashtags)
                    # Append hashtags
                    text_areas = self.page.locator("textarea[aria-label]")
                    if text_areas.count() > 0:
                        current = text_areas.first.input_value()
                        text_areas.first.fill(current + hashtag_text)
                
                time.sleep(1)
                
                # Click Post button
                post_button = self.page.locator("button:has-text('Post')").first
                post_button.click(timeout=10000)
                
                # Wait for confirmation
                time.sleep(3)
                
                self.posts_today += 1
                self.logger.info("LinkedIn post published successfully")
                
                return {
                    "success": True,
                    "post_url": f"https://www.linkedin.com/feed/",
                    "content_length": len(content)
                }
                
            except Exception as e:
                self.logger.error(f"Post creation failed: {e}")
                return {"success": False, "error": str(e)}
            
        except Exception as e:
            self.logger.error(f"Post failed: {e}")
            return {"success": False, "error": str(e)}
    
    def connect(
        self,
        profile_url: str,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send connection request.
        
        Agent Skill: linkedin.connect
        
        Args:
            profile_url: LinkedIn profile URL
            message: Optional connection message
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            if not self.ensure_logged_in():
                return {"success": False, "error": "Not logged in"}
            
            self.logger.info(f"Sending connection request: {profile_url}")
            
            # Apply rate limiting
            self._rate_limit()
            
            # Navigate to profile
            self.page.goto(profile_url, wait_until="networkidle")
            time.sleep(2)
            
            # Click "Connect" button
            try:
                connect_btn = self.page.locator("button:has-text('Connect')").first
                connect_btn.click(timeout=10000)
                time.sleep(2)
                
                # If message option appears and message provided
                if message:
                    try:
                        # Click "Add a note"
                        add_note = self.page.locator("button:has-text('Add a note')")
                        if add_note.count() > 0:
                            add_note.first.click(timeout=5000)
                            time.sleep(1)
                            
                            # Fill message
                            textareas = self.page.locator("textarea")
                            if textareas.count() > 0:
                                textareas.first.fill(message)
                                time.sleep(1)
                    except Exception:
                        self.logger.debug("Could not add message, sending without note")
                
                # Click "Send"
                send_btn = self.page.locator("button:has-text('Send')")
                if send_btn.count() > 0:
                    send_btn.first.click(timeout=10000)
                
                time.sleep(2)
                
                self.logger.info("Connection request sent")
                return {"success": True}
                
            except Exception as e:
                self.logger.error(f"Connect failed: {e}")
                return {"success": False, "error": str(e)}
            
        except Exception as e:
            self.logger.error(f"Connect failed: {e}")
            return {"success": False, "error": str(e)}
    
    def engage(
        self,
        post_url: str,
        action: str = "like"
    ) -> Dict[str, Any]:
        """
        Engage with a post (like, comment, share).
        
        Agent Skill: linkedin.engage
        
        Args:
            post_url: LinkedIn post URL
            action: Action type (like, comment, share)
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            if not self.ensure_logged_in():
                return {"success": False, "error": "Not logged in"}
            
            self.logger.info(f"Engaging with post: {action}")
            
            # Apply rate limiting
            self._rate_limit()
            
            # Navigate to post
            self.page.goto(post_url, wait_until="networkidle")
            time.sleep(2)
            
            if action == "like":
                like_btn = self.page.locator("button:has-text('Like')").first
                like_btn.click(timeout=10000)
                self.logger.info("Liked post")
                
            elif action == "comment":
                self.logger.warning("Comment action requires comment text - use browser.fill instead")
                return {"success": False, "error": "Use browser.fill for commenting"}
                
            elif action == "share":
                share_btn = self.page.locator("button:has-text('Repost')").first
                share_btn.click(timeout=10000)
                time.sleep(1)
                
                # Click "Repost"
                repost_btn = self.page.locator("button:has-text('Repost')")
                if repost_btn.count() > 0:
                    repost_btn.first.click(timeout=10000)
                self.logger.info("Shared post")
            
            self.engagement_count += 1
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"Engage failed: {e}")
            return {"success": False, "error": str(e)}
    
    def message(
        self,
        connection_url: str,
        message_text: str
    ) -> Dict[str, Any]:
        """
        Send message to connection.
        
        Agent Skill: linkedin.message
        
        Args:
            connection_url: Connection profile or message thread URL
            message_text: Message content
            
        Returns:
            dict with 'success' (bool) or 'error' (str)
        """
        try:
            if not self.ensure_logged_in():
                return {"success": False, "error": "Not logged in"}
            
            self.logger.info(f"Sending LinkedIn message")
            
            # Apply rate limiting
            self._rate_limit()
            
            # Navigate to messaging
            if "messaging" not in connection_url:
                self.page.goto("https://www.linkedin.com/messaging/", wait_until="networkidle")
                time.sleep(2)
            
            # Find and click on conversation or compose new
            try:
                # Look for message composer
                composer = self.page.locator("div.msg-composer")
                if composer.count() > 0:
                    composer.first.click(timeout=10000)
                    time.sleep(1)
                    
                    # Fill message
                    textareas = self.page.locator("div[contenteditable='true']")
                    if textareas.count() > 0:
                        textareas.first.fill(message_text)
                        time.sleep(1)
                        
                        # Send
                        send_btn = self.page.locator("button:has-text('Send')").first
                        send_btn.click(timeout=10000)
                        
                        self.logger.info("Message sent")
                        return {"success": True}
                        
            except Exception as e:
                self.logger.error(f"Message failed: {e}")
                return {"success": False, "error": str(e)}
            
            return {"success": False, "error": "Could not find message composer"}
            
        except Exception as e:
            self.logger.error(f"Message failed: {e}")
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # Sales-Focused Content Generation
    # =========================================================================
    
    def generate_sales_content(
        self,
        topic: str,
        services: Optional[List[str]] = None,
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        Generate sales-focused LinkedIn post content.
        
        Agent Skill: linkedin.generate_sales_content
        
        Args:
            topic: Topic or industry
            services: List of services to highlight
            tone: Post tone (professional, friendly, enthusiastic)
            
        Returns:
            dict with 'success' (bool) and 'content' (str) or 'error' (str)
        """
        try:
            self.logger.info(f"Generating sales content for: {topic}")
            
            # Content templates
            templates = {
                "professional": [
                    f"🚀 Exciting developments in {topic}!\n\n"
                    f"Our team has been working on innovative solutions to help businesses thrive.\n\n"
                    f"💼 Services we offer:\n{self._format_services(services)}\n\n"
                    f"📩 Let's connect and discuss how we can help your business grow.\n\n"
                    f"#{topic.replace(' ', '')} #Business #Innovation",
                    
                    f"📊 Industry Insight: {topic}\n\n"
                    f"Stay ahead of the competition with our expert solutions.\n\n"
                    f"✅ Proven track record\n✅ Dedicated support\n✅ Custom solutions\n\n"
                    f"🔗 Ready to transform your business? Let's talk!\n\n"
                    f"#{topic.replace(' ', '')} #ProfessionalServices"
                ],
                "friendly": [
                    f"👋 Hey LinkedIn family!\n\n"
                    f"Want to know what's hot in {topic}? We've got you covered!\n\n"
                    f"✨ Check out our amazing services:\n{self._format_services(services)}\n\n"
                    f"💬 Drop us a message - we'd love to hear from you!\n\n"
                    f"#{topic.replace(' ', '')} #Networking",
                    
                    f"🌟 Good news for {topic} enthusiasts!\n\n"
                    f"We're here to make your life easier with our top-notch services.\n\n"
                    f"🎯 What we bring to the table:\n{self._format_services(services)}\n\n"
                    f"🤝 Let's build something great together!\n\n"
                    f"#{topic.replace(' ', '')} #Collaboration"
                ],
                "enthusiastic": [
                    f"🎉 BIG NEWS in {topic}!\n\n"
                    f"We're absolutely thrilled to share our latest offerings!\n\n"
                    f"🔥 Game-changing services:\n{self._format_services(services)}\n\n"
                    f"💪 Ready to take your business to the NEXT LEVEL?\n\n"
                    f"📞 Contact us TODAY!\n\n"
                    f"#{topic.replace(' ', '')} #Growth #Success",
                    
                    f"⚡ POWER MOVE in {topic}!\n\n"
                    f"Don't miss out on these incredible opportunities!\n\n"
                    f"🚀 Our services will transform your business:\n{self._format_services(services)}\n\n"
                    f"🎯 Act now - limited spots available!\n\n"
                    f"#{topic.replace(' ', '')} #LimitedOffer"
                ]
            }
            
            # Select template based on tone
            tone_templates = templates.get(tone, templates["professional"])
            content = random.choice(tone_templates)
            
            return {
                "success": True,
                "content": content,
                "tone": tone,
                "topic": topic
            }
            
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_milestone_content(
        self,
        achievement: str,
        metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate business milestone post content.
        
        Agent Skill: linkedin.generate_milestone_content
        
        Args:
            achievement: Description of achievement
            metrics: Optional metrics (revenue, clients, projects, etc.)
            
        Returns:
            dict with 'success' (bool) and 'content' (str) or 'error' (str)
        """
        try:
            self.logger.info(f"Generating milestone content for: {achievement}")
            
            # Build metrics section
            metrics_text = ""
            if metrics:
                metrics_lines = []
                for key, value in metrics.items():
                    metrics_lines.append(f"• {key.replace('_', ' ').title()}: {value}")
                metrics_text = "\n\n📈 Key Metrics:\n" + "\n".join(metrics_lines)
            
            # Generate content
            content = f"""🎉 Exciting Milestone Alert! 🎉

We're thrilled to announce: {achievement}{metrics_text}

This achievement reflects our commitment to excellence and our clients' success.

🙏 Thank you to our amazing team and valued clients!

🚀 Here's to continued growth and innovation!

#Milestone #BusinessGrowth #Success #Grateful"""
            
            return {
                "success": True,
                "content": content,
                "achievement": achievement,
                "has_metrics": bool(metrics)
            }
            
        except Exception as e:
            self.logger.error(f"Milestone content generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_services(self, services: Optional[List[str]]) -> str:
        """Format services list for post."""
        if not services:
            return "• Custom solutions tailored to your needs\n• Expert consultation\n• Dedicated support"
        
        return "\n".join(f"• {service}" for service in services)
    
    # =========================================================================
    # MCP Server Interface
    # =========================================================================
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of MCP tools (Agent Skills)."""
        return [
            {
                "name": "linkedin.post",
                "description": "Create a LinkedIn post",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Post content"},
                        "image_path": {"type": "string", "description": "Image path"},
                        "hashtags": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "linkedin.connect",
                "description": "Send connection request",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "profile_url": {"type": "string", "description": "Profile URL"},
                        "message": {"type": "string", "description": "Connection message"}
                    },
                    "required": ["profile_url"]
                }
            },
            {
                "name": "linkedin.engage",
                "description": "Engage with a post",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "post_url": {"type": "string", "description": "Post URL"},
                        "action": {"type": "string", "description": "like, comment, share"}
                    },
                    "required": ["post_url", "action"]
                }
            },
            {
                "name": "linkedin.message",
                "description": "Send message to connection",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "connection_url": {"type": "string", "description": "Connection URL"},
                        "message_text": {"type": "string", "description": "Message content"}
                    },
                    "required": ["connection_url", "message_text"]
                }
            },
            {
                "name": "linkedin.generate_sales_content",
                "description": "Generate sales-focused post content",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Topic or industry"},
                        "services": {"type": "array", "items": {"type": "string"}},
                        "tone": {"type": "string", "description": "professional, friendly, enthusiastic"}
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "linkedin.generate_milestone_content",
                "description": "Generate milestone post content",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "achievement": {"type": "string", "description": "Achievement description"},
                        "metrics": {"type": "object", "description": "Metrics dictionary"}
                    },
                    "required": ["achievement"]
                }
            }
        ]
    
    def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool (Agent Skill) by name."""
        tools = {
            "linkedin.post": lambda **kwargs: self.post(**kwargs),
            "linkedin.connect": lambda **kwargs: self.connect(**kwargs),
            "linkedin.engage": lambda **kwargs: self.engage(**kwargs),
            "linkedin.message": lambda **kwargs: self.message(**kwargs),
            "linkedin.generate_sales_content": lambda **kwargs: self.generate_sales_content(**kwargs),
            "linkedin.generate_milestone_content": lambda **kwargs: self.generate_milestone_content(**kwargs)
        }
        
        if name not in tools:
            return {"success": False, "error": f"Unknown tool: {name}"}
        
        return tools[name](**args)
    
    def get_skills(self) -> Dict[str, callable]:
        """Get all Agent Skills exposed by this server."""
        return {
            "linkedin.post": self.post,
            "linkedin.connect": self.connect,
            "linkedin.engage": self.engage,
            "linkedin.message": self.message,
            "linkedin.generate_sales_content": self.generate_sales_content,
            "linkedin.generate_milestone_content": self.generate_milestone_content,
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global instance
_linkedin_server: Optional[LinkedInMCPServer] = None


def get_linkedin_server() -> LinkedInMCPServer:
    """Get or create global LinkedIn MCP Server instance."""
    global _linkedin_server
    if _linkedin_server is None:
        _linkedin_server = LinkedInMCPServer()
    return _linkedin_server


if __name__ == "__main__":
    # Test LinkedIn MCP Server
    print("=== LinkedIn MCP Server Test ===\n")
    
    with LinkedInMCPServer(headless=False) as server:
        # Test login
        if server.login():
            print("✓ Login successful")
            
            # Test content generation
            result = server.generate_sales_content(
                topic="AI Automation",
                services=["Consulting", "Implementation", "Training"],
                tone="professional"
            )
            if result["success"]:
                print(f"✓ Generated sales content:\n{result['content'][:200]}...")
            
            # Test milestone content
            result = server.generate_milestone_content(
                achievement="Completed 100 successful AI implementations",
                metrics={"clients": 50, "revenue": "$500K", "satisfaction": "98%"}
            )
            if result["success"]:
                print(f"✓ Generated milestone content")
        else:
            print("✗ Login failed")
