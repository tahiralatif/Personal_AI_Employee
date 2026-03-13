"""Unified Social Media MCP Server for Gold Tier AI Employee.

This MCP server provides unified access to all social media platforms:
- Facebook
- Instagram  
- Twitter (X)
- LinkedIn (from Silver Tier)

Tools:
1. post_to_platform - Post to specific platform
2. post_to_all_platforms - Cross-platform posting
3. get_unified_analytics - Unified analytics across platforms
4. schedule_post - Schedule post for platform
5. get_platform_summary - Get platform-specific summary
6. generate_content - Generate social media content
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..agents.facebook_agent import facebook_agent
from ..agents.instagram_agent import instagram_agent
from ..agents.twitter_agent import twitter_agent

logger = logging.getLogger(__name__)


class SocialMediaMCPServer:
    """Unified Social Media MCP Server."""
    
    def __init__(self):
        """Initialize Social Media MCP Server."""
        self.name = "social_media_mcp"
        self.version = "1.0.0"
        self.description = "Unified social media integration for Facebook, Instagram, Twitter"
        
        # Platform agents
        self.platforms = {
            "facebook": facebook_agent,
            "instagram": instagram_agent,
            "twitter": twitter_agent
        }
        
        # Tool registry
        self.tools = self._register_tools()
        
        logger.info(f"Social Media MCP Server initialized: {self.name} v{self.version}")
    
    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register all available tools."""
        return {
            "post_to_platform": {
                "name": "post_to_platform",
                "description": "Post content to a specific social media platform",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": ["facebook", "instagram", "twitter"],
                            "description": "Target platform"
                        },
                        "content": {
                            "type": "string",
                            "description": "Post content"
                        },
                        "media_urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Media URLs"
                        },
                        "hashtags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Hashtags (Instagram)"
                        }
                    },
                    "required": ["platform", "content"]
                }
            },
            "post_to_all_platforms": {
                "name": "post_to_all_platforms",
                "description": "Post content to all platforms simultaneously",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Post content"
                        },
                        "media_urls": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "platforms": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["facebook", "instagram", "twitter"]
                            }
                        }
                    },
                    "required": ["content"]
                }
            },
            "get_unified_analytics": {
                "name": "get_unified_analytics",
                "description": "Get unified analytics across all platforms",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "period": {
                            "type": "string",
                            "enum": ["day", "week", "month"],
                            "description": "Analytics period"
                        }
                    }
                }
            },
            "schedule_post": {
                "name": "schedule_post",
                "description": "Schedule post for later publishing",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": ["facebook", "instagram", "twitter"]
                        },
                        "content": {"type": "string"},
                        "schedule_time": {"type": "string"},
                        "media_urls": {"type": "array"}
                    },
                    "required": ["platform", "content", "schedule_time"]
                }
            },
            "get_platform_summary": {
                "name": "get_platform_summary",
                "description": "Get platform-specific summary",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": ["facebook", "instagram", "twitter"]
                        },
                        "period": {
                            "type": "string",
                            "enum": ["day", "week", "month"]
                        }
                    },
                    "required": ["platform"]
                }
            },
            "generate_content": {
                "name": "generate_content",
                "description": "Generate social media content for topic",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "platform": {"type": "string"},
                        "tone": {
                            "type": "string",
                            "enum": ["professional", "friendly", "enthusiastic"]
                        }
                    },
                    "required": ["topic"]
                }
            }
        }
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return list(self.tools.values())
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name."""
        try:
            if name == "post_to_platform":
                return self._post_to_platform(**arguments)
            elif name == "post_to_all_platforms":
                return self._post_to_all_platforms(**arguments)
            elif name == "get_unified_analytics":
                return self._get_unified_analytics(**arguments)
            elif name == "schedule_post":
                return self._schedule_post(**arguments)
            elif name == "get_platform_summary":
                return self._get_platform_summary(**arguments)
            elif name == "generate_content":
                return self._generate_content(**arguments)
            else:
                return {"success": False, "error": f"Unknown tool: {name}"}
                
        except Exception as e:
            logger.error(f"Tool call failed: {name} - {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== TOOL IMPLEMENTATIONS ====================
    
    def _post_to_platform(
        self,
        platform: str,
        content: str,
        media_urls: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Post to specific platform."""
        if platform not in self.platforms:
            return {"success": False, "error": f"Unknown platform: {platform}"}
        
        agent = self.platforms[platform]
        
        if platform == "facebook":
            return agent.post_update(message=content, image_url=media_urls[0] if media_urls else None)
        elif platform == "instagram":
            return agent.post_media(
                image_url=media_urls[0] if media_urls else "",
                caption=content,
                hashtags=hashtags
            )
        elif platform == "twitter":
            return agent.post_tweet(text=content, media_urls=media_urls)
        
        return {"success": False, "error": "Platform not implemented"}
    
    def _post_to_all_platforms(
        self,
        content: str,
        media_urls: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Post to all platforms."""
        if platforms is None:
            platforms = ["facebook", "instagram", "twitter"]
        
        results = {}
        success_count = 0
        
        for platform in platforms:
            if platform in self.platforms:
                result = self._post_to_platform(platform, content, media_urls)
                results[platform] = result
                if result.get("success"):
                    success_count += 1
        
        return {
            "success": success_count > 0,
            "results": results,
            "success_count": success_count,
            "total_platforms": len(platforms)
        }
    
    def _get_unified_analytics(
        self,
        period: str = "week"
    ) -> Dict[str, Any]:
        """Get unified analytics."""
        analytics = {
            "period": period,
            "platforms": {}
        }
        
        total_engagement = 0
        
        for platform_name, agent in self.platforms.items():
            summary = agent.generate_summary(period)
            if summary.get("success"):
                analytics["platforms"][platform_name] = {
                    "engagement": summary.get("total_engagement", 0),
                    "posts": summary.get("posts_count", 0),
                    "followers": summary.get("followers_count", 0)
                }
                total_engagement += summary.get("total_engagement", 0)
        
        analytics["total_engagement"] = total_engagement
        
        return {"success": True, "analytics": analytics}
    
    def _schedule_post(
        self,
        platform: str,
        content: str,
        schedule_time: str,
        media_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Schedule post."""
        if platform not in self.platforms:
            return {"success": False, "error": f"Unknown platform: {platform}"}
        
        agent = self.platforms[platform]
        
        if hasattr(agent, "schedule_post"):
            return agent.schedule_post(content, schedule_time, media_urls[0] if media_urls else None)
        else:
            return {"success": False, "error": f"Scheduling not supported for {platform}"}
    
    def _get_platform_summary(
        self,
        platform: str,
        period: str = "week"
    ) -> Dict[str, Any]:
        """Get platform summary."""
        if platform not in self.platforms:
            return {"success": False, "error": f"Unknown platform: {platform}"}
        
        agent = self.platforms[platform]
        return agent.generate_summary(period)
    
    def _generate_content(
        self,
        topic: str,
        platform: Optional[str] = None,
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """Generate social media content."""
        # Content templates by platform
        templates = {
            "facebook": "📢 {topic}\n\nLearn more about {topic} and how it can help your business! #Business #{topic_no_space}",
            "instagram": "✨ {topic}\n\nDouble tap if you agree! 💙 #{topic_no_space} #Business #Inspiration",
            "twitter": "Excited to share insights about {topic}! 🚀 Read more: [link] #{topic_no_space} #Business"
        }
        
        topic_no_space = topic.replace(" ", "")
        
        if platform and platform in templates:
            content = templates[platform].format(
                topic=topic,
                topic_no_space=topic_no_space
            )
            
            if tone == "friendly":
                content += " 😊"
            elif tone == "enthusiastic":
                content += " 🔥🎉"
            
            return {
                "success": True,
                "content": content,
                "platform": platform,
                "tone": tone
            }
        else:
            # Generate for all platforms
            content = {}
            for plat, template in templates.items():
                content[plat] = template.format(
                    topic=topic,
                    topic_no_space=topic_no_space
                )
            
            return {
                "success": True,
                "content": content,
                "topic": topic,
                "tone": tone
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get server health status."""
        status = {
            "name": self.name,
            "version": self.version,
            "platforms": {}
        }
        
        for platform_name, agent in self.platforms.items():
            agent_status = agent.get_agent_status()
            status["platforms"][platform_name] = {
                "connected": agent_status.get(f"{platform_name}_connected", False),
                "success_rate": agent_status["statistics"]["success_rate"]
            }
        
        return status


# Global MCP server instance
social_media_mcp = SocialMediaMCPServer()