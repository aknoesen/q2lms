#!/usr/bin/env python3
"""
Filename Utilities Module
Handles filename sanitization, validation, and custom naming for exports
"""

import re
import os
from datetime import datetime
from typing import Optional, Tuple


class FilenameHandler:
    """Handles all filename-related operations for QTI exports"""
    
    # Characters that are problematic in filenames across different operating systems
    UNSAFE_CHARS = r'[<>:"/\\|?*\x00-\x1f]'
    
    # Reserved names in Windows
    RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    def __init__(self):
        self.max_length = 100  # Conservative max length for cross-platform compatibility
    
    def sanitize_filename(self, filename: str, replacement_char: str = '_') -> str:
        """
        Sanitize a filename to be safe across different operating systems
        
        Args:
            filename: The original filename
            replacement_char: Character to replace unsafe characters with
            
        Returns:
            A sanitized filename safe for use
        """
        if not filename or not filename.strip():
            return self._generate_default_name()
        
        # Convert to string and strip whitespace
        filename = str(filename).strip()
        
        # Replace unsafe characters
        sanitized = re.sub(self.UNSAFE_CHARS, replacement_char, filename)
        
        # Replace multiple consecutive replacement chars with single one
        sanitized = re.sub(f'{re.escape(replacement_char)}+', replacement_char, sanitized)
        
        # Remove leading/trailing replacement chars and dots
        sanitized = sanitized.strip(f'{replacement_char}.')
        
        # Handle reserved names
        name_without_ext = os.path.splitext(sanitized)[0].upper()
        if name_without_ext in self.RESERVED_NAMES:
            sanitized = f"{sanitized}_file"
        
        # Truncate if too long, preserving extension
        sanitized = self._truncate_filename(sanitized)
        
        # If somehow we end up with empty string, use default
        if not sanitized:
            return self._generate_default_name()
        
        return sanitized
    
    def _truncate_filename(self, filename: str) -> str:
        """Truncate filename while preserving extension"""
        if len(filename) <= self.max_length:
            return filename
        
        name, ext = os.path.splitext(filename)
        available_length = self.max_length - len(ext)
        
        if available_length > 0:
            return name[:available_length] + ext
        else:
            # Extension is too long, just truncate everything
            return filename[:self.max_length]
    
    def _generate_default_name(self) -> str:
        """Generate a default filename when none is provided"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"Question_Package_{timestamp}"
    
    def create_qti_filename(self, 
                           user_input: Optional[str] = None,
                           quiz_title: Optional[str] = None,
                           add_timestamp: bool = False) -> str:
        """
        Create a filename for QTI package export
        
        Args:
            user_input: User-provided filename
            quiz_title: Fallback quiz title
            add_timestamp: Whether to add timestamp suffix
            
        Returns:
            Complete filename with .zip extension
        """
        # Determine base name
        if user_input and user_input.strip():
            base_name = user_input.strip()
        elif quiz_title and quiz_title.strip():
            base_name = quiz_title.strip()
        else:
            base_name = self._generate_default_name()
        
        # Remove .zip extension if user included it
        if base_name.lower().endswith('.zip'):
            base_name = base_name[:-4]
        
        # Sanitize the base name
        base_name = self.sanitize_filename(base_name)
        
        # Add timestamp if requested
        if add_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"{base_name}_{timestamp}"
        
        # Add .zip extension
        return f"{base_name}.zip"
    
    def validate_filename_input(self, filename: str) -> Tuple[bool, str]:
        """
        Validate user filename input and provide feedback
        
        Args:
            filename: User-provided filename
            
        Returns:
            Tuple of (is_valid, feedback_message)
        """
        if not filename or not filename.strip():
            return False, "Filename cannot be empty"
        
        filename = filename.strip()
        
        # Check for obviously problematic characters
        if re.search(self.UNSAFE_CHARS, filename):
            unsafe_found = set(re.findall(self.UNSAFE_CHARS, filename))
            return False, f"Filename contains unsafe characters: {', '.join(sorted(unsafe_found))}"
        
        # Check length
        if len(filename) > self.max_length:
            return False, f"Filename too long (max {self.max_length} characters)"
        
        # Check for reserved names
        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in self.RESERVED_NAMES:
            return False, f"'{name_without_ext}' is a reserved filename"
        
        # Check for only dots or spaces
        if filename.replace('.', '').replace(' ', '').replace('_', '') == '':
            return False, "Filename must contain at least one alphanumeric character"
        
        return True, "Filename looks good!"
    
    def suggest_filename(self, quiz_title: str, question_count: int) -> str:
        """
        Suggest a good filename based on quiz properties
        
        Args:
            quiz_title: The quiz title
            question_count: Number of questions
            
        Returns:
            Suggested filename (without extension)
        """
        if not quiz_title or not quiz_title.strip():
            base = f"Quiz_{question_count}Q"
        else:
            # Clean up the title for use in filename
            clean_title = re.sub(r'\s+', '_', quiz_title.strip())
            clean_title = self.sanitize_filename(clean_title)
            base = f"{clean_title}_{question_count}Q"
        
        return base


class ExportNamingManager:
    """Manages naming for different types of exports"""
    
    def __init__(self):
        self.filename_handler = FilenameHandler()
    
    def get_csv_filename(self, user_input: Optional[str] = None, 
                        base_name: str = "questions") -> str:
        """Get filename for CSV export"""
        if user_input:
            name = self.filename_handler.sanitize_filename(user_input)
        else:
            name = base_name
        
        # Remove .csv extension if present
        if name.lower().endswith('.csv'):
            name = name[:-4]
        
        return f"{name}.csv"
    
    def get_qti_filename(self, user_input: Optional[str] = None,
                        quiz_title: Optional[str] = None,
                        add_timestamp: bool = False) -> str:
        """Get filename for QTI package export"""
        return self.filename_handler.create_qti_filename(
            user_input, quiz_title, add_timestamp
        )
    
    def validate_user_input(self, filename: str) -> Tuple[bool, str]:
        """Validate user filename input"""
        return self.filename_handler.validate_filename_input(filename)
    
    def suggest_name(self, quiz_title: str, question_count: int) -> str:
        """Suggest a filename based on quiz properties"""
        return self.filename_handler.suggest_filename(quiz_title, question_count)


# Convenience functions for backward compatibility
def sanitize_filename(filename: str) -> str:
    """Legacy function for backward compatibility"""
    handler = FilenameHandler()
    return handler.sanitize_filename(filename)


def create_safe_filename(user_input: Optional[str], 
                        fallback: str = "Question_Package") -> str:
    """Create a safe filename with fallback"""
    handler = FilenameHandler()
    if user_input:
        return handler.sanitize_filename(user_input)
    return handler.sanitize_filename(fallback)
