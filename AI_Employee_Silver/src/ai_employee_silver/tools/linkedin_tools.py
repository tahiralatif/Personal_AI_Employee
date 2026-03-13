"""
LinkedIn Tools for AI Employee System

Tools for LinkedIn Agent to interact with LinkedIn API.
"""

import os
import requests
from datetime import datetime
from pathlib import Path
from agents import function_tool


@function_tool()
def read_scheduled_posts() -> str:
    """
    Read scheduled posts from Plans folder.
    
    Returns:
        List of scheduled LinkedIn posts
    """
    try:
        vault_path = Path(os.getenv("VAULT_PATH")).expanduser()
        plans_path = vault_path / "Plans"
        
        if not plans_path.exists():
            return "No Plans folder found."
        
        posts = []
        for post_file in plans_path.glob("*.md"):
            content = post_file.read_text(encoding="utf-8")
            
            # Check if it's a LinkedIn post
            if "type: linkedin_post" in content:
                # Extract scheduled time if available
                scheduled_time = "Not specified"
                if "scheduled_time:" in content:
                    for line in content.split("\n"):
                        if "scheduled_time:" in line:
                            scheduled_time = line.split(":")[1].strip()
                            break
                
                posts.append({
                    "file": post_file.name,
                    "scheduled_time": scheduled_time,
                    "content": content[:300] + "..." if len(content) > 300 else content
                })
        
        if not posts:
            return "No scheduled LinkedIn posts found."
        
        result = f"Found {len(posts)} scheduled LinkedIn posts:\n\n"
        for p in posts:
            result += f"""
---
File: {p['file']}
Scheduled: {p['scheduled_time']}
Content: {p['content']}
---
"""
        
        return result
    
    except Exception as e:
        return f"Error reading scheduled posts: {str(e)}"


@function_tool()
def publish_linkedin_post(post_content: str, image_url: str = None) -> str:
    """
    Publish post to LinkedIn.
    
    Args:
        post_content: Post text content (max 1300 characters)
        image_url: Optional image URL to include
    
    Returns:
        Post URL if published successfully
    """
    try:
        access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        organization_id = os.getenv("LINKEDIN_ORGANIZATION_ID")
        
        if not access_token:
            return "Error: LinkedIn access token not configured"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }
        
        # Build payload
        payload = {
            "owner": f"urn:li:organization:{organization_id}" if organization_id else "urn:li:person:me",
            "subject": "LinkedIn Post",
            "text": {
                "text": post_content[:1300]  # LinkedIn character limit
            },
            "visibility": "PUBLIC"
        }
        
        # Add image if provided
        if image_url:
            payload["content"] = {
                "contentEntities": [
                    {
                        "entityLocation": image_url,
                        "thumbnails": [
                            {
                                "resolvedUrl": image_url
                            }
                        ]
                    }
                ],
                "title": "Post Image"
            }
        
        # Publish post
        response = requests.post(
            "https://api.linkedin.com/v2/shares",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            post_data = response.json()
            post_id = post_data.get("id", "Unknown")
            permalink = post_data.get("permalink", f"https://www.linkedin.com/feed/update/{post_id}")
            return f"✓ Post published successfully!\n\nID: {post_id}\nURL: {permalink}"
        else:
            return f"✗ Failed to publish post: {response.status_code}\n{response.text}"
    
    except Exception as e:
        return f"✗ Error publishing LinkedIn post: {str(e)}"


@function_tool()
def get_post_engagement(post_id: str) -> str:
    """
    Get engagement metrics for a LinkedIn post.
    
    Args:
        post_id: LinkedIn post ID
    
    Returns:
        Engagement metrics (likes, comments, shares)
    """
    try:
        access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        
        if not access_token:
            return "Error: LinkedIn access token not configured"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        # Get engagement metrics
        response = requests.get(
            f"https://api.linkedin.com/v2/actions?q=actionSummary&values=(actionType,total)&object=urn:li:share:{post_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            metrics = {"likes": 0, "comments": 0, "shares": 0}
            
            for element in data.get("elements", []):
                action_type = element.get("actionType", "")
                count = element.get("total", {}).get("count", 0)
                
                if action_type == "LIKE":
                    metrics["likes"] = count
                elif action_type == "COMMENT":
                    metrics["comments"] = count
                elif action_type == "SHARE":
                    metrics["shares"] = count
            
            result = f"Engagement metrics for post {post_id}:\n\n"
            result += f"👍 Likes: {metrics['likes']}\n"
            result += f"💬 Comments: {metrics['comments']}\n"
            result += f"🔄 Shares: {metrics['shares']}\n"
            
            return result
        else:
            return f"Failed to get engagement: {response.status_code}"
    
    except Exception as e:
        return f"Error getting engagement: {str(e)}"


@function_tool()
def move_post_to_done(post_file: str) -> str:
    """
    Move published post file to Done folder.
    
    Args:
        post_file: Name of post file in Plans folder
    
    Returns:
        Success or error message
    """
    try:
        vault_path = Path(os.getenv("VAULT_PATH")).expanduser()
        plans_path = vault_path / "Plans"
        done_path = vault_path / "Done"
        
        done_path.mkdir(parents=True, exist_ok=True)
        
        src_path = plans_path / post_file
        if not src_path.exists():
            return f"Error: Post file not found: {post_file}"
        
        # Add completion timestamp
        content = src_path.read_text(encoding="utf-8")
        content += f"\n\n---\nPublished: {datetime.now().isoformat()}\nStatus: Completed\n"
        
        dst_path = done_path / post_file
        dst_path.write_text(content, encoding="utf-8")
        src_path.unlink()
        
        return f"✓ Post moved to Done: {post_file}"
    
    except Exception as e:
        return f"✗ Error moving post: {str(e)}"
