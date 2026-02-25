"""
File utility functions for the AI Employee system.

This module provides safe file operations following the requirements
specified in the constitution and data model.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple, List
import mimetypes
from datetime import datetime
import hashlib


def safe_move_file(source_path: Path, dest_path: Path) -> bool:
    """
    Safely move a file from source to destination.

    Args:
        source_path: Path to the source file
        dest_path: Path to the destination

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Move the file
        shutil.move(str(source_path), str(dest_path))
        return True
    except Exception as e:
        print(f"Error moving file {source_path} to {dest_path}: {str(e)}")
        return False


def safe_copy_file(source_path: Path, dest_path: Path) -> bool:
    """
    Safely copy a file from source to destination.

    Args:
        source_path: Path to the source file
        dest_path: Path to the destination

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy the file
        shutil.copy2(str(source_path), str(dest_path))
        return True
    except Exception as e:
        print(f"Error copying file {source_path} to {dest_path}: {str(e)}")
        return False


def get_file_size(file_path: Path) -> int:
    """
    Get the size of a file in bytes.

    Args:
        file_path: Path to the file

    Returns:
        Size of the file in bytes
    """
    return file_path.stat().st_size


def get_file_type(file_path: Path) -> str:
    """
    Determine the file type based on extension.

    Args:
        file_path: Path to the file

    Returns:
        MIME type of the file
    """
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or "application/octet-stream"


def is_safe_filename(filename: str) -> bool:
    """
    Check if a filename is safe to use.

    Args:
        filename: Filename to check

    Returns:
        True if filename is safe, False otherwise
    """
    # Check for dangerous patterns
    dangerous_patterns = [
        '..',   # Parent directory traversal
        '~',    # Home directory expansion
        '/',    # Absolute path
        '\\',   # Windows path separator
        chr(0), # Null byte
    ]

    for pattern in dangerous_patterns:
        if pattern in filename:
            return False

    # Check length (prevent extremely long filenames)
    if len(filename) > 255:
        return False

    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by replacing special characters with underscores.

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove path separators and other dangerous characters
    sanitized = filename.replace('/', '_').replace('\\', '_').replace('..', '_')

    # Replace special characters with underscores
    for char in '<>:"|?*':
        sanitized = sanitized.replace(char, '_')

    # Limit length to 255 characters
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        max_name_len = 250 - len(ext)  # Leave room for extension and counter
        if max_name_len > 0:
            sanitized = name[:max_name_len] + ext
        else:
            sanitized = sanitized[:255]

    return sanitized


def create_unique_filename(base_path: Path, filename: str, max_attempts: int = 100) -> Path:
    """
    Create a unique filename by appending a counter if the file exists.

    Args:
        base_path: Base directory path
        filename: Desired filename
        max_attempts: Maximum number of attempts to find a unique name

    Returns:
        Unique file path
    """
    file_path = base_path / filename
    counter = 1

    while file_path.exists() and counter <= max_attempts:
        name, ext = os.path.splitext(filename)
        unique_name = f"{name}_{counter}{ext}"
        file_path = base_path / unique_name
        counter += 1

    if counter > max_attempts:
        raise RuntimeError(f"Could not create unique filename after {max_attempts} attempts")

    return file_path


def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate the hash of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hex digest of the file hash
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read file in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def validate_file_size(file_path: Path, max_size_bytes: int) -> Tuple[bool, str]:
    """
    Validate that a file is within the allowed size limit.

    Args:
        file_path: Path to the file
        max_size_bytes: Maximum allowed size in bytes

    Returns:
        Tuple of (is_valid, message)
    """
    size = get_file_size(file_path)
    if size > max_size_bytes:
        return False, f"File size {size} bytes exceeds maximum allowed size of {max_size_bytes} bytes"
    return True, "File size is within limits"


def read_file_safely(file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
    """
    Safely read a file with error handling.

    Args:
        file_path: Path to the file
        encoding: Text encoding to use (default: utf-8)

    Returns:
        File content as string or None if error occurs
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception:
            print(f"Error reading file {file_path}: unable to decode with UTF-8 or Latin-1")
            return None
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None


def write_file_safely(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
    """
    Safely write content to a file with error handling.

    Args:
        file_path: Path to the file
        content: Content to write
        encoding: Text encoding to use (default: utf-8)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing to file {file_path}: {str(e)}")
        return False


def ensure_directory_exists(directory_path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory_path: Path to the directory

    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        directory_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {str(e)}")
        return False


def get_files_in_directory(directory_path: Path, pattern: str = "*") -> List[Path]:
    """
    Get a list of files in a directory matching a pattern.

    Args:
        directory_path: Path to the directory
        pattern: Glob pattern to match (default: "*")

    Returns:
        List of matching file paths
    """
    try:
        return list(directory_path.glob(pattern))
    except Exception as e:
        print(f"Error reading directory {directory_path}: {str(e)}")
        return []


def get_file_creation_time(file_path: Path) -> datetime:
    """
    Get the creation time of a file.

    Args:
        file_path: Path to the file

    Returns:
        Datetime object representing creation time
    """
    stat = file_path.stat()
    # On Windows, st_ctime is creation time; on Unix, it's the last metadata change
    # For cross-platform compatibility, we'll use st_mtime as a fallback
    try:
        return datetime.fromtimestamp(stat.st_birthtime if hasattr(stat, 'st_birthtime') else stat.st_ctime)
    except AttributeError:
        # On some platforms, birthtime is not available, use ctime
        return datetime.fromtimestamp(stat.st_ctime)


def get_file_modification_time(file_path: Path) -> datetime:
    """
    Get the modification time of a file.

    Args:
        file_path: Path to the file

    Returns:
        Datetime object representing modification time
    """
    return datetime.fromtimestamp(file_path.stat().st_mtime)


if __name__ == "__main__":
    # Example usage
    test_file = Path("test_file.txt")

    # Write a test file
    if write_file_safely(test_file, "This is a test file"):
        print(f"Created test file: {test_file}")
        print(f"File size: {get_file_size(test_file)} bytes")
        print(f"File type: {get_file_type(test_file)}")
        print(f"File hash: {calculate_file_hash(test_file)}")

        # Clean up
        if test_file.exists():
            test_file.unlink()
            print("Cleaned up test file")
    else:
        print("Failed to create test file")