"""
Enhanced File System Watcher for AI Employee Silver Tier.

This watcher monitors the Inbox folder for new files and creates action files.
It inherits from BaseWatcher and provides enhanced file type support.

Agent Skills:
    - filesystem.check_updates(): Check for new files
    - filesystem.create_action_file(): Create action file for file
    - filesystem.mark_processed(): Mark file as processed
"""

import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from .base_watcher import BaseWatcher
from ..config.settings import get_settings
from ..utils.logger import get_logger


# Supported file types with descriptions
SUPPORTED_FILE_TYPES = {
    # Documents
    '.pdf': 'PDF Document',
    '.doc': 'Word Document',
    '.docx': 'Word Document',
    '.txt': 'Text File',
    '.md': 'Markdown File',
    '.rtf': 'Rich Text File',
    
    # Spreadsheets
    '.xls': 'Excel Spreadsheet',
    '.xlsx': 'Excel Spreadsheet',
    '.csv': 'CSV File',
    
    # Presentations
    '.ppt': 'PowerPoint Presentation',
    '.pptx': 'PowerPoint Presentation',
    
    # Images
    '.jpg': 'JPEG Image',
    '.jpeg': 'JPEG Image',
    '.png': 'PNG Image',
    '.gif': 'GIF Image',
    '.webp': 'WebP Image',
    
    # Archives
    '.zip': 'ZIP Archive',
    '.rar': 'RAR Archive',
    '.7z': '7-Zip Archive',
    '.tar': 'TAR Archive',
    '.gz': 'GZIP Archive',
    
    # Code/Config
    '.py': 'Python Script',
    '.js': 'JavaScript File',
    '.ts': 'TypeScript File',
    '.json': 'JSON File',
    '.xml': 'XML File',
    '.yaml': 'YAML File',
    '.yml': 'YAML File',
    '.toml': 'TOML File',
    '.ini': 'INI Configuration',
    
    # Other
    '.html': 'HTML File',
    '.htm': 'HTML File',
    '.css': 'CSS File',
    '.sql': 'SQL File',
    '.log': 'Log File',
}

# Security scan extensions (potentially dangerous)
DANGEROUS_EXTENSIONS = {'.exe', '.bat', '.cmd', '.scr', '.vbs', '.js', '.msi'}


class FileDropHandler(FileSystemEventHandler):
    """
    Event handler for file system watcher.
    
    Captures file creation events and queues them for processing.
    """
    
    def __init__(self, watcher: 'FileSystemWatcher'):
        """
        Initialize file drop handler.
        
        Args:
            watcher: Parent FileSystemWatcher instance
        """
        super().__init__()
        self.watcher = watcher
        self.logger = watcher.logger
    
    def on_created(self, event):
        """
        Handle file creation event.
        
        Args:
            event: File system event
        """
        if isinstance(event, FileCreatedEvent) and not event.is_directory:
            file_path = Path(event.src_path)
            
            # Skip hidden files and temporary files
            if file_path.name.startswith('.') or file_path.suffix == '.tmp':
                return
            
            # Skip if file is still being written
            if not self._is_file_ready(file_path):
                return
            
            self.logger.info(f"New file detected: {file_path.name}")
            self.watcher.process_file(file_path)
    
    def _is_file_ready(self, file_path: Path) -> bool:
        """
        Check if file is ready for processing (not being written).
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is ready
        """
        try:
            # Try to open file for reading
            with open(file_path, 'rb') as f:
                f.read(1)
            return True
        except (IOError, PermissionError):
            self.logger.debug(f"File not ready: {file_path.name}")
            return False


class FileSystemWatcher(BaseWatcher):
    """
    Enhanced file system watcher implementing the BaseWatcher interface.
    
    Monitors the Inbox folder for new files and creates action files.
    Supports multiple file types with content preview and security scanning.
    """
    
    def __init__(
        self,
        vault_path: str | Path,
        check_interval: int = 1,  # 1 second for event-driven
        name: str = "FileSystemWatcher",
        inbox_path: Optional[str] = None
    ):
        """
        Initialize File System Watcher.
        
        Args:
            vault_path: Path to the AI Employee vault
            check_interval: Seconds between checks (default: 1 for event-driven)
            name: Watcher name
            inbox_path: Path to Inbox folder (default: vault/Inbox)
        """
        super().__init__(vault_path, check_interval, name)
        
        # Set up inbox path
        self.inbox_path = Path(inbox_path) if inbox_path else self.vault_path / "Inbox"
        self.inbox_path.mkdir(parents=True, exist_ok=True)
        
        # File tracking
        self.processed_hashes: set[str] = set()
        
        # Security settings
        self.scan_for_security = True
        self.quarantine_dangerous = True
        self.quarantine_path = self.vault_path / "Quarantine"
        
        # Set up watchdog observer
        self.observer = Observer()
        self.handler = FileDropHandler(self)
        self.observer.schedule(self.handler, str(self.inbox_path), recursive=False)
    
    def start(self) -> None:
        """Start the file system watcher."""
        try:
            self.observer.start()
            self.is_running = True
            self.logger.info(f"File system watcher started, monitoring: {self.inbox_path}")
        except Exception as e:
            self.logger.error(f"Failed to start file system watcher: {e}")
    
    def stop(self) -> None:
        """Stop the file system watcher."""
        try:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            self.logger.info("File system watcher stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop file system watcher: {e}")
    
    def check_for_updates(self) -> list[dict[str, Any]]:
        """
        Check for new files in Inbox.
        
        Note: This is event-driven, so we don't actively poll.
        The handler processes files as they appear.
        
        Returns:
            List of new file items (usually empty for event-driven)
        """
        # Event-driven watcher doesn't need to poll
        # Files are processed as they arrive via on_created event
        return []
    
    def process_file(self, file_path: Path) -> Optional[Path]:
        """
        Process a new file and create action file.
        
        Args:
            file_path: Path to the new file
            
        Returns:
            Path to created action file, or None
        """
        try:
            # Check if file already processed
            file_hash = self._calculate_hash(file_path)
            if file_hash in self.processed_hashes:
                self.logger.debug(f"File already processed: {file_path.name}")
                return None
            
            # Security scan
            if self.scan_for_security:
                if not self._security_scan(file_path):
                    self.logger.warning(f"Security scan failed: {file_path.name}")
                    if self.quarantine_dangerous:
                        self._quarantine_file(file_path)
                    return None
            
            # Create item dict
            item = {
                'id': file_hash[:16],  # Use hash as ID
                'type': 'file_drop',
                'source': 'FileSystem',
                'data': {
                    'file_path': str(file_path),
                    'filename': file_path.name,
                    'extension': file_path.suffix.lower(),
                    'size': file_path.stat().st_size,
                    'file_type': self._get_file_type(file_path),
                    'hash': file_hash
                }
            }
            
            # Parse and create action file
            parsed = self.parse_item(item)
            action_file = self.create_action_file(parsed)
            
            # Mark as processed
            self.mark_processed(item['id'])
            
            return action_file
            
        except Exception as e:
            self.logger.error(f"Error processing file: {e}")
            return None
    
    def parse_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """
        Parse file item into structured format.
        
        Args:
            item: File item from check_for_updates
            
        Returns:
            Structured file data
        """
        data = item['data']
        
        return {
            'id': item['id'],
            'type': 'file_drop',
            'source': 'FileSystem',
            'filename': data['filename'],
            'extension': data['extension'],
            'file_type': data['file_type'],
            'size': data['size'],
            'size_formatted': self._format_size(data['size']),
            'hash': data['hash'],
            'received': datetime.now().isoformat(),
            'priority': self._classify_priority(data),
            'content_preview': self._generate_content_preview(data['file_path'])
        }
    
    def create_action_file(self, item: dict[str, Any]) -> Path:
        """
        Create action file for dropped file in Needs_Action/FileDrop/.
        
        Args:
            item: Parsed file data
            
        Returns:
            Path to created action file
        """
        try:
            # Ensure directory exists
            filedrop_dir = self.needs_action / "FileDrop"
            filedrop_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = self._sanitize_string(item['filename'])[:50]
            filename = f"FILE_{timestamp}_{safe_filename}.md"
            filepath = filedrop_dir / filename
            
            # Build content
            content = self._build_action_file_content(item)
            
            # Write file
            filepath.write_text(content, encoding='utf-8')
            
            self.logger.info(f"Created action file: {filename}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            fallback_path = self.needs_action / "FileDrop" / f"FILE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            fallback_path.write_text(f"# Error creating action file\n\nError: {e}\n", encoding='utf-8')
            return fallback_path
    
    def _build_action_file_content(self, item: dict[str, Any]) -> str:
        """
        Build markdown content for action file.
        
        Args:
            item: Parsed file data
            
        Returns:
            Markdown content string
        """
        # YAML frontmatter
        frontmatter = f"""---
type: file_drop
source: FileSystem
id: {item['id']}
filename: {item['filename']}
file_type: {item['file_type']}
size: {item['size_formatted']}
received: {item['received']}
priority: {item['priority']}
status: pending
---

# File Dropped: {item['filename']}

## File Details
- **Type:** {item['file_type']}
- **Size:** {item['size_formatted']}
- **Received:** {item['received']}
- **Priority:** {item['priority'].upper()}
- **SHA256 Hash:** `{item['hash'][:32]}...`

## Content Preview
{item['content_preview']}

## Suggested Actions
- [ ] Review file content
- [ ] {self._suggest_action(item)}
- [ ] Create plan if needed
- [ ] Move to /Done/ when complete

## File Location
- **Original:** `{item['filename']}` in Inbox/
- **Action File:** `{self.needs_action / 'FileDrop'}`

---
*Generated by AI Employee Silver Tier - File System Watcher*
"""
        return frontmatter
    
    def _suggest_action(self, item: dict[str, Any]) -> str:
        """Suggest action based on file type."""
        ext = item.get('extension', '').lower()
        
        if ext in ['.pdf', '.doc', '.docx', '.txt', '.md']:
            return "Read and extract key information"
        elif ext in ['.xls', '.xlsx', '.csv']:
            return "Analyze data and create summary"
        elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
            return "Review image and add description"
        elif ext in ['.zip', '.rar', '.7z']:
            return "Extract and review contents"
        elif ext in ['.py', '.js', '.ts']:
            return "Review code and document purpose"
        else:
            return "Categorize and process"
    
    def _classify_priority(self, data: dict[str, Any]) -> str:
        """
        Classify file priority based on type and size.
        
        Args:
            data: File data dictionary
            
        Returns:
            Priority level: 'high', 'medium', or 'low'
        """
        ext = data.get('extension', '').lower()
        size = data.get('size', 0)
        
        # High priority: documents, spreadsheets
        if ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv']:
            return 'high'
        
        # Medium priority: code, config files
        if ext in ['.py', '.js', '.ts', '.json', '.yaml', '.yml']:
            return 'medium'
        
        # Low priority: images, archives
        return 'low'
    
    def _get_file_type(self, file_path: Path) -> str:
        """
        Get human-readable file type description.
        
        Args:
            file_path: Path to file
            
        Returns:
            File type description
        """
        ext = file_path.suffix.lower()
        return SUPPORTED_FILE_TYPES.get(ext, f"File ({ext})")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def _calculate_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash hex string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _security_scan(self, file_path: Path) -> bool:
        """
        Perform basic security scan on file.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file passes security scan
        """
        ext = file_path.suffix.lower()
        
        # Check for dangerous extensions
        if ext in DANGEROUS_EXTENSIONS:
            self.logger.warning(f"Dangerous file type detected: {ext}")
            return False
        
        # Check file size (max 100MB)
        max_size = 100 * 1024 * 1024
        if file_path.stat().st_size > max_size:
            self.logger.warning(f"File too large: {file_path.stat().st_size} bytes")
            return False
        
        return True
    
    def _quarantine_file(self, file_path: Path) -> None:
        """
        Move dangerous file to quarantine.
        
        Args:
            file_path: Path to file
        """
        try:
            self.quarantine_path.mkdir(parents=True, exist_ok=True)
            quarantine_dest = self.quarantine_path / file_path.name
            file_path.rename(quarantine_dest)
            self.logger.warning(f"File quarantined: {file_path.name}")
        except Exception as e:
            self.logger.error(f"Failed to quarantine file: {e}")
    
    def _generate_content_preview(self, file_path_str: str) -> str:
        """
        Generate content preview for text-based files.
        
        Args:
            file_path_str: Path to file as string
            
        Returns:
            Content preview string
        """
        file_path = Path(file_path_str)
        ext = file_path.suffix.lower()
        
        # Text-based file types
        text_extensions = {'.txt', '.md', '.py', '.js', '.ts', '.json', '.xml', '.yaml', '.yml', '.csv', '.log'}
        
        if ext not in text_extensions:
            return f"*Preview not available for {ext.upper()} files*"
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500)  # Read first 500 characters
            
            # Truncate and add ellipsis if needed
            if len(content) >= 500:
                content = content[:497] + "..."
            
            # Format as code block
            return f"```\n{content}\n```"
            
        except Exception as e:
            return f"*Error reading file: {e}*"
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string for filename."""
        if not text:
            return ""
        unsafe = '<>:"/\\|?*'
        for char in unsafe:
            text = text.replace(char, '_')
        return text.strip(' _.')
    
    def mark_as_read(self, item: dict[str, Any]) -> None:
        """
        Mark file as processed (no-op for file system).
        
        Args:
            item: File item
        """
        pass  # Files don't have a "read" status
    
    def get_skills(self) -> dict[str, callable]:
        """
        Return Agent Skills exposed by this watcher.
        
        Returns:
            Dictionary of skill names to callables
        """
        base_skills = super().get_skills()
        
        # Add file system-specific skills
        filesystem_skills = {
            'filesystem.check_files': self.check_for_updates,
            'filesystem.process_file': self.process_file,
            'filesystem.parse_file': self.parse_item,
            'filesystem.create_file_action': self.create_action_file,
            'filesystem.security_scan': self._security_scan,
            'filesystem.calculate_hash': self._calculate_hash,
        }
        
        return {**base_skills, **filesystem_skills}
