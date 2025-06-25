#!/usr/bin/env python3
"""
Database Merger Module for Question Database Manager
Handles merging multiple question databases with conflict resolution and preview capabilities.
Phase 3C Implementation - Integrates with Phase 3A (File Processor) and Phase 3B (Upload State Manager)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
import difflib
import hashlib
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MergeStrategy(Enum):
    """Database merge strategies"""
    APPEND_ALL = "append_all"                   # Add all questions, even duplicates
    SKIP_DUPLICATES = "skip_duplicates"         # Skip duplicate questions
    REPLACE_DUPLICATES = "replace_duplicates"   # Replace existing with new
    RENAME_DUPLICATES = "rename_duplicates"     # Rename conflicting questions


class ConflictType(Enum):
    """Types of conflicts that can be detected"""
    QUESTION_ID = "question_id"         # Same question ID in both databases
    CONTENT_DUPLICATE = "content_duplicate"  # Similar question text/answers
    METADATA_CONFLICT = "metadata_conflict"  # Different course/topic information
    LATEX_CONFLICT = "latex_conflict"    # LaTeX formatting differences


class ConflictSeverity(Enum):
    """Severity levels for conflicts"""
    LOW = "low"           # Minor differences, easily resolved
    MEDIUM = "medium"     # Moderate conflicts requiring attention
    HIGH = "high"         # Significant conflicts needing careful resolution
    CRITICAL = "critical" # Major conflicts that could break functionality


@dataclass
class Conflict:
    """Represents a conflict between questions"""
    conflict_type: ConflictType
    severity: ConflictSeverity
    existing_question: Dict[str, Any]
    new_question: Dict[str, Any]
    conflict_details: str
    suggested_resolution: str
    existing_index: Optional[int] = None
    new_index: Optional[int] = None
    similarity_score: float = 0.0
    
    def get_conflict_id(self) -> str:
        """Generate unique ID for this conflict"""
        content = f"{self.conflict_type.value}_{self.existing_index}_{self.new_index}"
        return hashlib.md5(content.encode()).hexdigest()[:8]


@dataclass
class MergePreview:
    """Preview of merge operation results"""
    strategy: MergeStrategy
    existing_count: int
    new_count: int
    final_count: int
    conflicts: List[Conflict]
    merge_summary: Dict[str, Any]
    statistics: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)
    
    def get_conflict_summary(self) -> Dict[str, int]:
        """Get summary of conflicts by type and severity"""
        summary = {}
        for conflict in self.conflicts:
            key = f"{conflict.conflict_type.value}_{conflict.severity.value}"
            summary[key] = summary.get(key, 0) + 1
        return summary


@dataclass
class MergeResult:
    """Result of merge operation"""
    success: bool
    merged_df: Optional[pd.DataFrame]
    conflicts_resolved: List[Conflict]
    merge_preview: MergePreview
    error_message: str = ""
    rollback_data: Optional[Dict[str, Any]] = None
    merge_metadata: Dict[str, Any] = field(default_factory=dict)


class ConflictDetector:
    """Detects conflicts between question databases"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        """
        Initialize conflict detector.
        
        Args:
            similarity_threshold: Threshold for content similarity (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold
    
    def detect_conflicts(self, existing_df: pd.DataFrame, 
                        new_questions: List[Dict[str, Any]]) -> List[Conflict]:
        """
        Detect all types of conflicts between existing and new questions.
        
        Args:
            existing_df: Existing database DataFrame
            new_questions: List of new questions to merge
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Convert existing DataFrame to list of dicts for easier processing
        existing_questions = existing_df.to_dict('records') if not existing_df.empty else []
        
        # Detect different types of conflicts
        conflicts.extend(self._detect_id_conflicts(existing_questions, new_questions))
        conflicts.extend(self._detect_content_duplicates(existing_questions, new_questions))
        conflicts.extend(self._detect_metadata_conflicts(existing_questions, new_questions))
        
        logger.info(f"Detected {len(conflicts)} conflicts")
        return conflicts
    
    def _detect_id_conflicts(self, existing: List[Dict], new: List[Dict]) -> List[Conflict]:
        """Detect question ID conflicts"""
        conflicts = []
        
        # Build index of existing question IDs
        existing_ids = {}
        for i, question in enumerate(existing):
            q_id = question.get('question_id') or question.get('id') or str(i)
            existing_ids[q_id] = (i, question)
        
        # Check new questions for ID conflicts
        for j, new_q in enumerate(new):
            new_id = new_q.get('question_id') or new_q.get('id') or str(j)
            
            if new_id in existing_ids:
                existing_idx, existing_q = existing_ids[new_id]
                
                # Determine severity based on content similarity
                similarity = self._calculate_content_similarity(existing_q, new_q)
                
                if similarity > 0.9:
                    severity = ConflictSeverity.LOW  # Likely same question
                elif similarity > 0.7:
                    severity = ConflictSeverity.MEDIUM  # Similar questions
                else:
                    severity = ConflictSeverity.HIGH  # Different questions, same ID
                
                conflicts.append(Conflict(
                    conflict_type=ConflictType.QUESTION_ID,
                    severity=severity,
                    existing_question=existing_q,
                    new_question=new_q,
                    existing_index=existing_idx,
                    new_index=j,
                    similarity_score=similarity,
                    conflict_details=f"Question ID '{new_id}' already exists",
                    suggested_resolution=self._suggest_id_resolution(similarity)
                ))
        
        return conflicts
    
    def _detect_content_duplicates(self, existing: List[Dict], new: List[Dict]) -> List[Conflict]:
        """Detect content similarity conflicts"""
        conflicts = []
        
        for j, new_q in enumerate(new):
            for i, existing_q in enumerate(existing):
                similarity = self._calculate_content_similarity(existing_q, new_q)
                
                if similarity > self.similarity_threshold:
                    # Skip if we already have an ID conflict for these questions
                    new_id = new_q.get('question_id') or new_q.get('id')
                    existing_id = existing_q.get('question_id') or existing_q.get('id')
                    if new_id == existing_id:
                        continue  # Already handled by ID conflict detection
                    
                    severity = ConflictSeverity.MEDIUM if similarity > 0.9 else ConflictSeverity.LOW
                    
                    conflicts.append(Conflict(
                        conflict_type=ConflictType.CONTENT_DUPLICATE,
                        severity=severity,
                        existing_question=existing_q,
                        new_question=new_q,
                        existing_index=i,
                        new_index=j,
                        similarity_score=similarity,
                        conflict_details=f"Content similarity: {similarity:.2%}",
                        suggested_resolution=f"Review questions for duplication (similarity: {similarity:.2%})"
                    ))
        
        return conflicts
    
    def _detect_metadata_conflicts(self, existing: List[Dict], new: List[Dict]) -> List[Conflict]:
        """Detect metadata conflicts"""
        conflicts = []
        
        # Check for global metadata conflicts (would be handled at database level)
        # For now, focus on question-level metadata conflicts
        
        for j, new_q in enumerate(new):
            for i, existing_q in enumerate(existing):
                # Check if questions are similar but have different metadata
                similarity = self._calculate_content_similarity(existing_q, new_q)
                
                if similarity > 0.8:  # Similar questions
                    metadata_conflicts = self._compare_question_metadata(existing_q, new_q)
                    
                    if metadata_conflicts:
                        conflicts.append(Conflict(
                            conflict_type=ConflictType.METADATA_CONFLICT,
                            severity=ConflictSeverity.LOW,
                            existing_question=existing_q,
                            new_question=new_q,
                            existing_index=i,
                            new_index=j,
                            similarity_score=similarity,
                            conflict_details=f"Metadata differences: {', '.join(metadata_conflicts)}",
                            suggested_resolution="Review and standardize metadata fields"
                        ))
        
        return conflicts
    
    def _calculate_content_similarity(self, q1: Dict[str, Any], q2: Dict[str, Any]) -> float:
        """Calculate similarity between two questions based on content"""
        # Get question text
        text1 = str(q1.get('question_text', q1.get('question', ''))).strip().lower()
        text2 = str(q2.get('question_text', q2.get('question', ''))).strip().lower()
        
        if not text1 or not text2:
            return 0.0
        
        # Use difflib for text similarity
        similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
        
        # Also compare answers if available
        answer1 = str(q1.get('correct_answer', q1.get('answer', ''))).strip().lower()
        answer2 = str(q2.get('correct_answer', q2.get('answer', ''))).strip().lower()
        
        if answer1 and answer2:
            answer_similarity = difflib.SequenceMatcher(None, answer1, answer2).ratio()
            # Weight text similarity more heavily than answer similarity
            similarity = 0.7 * similarity + 0.3 * answer_similarity
        
        return similarity
    
    def _compare_question_metadata(self, q1: Dict[str, Any], q2: Dict[str, Any]) -> List[str]:
        """Compare metadata fields between questions"""
        conflicts = []
        metadata_fields = ['topic', 'subtopic', 'difficulty', 'points', 'type']
        
        for field in metadata_fields:
            val1 = q1.get(field)
            val2 = q2.get(field)
            
            if val1 is not None and val2 is not None and val1 != val2:
                conflicts.append(f"{field}: '{val1}' vs '{val2}'")
        
        return conflicts
    
    def _suggest_id_resolution(self, similarity: float) -> str:
        """Suggest resolution for ID conflicts based on similarity"""
        if similarity > 0.9:
            return "Questions appear identical - recommend skipping duplicate"
        elif similarity > 0.7:
            return "Questions are similar - review for updates or rename new question"
        else:
            return "Different questions with same ID - rename one of the questions"


class ConflictResolver:
    """Resolves conflicts based on merge strategy"""
    
    def __init__(self, strategy: MergeStrategy):
        self.strategy = strategy
    
    def resolve_conflicts(self, conflicts: List[Conflict], 
                         existing_df: pd.DataFrame,
                         new_questions: List[Dict[str, Any]]) -> Tuple[List[Dict], List[str]]:
        """
        Resolve conflicts based on merge strategy.
        
        Args:
            conflicts: List of detected conflicts
            existing_df: Existing database DataFrame
            new_questions: New questions to merge
            
        Returns:
            Tuple of (resolved_questions, warnings)
        """
        warnings = []
        
        if self.strategy == MergeStrategy.APPEND_ALL:
            return self._resolve_append_all(conflicts, new_questions, warnings)
        elif self.strategy == MergeStrategy.SKIP_DUPLICATES:
            return self._resolve_skip_duplicates(conflicts, new_questions, warnings)
        elif self.strategy == MergeStrategy.REPLACE_DUPLICATES:
            return self._resolve_replace_duplicates(conflicts, existing_df, new_questions, warnings)
        elif self.strategy == MergeStrategy.RENAME_DUPLICATES:
            return self._resolve_rename_duplicates(conflicts, new_questions, warnings)
        else:
            warnings.append(f"Unknown merge strategy: {self.strategy}")
            return new_questions, warnings
    
    def _resolve_append_all(self, conflicts: List[Conflict], 
                           new_questions: List[Dict], warnings: List[str]) -> Tuple[List[Dict], List[str]]:
        """Append all questions, including duplicates"""
        if conflicts:
            warnings.append(f"Appending all questions despite {len(conflicts)} conflicts")
        return new_questions, warnings
    
    def _resolve_skip_duplicates(self, conflicts: List[Conflict], 
                                new_questions: List[Dict], warnings: List[str]) -> Tuple[List[Dict], List[str]]:
        """Skip questions that have conflicts"""
        skip_indices = set()
        
        for conflict in conflicts:
            if (conflict.conflict_type in [ConflictType.QUESTION_ID, ConflictType.CONTENT_DUPLICATE] and
                conflict.similarity_score > 0.8):
                skip_indices.add(conflict.new_index)
                warnings.append(f"Skipping question {conflict.new_index + 1} due to {conflict.conflict_type.value}")
        
        resolved_questions = [q for i, q in enumerate(new_questions) if i not in skip_indices]
        
        if skip_indices:
            warnings.append(f"Skipped {len(skip_indices)} duplicate questions")
        
        return resolved_questions, warnings
    
    def _resolve_replace_duplicates(self, conflicts: List[Conflict], existing_df: pd.DataFrame,
                                   new_questions: List[Dict], warnings: List[str]) -> Tuple[List[Dict], List[str]]:
        """Replace existing questions with new ones for conflicts"""
        # This strategy requires coordination with the main merge process
        # For now, return new questions and let main process handle replacement
        
        replace_indices = set()
        for conflict in conflicts:
            if conflict.conflict_type == ConflictType.QUESTION_ID:
                replace_indices.add(conflict.existing_index)
                warnings.append(f"Will replace existing question {conflict.existing_index + 1}")
        
        if replace_indices:
            warnings.append(f"Will replace {len(replace_indices)} existing questions")
        
        return new_questions, warnings
    
    def _resolve_rename_duplicates(self, conflicts: List[Conflict], 
                                  new_questions: List[Dict], warnings: List[str]) -> Tuple[List[Dict], List[str]]:
        """Rename conflicting questions to avoid duplicates"""
        resolved_questions = new_questions.copy()
        
        for conflict in conflicts:
            if conflict.conflict_type == ConflictType.QUESTION_ID and conflict.new_index is not None:
                new_q = resolved_questions[conflict.new_index]
                old_id = new_q.get('question_id') or new_q.get('id', f"q_{conflict.new_index}")
                new_id = f"{old_id}_new_{datetime.now().strftime('%H%M%S')}"
                
                # Update question ID
                if 'question_id' in new_q:
                    new_q['question_id'] = new_id
                elif 'id' in new_q:
                    new_q['id'] = new_id
                
                # Update title if it exists
                if 'title' in new_q:
                    new_q['title'] = f"{new_q['title']} (Renamed)"
                
                warnings.append(f"Renamed question ID from '{old_id}' to '{new_id}'")
        
        return resolved_questions, warnings


class DatabaseMerger:
    """Main database merger class"""
    
    def __init__(self, strategy: MergeStrategy = MergeStrategy.SKIP_DUPLICATES,
                 similarity_threshold: float = 0.8):
        """
        Initialize database merger.
        
        Args:
            strategy: Default merge strategy
            similarity_threshold: Threshold for content similarity detection
        """
        self.strategy = strategy
        self.conflict_detector = ConflictDetector(similarity_threshold)
        self.conflict_resolver = ConflictResolver(strategy)
        # Add these methods to your DatabaseMerger class in database_merger.py

    def auto_renumber_questions(self, existing_df: pd.DataFrame, new_questions: List[Dict]) -> List[Dict]:
        """
        Automatically renumber new questions to avoid ID conflicts.
        Args:
            existing_df: Current database DataFrame
            new_questions: List of new questions to add
        Returns:
            List of new questions with renumbered IDs
        """
        if existing_df is None or len(existing_df) == 0:
            # No existing database, keep original numbering
            return new_questions

        # Find the highest existing ID
        existing_ids = []
        id_columns = ['id', 'question_id', 'ID', 'Question_ID']
        id_column = None

        for col in id_columns:
            if col in existing_df.columns:
                id_column = col
                break

        if id_column:
            for idx, row in existing_df.iterrows():
                try:
                    existing_id = str(row[id_column])
                    if existing_id.isdigit():
                        existing_ids.append(int(existing_id))
                    else:
                        import re
                        numbers = re.findall(r'\d+', existing_id)
                        if numbers:
                            existing_ids.append(int(numbers[-1]))
                except Exception:
                    continue

        logger.info(f"🔍 DEBUG auto_renumber: existing_ids = {existing_ids}")
        logger.info(f"🔍 DEBUG auto_renumber: id_column = {id_column}")
        logger.info(f"🔍 DEBUG auto_renumber: len(existing_df) = {len(existing_df)}")

        # Find the next available ID
        if id_column is None:
            next_id = len(existing_df)
            logger.info(f"No ID column found in auto_renumber_questions, using row count: {next_id}")
        elif existing_ids:
            next_id = max(existing_ids) + 1
        else:
            next_id = 0

        logger.info(f"Auto-renumbering: Next available ID is {next_id}")

        # Renumber the new questions
        renumbered_questions = []
        for i, question in enumerate(new_questions):
            new_question = question.copy()
            new_id = next_id + i
            for id_field in ['id', 'question_id', 'ID', 'Question_ID']:
                if id_field in new_question:
                    new_question[id_field] = str(new_id)
            if not any(field in new_question for field in ['id', 'question_id', 'ID', 'Question_ID']):
                new_question['id'] = str(new_id)
            renumbered_questions.append(new_question)

        logger.info(f"Auto-renumbered {len(new_questions)} questions from ID {next_id} to {next_id + len(new_questions) - 1}")
        return renumbered_questions

    def detect_sequential_id_conflicts(self, existing_df: pd.DataFrame, new_questions: List[Dict]) -> bool:
        """
        Detect if conflicts are just sequential numbering (0,1,2,3...) vs meaningful conflicts.
        Returns:
            True if new questions appear to be just sequential numbering that conflicts with existing
        """
        if existing_df is None or len(existing_df) == 0 or len(new_questions) == 0:
            return False

        existing_ids = set()
        new_ids = []
        id_columns = ['id', 'question_id', 'ID', 'Question_ID']
        id_column = None

        for col in id_columns:
            if col in existing_df.columns:
                id_column = col
                break

        if id_column:
            for idx, row in existing_df.iterrows():
                try:
                    existing_id = str(row[id_column])
                    if existing_id.isdigit():
                        existing_ids.add(int(existing_id))
                except Exception:
                    continue

        for question in new_questions:
            for id_field in id_columns:
                if id_field in question:
                    try:
                        new_id = str(question[id_field])
                        if new_id.isdigit():
                            new_ids.append(int(new_id))
                        break
                    except Exception:
                        continue

        if not existing_ids or not new_ids:
            return False

        new_ids_sorted = sorted(new_ids)
        expected_sequence = list(range(len(new_ids_sorted)))
        is_new_sequential = (new_ids_sorted == expected_sequence)

        logger.info(f"Sequential detection: new_ids={new_ids_sorted}, expected={expected_sequence}, is_sequential={is_new_sequential}")

        if not is_new_sequential:
            return False

        conflicts = existing_ids.intersection(set(new_ids))
        has_conflicts = len(conflicts) > 0

        logger.info(f"ID conflicts: existing_ids={sorted(list(existing_ids))}, new_ids={new_ids_sorted}, conflicts={sorted(list(conflicts))}")
        result = is_new_sequential and has_conflicts
        logger.info(f"Sequential conflict detection result: {result} (sequential={is_new_sequential}, conflicts={len(conflicts)})")
        return result

# ...existing code...