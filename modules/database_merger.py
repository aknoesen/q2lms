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
    
    def generate_preview(self, existing_df: pd.DataFrame, 
                        new_questions: List[Dict[str, Any]],
                        strategy: Optional[MergeStrategy] = None) -> MergePreview:
        """
        Generate a preview of the merge operation.
        
        Args:
            existing_df: Current database DataFrame
            new_questions: Questions to be merged
            strategy: Merge strategy to use (defaults to instance strategy)
            
        Returns:
            MergePreview with detailed information about the merge
        """
        if strategy is None:
            strategy = self.strategy
        
        logger.info(f"Generating merge preview with strategy: {strategy.value}")
        
        # Detect conflicts
        conflicts = self.conflict_detector.detect_conflicts(existing_df, new_questions)
        
        # Calculate statistics
        existing_count = len(existing_df) if not existing_df.empty else 0
        new_count = len(new_questions)
        
        # Estimate final count based on strategy
        final_count = self._estimate_final_count(existing_count, new_count, conflicts, strategy)
        
        # Generate merge summary
        merge_summary = self._generate_merge_summary(existing_df, new_questions, conflicts, strategy)
        
        # Generate statistics
        statistics = self._generate_statistics(existing_df, new_questions, conflicts)
        
        # Generate warnings
        warnings = self._generate_warnings(conflicts, strategy)
        
        preview = MergePreview(
            strategy=strategy,
            existing_count=existing_count,
            new_count=new_count,
            final_count=final_count,
            conflicts=conflicts,
            merge_summary=merge_summary,
            statistics=statistics,
            warnings=warnings
        )
        
        logger.info(f"Preview generated: {existing_count} + {new_count} -> {final_count} questions, {len(conflicts)} conflicts")
        return preview
    
    def merge_databases(self, existing_df: pd.DataFrame, 
                       new_questions: List[Dict[str, Any]],
                       strategy: Optional[MergeStrategy] = None,
                       preview: Optional[MergePreview] = None) -> MergeResult:
        """
        Perform the actual database merge operation.
        
        Args:
            existing_df: Current database DataFrame
            new_questions: Questions to be merged
            strategy: Merge strategy to use
            preview: Pre-generated preview (optional)
            
        Returns:
            MergeResult with the merged database and operation details
        """
        if strategy is None:
            strategy = self.strategy
        
        logger.info(f"Starting database merge with strategy: {strategy.value}")
        
        try:
            # Generate preview if not provided
            if preview is None:
                preview = self.generate_preview(existing_df, new_questions, strategy)
            
            # Create rollback data
            rollback_data = {
                'df': existing_df.copy() if not existing_df.empty else pd.DataFrame(),
                'timestamp': datetime.now().isoformat(),
                'operation': f"merge_{strategy.value}"
            }
            
            # Update conflict resolver strategy
            self.conflict_resolver.strategy = strategy
            
            # Resolve conflicts
            resolved_questions, warnings = self.conflict_resolver.resolve_conflicts(
                preview.conflicts, existing_df, new_questions
            )
            
            # Perform the merge based on strategy
            merged_df = self._execute_merge(existing_df, resolved_questions, preview.conflicts, strategy)
            
            # Generate merge metadata
            merge_metadata = {
                'merge_timestamp': datetime.now().isoformat(),
                'merge_strategy': strategy.value,
                'original_count': len(existing_df) if not existing_df.empty else 0,
                'added_count': len(resolved_questions),
                'final_count': len(merged_df),
                'conflicts_detected': len(preview.conflicts),
                'warnings': warnings
            }
            
            result = MergeResult(
                success=True,
                merged_df=merged_df,
                conflicts_resolved=preview.conflicts,
                merge_preview=preview,
                rollback_data=rollback_data,
                merge_metadata=merge_metadata
            )
            
            logger.info(f"Merge completed successfully: {merge_metadata['final_count']} total questions")
            return result
            
        except Exception as e:
            logger.error(f"Merge operation failed: {str(e)}")
            
            return MergeResult(
                success=False,
                merged_df=None,
                conflicts_resolved=[],
                merge_preview=preview or MergePreview(
                    strategy=strategy,
                    existing_count=0,
                    new_count=0,
                    final_count=0,
                    conflicts=[],
                    merge_summary={},
                    statistics={}
                ),
                error_message=str(e),
                rollback_data=None
            )
    
    def _estimate_final_count(self, existing_count: int, new_count: int, 
                             conflicts: List[Conflict], strategy: MergeStrategy) -> int:
        """Estimate final question count after merge"""
        
        if strategy == MergeStrategy.APPEND_ALL:
            return existing_count + new_count
        
        elif strategy == MergeStrategy.SKIP_DUPLICATES:
            # Count questions that would be skipped
            skip_count = len([c for c in conflicts 
                            if c.conflict_type in [ConflictType.QUESTION_ID, ConflictType.CONTENT_DUPLICATE]
                            and c.similarity_score > 0.8])
            return existing_count + new_count - skip_count
        
        elif strategy == MergeStrategy.REPLACE_DUPLICATES:
            # Existing questions get replaced, so no net increase for duplicates
            replace_count = len([c for c in conflicts if c.conflict_type == ConflictType.QUESTION_ID])
            return existing_count + new_count - replace_count
        
        elif strategy == MergeStrategy.RENAME_DUPLICATES:
            return existing_count + new_count
        
        else:
            return existing_count + new_count
    
    def _generate_merge_summary(self, existing_df: pd.DataFrame, new_questions: List[Dict],
                               conflicts: List[Conflict], strategy: MergeStrategy) -> Dict[str, Any]:
        """Generate detailed merge summary"""
        
        # Analyze question types in new questions
        new_types = {}
        for q in new_questions:
            q_type = q.get('type', 'unknown')
            new_types[q_type] = new_types.get(q_type, 0) + 1
        
        # Analyze existing types
        existing_types = {}
        if not existing_df.empty and 'type' in existing_df.columns:
            existing_types = existing_df['type'].value_counts().to_dict()
        
        summary = {
            'strategy_used': strategy.value,
            'new_question_types': new_types,
            'existing_question_types': existing_types,
            'conflict_breakdown': self._breakdown_conflicts(conflicts),
            'estimated_changes': self._estimate_changes(conflicts, strategy),
            'recommendations': self._generate_recommendations(conflicts, strategy)
        }
        
        return summary
    
    def _generate_statistics(self, existing_df: pd.DataFrame, new_questions: List[Dict],
                           conflicts: List[Conflict]) -> Dict[str, Any]:
        """Generate detailed statistics about the merge"""
        
        stats = {
            'total_conflicts': len(conflicts),
            'conflict_types': {},
            'severity_breakdown': {},
            'similarity_distribution': [],
            'metadata_coverage': {}
        }
        
        # Conflict type breakdown
        for conflict in conflicts:
            ctype = conflict.conflict_type.value
            stats['conflict_types'][ctype] = stats['conflict_types'].get(ctype, 0) + 1
            
            severity = conflict.severity.value
            stats['severity_breakdown'][severity] = stats['severity_breakdown'].get(severity, 0) + 1
            
            if conflict.similarity_score > 0:
                stats['similarity_distribution'].append(conflict.similarity_score)
        
        # Metadata coverage analysis
        all_fields = set()
        for q in new_questions:
            all_fields.update(q.keys())
        
        if not existing_df.empty:
            all_fields.update(existing_df.columns)
        
        for field in all_fields:
            new_coverage = sum(1 for q in new_questions if q.get(field) is not None)
            existing_coverage = 0
            if not existing_df.empty and field in existing_df.columns:
                existing_coverage = existing_df[field].notna().sum()
            
            stats['metadata_coverage'][field] = {
                'new_questions': new_coverage,
                'existing_questions': existing_coverage,
                'new_percentage': (new_coverage / len(new_questions) * 100) if new_questions else 0,
                'existing_percentage': (existing_coverage / len(existing_df) * 100) if not existing_df.empty else 0
            }
        
        return stats
    
    def _generate_warnings(self, conflicts: List[Conflict], strategy: MergeStrategy) -> List[str]:
        """Generate warnings based on conflicts and strategy"""
        warnings = []
        
        critical_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.CRITICAL]
        if critical_conflicts:
            warnings.append(f"Found {len(critical_conflicts)} critical conflicts that need attention")
        
        high_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.HIGH]
        if high_conflicts:
            warnings.append(f"Found {len(high_conflicts)} high-severity conflicts")
        
        id_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.QUESTION_ID]
        if id_conflicts and strategy == MergeStrategy.APPEND_ALL:
            warnings.append(f"Duplicate question IDs will be preserved with APPEND_ALL strategy")
        
        content_duplicates = [c for c in conflicts if c.conflict_type == ConflictType.CONTENT_DUPLICATE]
        if len(content_duplicates) > len(conflicts) * 0.5:
            warnings.append("High percentage of content duplicates detected - review merge strategy")
        
        return warnings
    
    def _breakdown_conflicts(self, conflicts: List[Conflict]) -> Dict[str, Any]:
        """Break down conflicts by type and severity"""
        breakdown = {
            'by_type': {},
            'by_severity': {},
            'details': []
        }
        
        for conflict in conflicts:
            # By type
            ctype = conflict.conflict_type.value
            breakdown['by_type'][ctype] = breakdown['by_type'].get(ctype, 0) + 1
            
            # By severity
            severity = conflict.severity.value
            breakdown['by_severity'][severity] = breakdown['by_severity'].get(severity, 0) + 1
            
            # Detailed info
            breakdown['details'].append({
                'type': ctype,
                'severity': severity,
                'similarity': conflict.similarity_score,
                'description': conflict.conflict_details
            })
        
        return breakdown
    
    def _estimate_changes(self, conflicts: List[Conflict], strategy: MergeStrategy) -> Dict[str, Any]:
        """Estimate what changes will occur"""
        changes = {
            'questions_added': 0,
            'questions_skipped': 0,
            'questions_replaced': 0,
            'questions_renamed': 0,
            'warnings_generated': 0
        }
        
        if strategy == MergeStrategy.SKIP_DUPLICATES:
            changes['questions_skipped'] = len([c for c in conflicts 
                                              if c.conflict_type in [ConflictType.QUESTION_ID, ConflictType.CONTENT_DUPLICATE]
                                              and c.similarity_score > 0.8])
        
        elif strategy == MergeStrategy.REPLACE_DUPLICATES:
            changes['questions_replaced'] = len([c for c in conflicts if c.conflict_type == ConflictType.QUESTION_ID])
        
        elif strategy == MergeStrategy.RENAME_DUPLICATES:
            changes['questions_renamed'] = len([c for c in conflicts if c.conflict_type == ConflictType.QUESTION_ID])
        
        return changes
    
    def _generate_recommendations(self, conflicts: List[Conflict], strategy: MergeStrategy) -> List[str]:
        """Generate recommendations based on conflicts"""
        recommendations = []
        
        if not conflicts:
            recommendations.append("No conflicts detected - merge should proceed smoothly")
            return recommendations
        
        critical_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.CRITICAL]
        if critical_conflicts:
            recommendations.append("Review critical conflicts before proceeding")
        
        if strategy == MergeStrategy.APPEND_ALL and conflicts:
            recommendations.append("Consider using SKIP_DUPLICATES or RENAME_DUPLICATES to handle conflicts")
        
        content_duplicates = [c for c in conflicts if c.conflict_type == ConflictType.CONTENT_DUPLICATE]
        if len(content_duplicates) > 5:
            recommendations.append("Many content duplicates detected - consider manual review")
        
        return recommendations
    
    def _execute_merge(self, existing_df: pd.DataFrame, resolved_questions: List[Dict],
                      conflicts: List[Conflict], strategy: MergeStrategy) -> pd.DataFrame:
        """Execute the actual merge operation"""
        
        # Convert resolved questions to DataFrame
        if resolved_questions:
            new_df = pd.DataFrame(resolved_questions)
        else:
            new_df = pd.DataFrame()
        
        if existing_df.empty:
            return new_df
        
        if new_df.empty:
            return existing_df
        
        # Handle strategy-specific merging
        if strategy == MergeStrategy.REPLACE_DUPLICATES:
            return self._execute_replace_merge(existing_df, new_df, conflicts)
        else:
            # For other strategies, simple concatenation after conflict resolution
            return self._execute_append_merge(existing_df, new_df)
    
    def _execute_replace_merge(self, existing_df: pd.DataFrame, 
                              new_df: pd.DataFrame, conflicts: List[Conflict]) -> pd.DataFrame:
        """Execute merge with replacement strategy"""
        
        # Get indices of questions to replace
        replace_indices = set()
        for conflict in conflicts:
            if (conflict.conflict_type == ConflictType.QUESTION_ID and 
                conflict.existing_index is not None):
                replace_indices.add(conflict.existing_index)
        
        # Create copy of existing DataFrame
        merged_df = existing_df.copy()
        
        # Remove questions that will be replaced
        if replace_indices:
            merged_df = merged_df.drop(merged_df.index[list(replace_indices)])
        
        # Append new questions
        merged_df = self._execute_append_merge(merged_df, new_df)
        
        return merged_df
    
    def _execute_append_merge(self, existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
        """Execute simple append merge"""
        
        # Align columns between DataFrames
        all_columns = set(existing_df.columns) | set(new_df.columns)
        
        # Add missing columns with NaN values
        for col in all_columns:
            if col not in existing_df.columns:
                existing_df[col] = np.nan
            if col not in new_df.columns:
                new_df[col] = np.nan
        
        # Reorder columns to match
        column_order = list(all_columns)
        existing_df = existing_df[column_order]
        new_df = new_df[column_order]
        
        # Concatenate DataFrames
        merged_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        return merged_df


# Integration functions for use with Phase 3A and 3B
def create_merge_preview(existing_df: pd.DataFrame, 
                        new_questions: List[Dict[str, Any]], 
                        strategy: MergeStrategy = MergeStrategy.SKIP_DUPLICATES,
                        similarity_threshold: float = 0.8) -> MergePreview:
    """
    Convenience function to create merge preview.
    Integrates with Phase 3A (FileProcessor) output and Phase 3B (UploadStateManager).
    
    Args:
        existing_df: Current database DataFrame from session state
        new_questions: Questions from FileProcessor.process_file() result
        strategy: Merge strategy to use
        similarity_threshold: Similarity threshold for conflict detection
        
    Returns:
        MergePreview object for UI consumption
    """
    merger = DatabaseMerger(strategy, similarity_threshold)
    return merger.generate_preview(existing_df, new_questions, strategy)


def execute_database_merge(existing_df: pd.DataFrame,
                          new_questions: List[Dict[str, Any]],
                          strategy: MergeStrategy = MergeStrategy.SKIP_DUPLICATES,
                          preview: Optional[MergePreview] = None,
                          similarity_threshold: float = 0.8) -> MergeResult:
    """
    Convenience function to execute database merge.
    Integrates with Phase 3A and 3B for complete workflow.
    
    Args:
        existing_df: Current database DataFrame
        new_questions: Questions from FileProcessor
        strategy: Merge strategy to use
        preview: Pre-generated preview (optional)
        similarity_threshold: Similarity threshold for conflict detection
        
    Returns:
        MergeResult with merged database and operation details
    """
    merger = DatabaseMerger(strategy, similarity_threshold)
    return merger.merge_databases(existing_df, new_questions, strategy, preview)


def prepare_session_state_for_preview(preview: MergePreview, 
                                     processing_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare session state data for PREVIEW_MERGE state.
    Integrates with Phase 3B UploadStateManager for UI consumption.
    
    Args:
        preview: MergePreview object
        processing_results: Results from Phase 3A FileProcessor
        
    Returns:
        Dictionary to store in st.session_state['preview_data']
    """
    
    preview_data = {
        # Merge strategy and configuration
        'merge_strategy': preview.strategy.value,
        'similarity_threshold': 0.8,  # Could be made configurable
        
        # Question counts and statistics
        'existing_count': preview.existing_count,
        'new_count': preview.new_count,
        'final_count': preview.final_count,
        
        # Conflict information
        'total_conflicts': len(preview.conflicts),
        'conflict_summary': preview.get_conflict_summary(),
        'conflicts_by_type': preview.merge_summary.get('conflict_breakdown', {}).get('by_type', {}),
        'conflicts_by_severity': preview.merge_summary.get('conflict_breakdown', {}).get('by_severity', {}),
        
        # Detailed merge information
        'merge_summary': preview.merge_summary,
        'statistics': preview.statistics,
        'warnings': preview.warnings,
        
        # Processing context from Phase 3A
        'file_info': processing_results.get('file_info', {}),
        'format_detected': processing_results.get('format_detected', 'Unknown'),
        'validation_passed': processing_results.get('validation_passed', False),
        
        # UI display data
        'conflict_details': [
            {
                'id': conflict.get_conflict_id(),
                'type': conflict.conflict_type.value,
                'severity': conflict.severity.value,
                'description': conflict.conflict_details,
                'suggestion': conflict.suggested_resolution,
                'similarity': round(conflict.similarity_score * 100, 1) if conflict.similarity_score > 0 else None,
                'existing_question': {
                    'id': conflict.existing_question.get('question_id', f"Q{conflict.existing_index + 1}"),
                    'text': conflict.existing_question.get('question_text', '')[:100] + '...' if len(conflict.existing_question.get('question_text', '')) > 100 else conflict.existing_question.get('question_text', ''),
                    'type': conflict.existing_question.get('type', 'unknown')
                },
                'new_question': {
                    'id': conflict.new_question.get('question_id', f"New Q{conflict.new_index + 1}"),
                    'text': conflict.new_question.get('question_text', '')[:100] + '...' if len(conflict.new_question.get('question_text', '')) > 100 else conflict.new_question.get('question_text', ''),
                    'type': conflict.new_question.get('type', 'unknown')
                }
            }
            for conflict in preview.conflicts
        ],
        
        # Recommendations and next steps
        'recommendations': preview.merge_summary.get('recommendations', []),
        'estimated_changes': preview.merge_summary.get('estimated_changes', {}),
        
        # Timestamps and metadata
        'preview_generated': datetime.now().isoformat(),
        'preview_valid': True
    }
    
    return preview_data


def update_session_state_after_merge(merge_result: MergeResult) -> Dict[str, Any]:
    """
    Update session state after successful merge.
    Integrates with Phase 3B for state management.
    
    Args:
        merge_result: Result from execute_database_merge()
        
    Returns:
        Dictionary of session state updates
    """
    
    updates = {}
    
    if merge_result.success:
        # Update core database state
        updates['df'] = merge_result.merged_df
        updates['original_questions'] = merge_result.merged_df.to_dict('records') if merge_result.merged_df is not None else []
        
        # Update metadata
        if 'metadata' not in updates:
            updates['metadata'] = {}
        
        updates['metadata'].update({
            'last_merge': merge_result.merge_metadata,
            'total_questions': len(merge_result.merged_df) if merge_result.merged_df is not None else 0,
            'last_updated': datetime.now().isoformat()
        })
        
        # Set success message
        strategy_name = merge_result.merge_preview.strategy.value.replace('_', ' ').title()
        updates['success_message'] = (
            f"Database merged successfully using {strategy_name} strategy. "
            f"Added {merge_result.merge_metadata.get('added_count', 0)} questions. "
            f"Total: {merge_result.merge_metadata.get('final_count', 0)} questions."
        )
        
        # Clear operation state
        updates['uploaded_files'] = []
        updates['processing_results'] = {}
        updates['preview_data'] = {}
        updates['error_message'] = ''
        
        # Set rollback data
        if merge_result.rollback_data:
            updates['rollback_point'] = merge_result.rollback_data
            updates['can_rollback'] = True
        
    else:
        # Handle merge failure
        updates['error_message'] = f"Merge failed: {merge_result.error_message}"
        # Don't clear other state on failure
    
    return updates


# Utility functions for conflict analysis
def analyze_conflicts_for_ui(conflicts: List[Conflict]) -> Dict[str, Any]:
    """
    Analyze conflicts for UI display.
    
    Args:
        conflicts: List of detected conflicts
        
    Returns:
        Dictionary with UI-friendly conflict analysis
    """
    
    if not conflicts:
        return {
            'has_conflicts': False,
            'total_count': 0,
            'severity_counts': {},
            'type_counts': {},
            'recommendations': ["No conflicts detected - merge can proceed safely"]
        }
    
    analysis = {
        'has_conflicts': True,
        'total_count': len(conflicts),
        'severity_counts': {},
        'type_counts': {},
        'high_priority_conflicts': [],
        'recommendations': []
    }
    
    # Count by severity and type
    for conflict in conflicts:
        severity = conflict.severity.value
        conflict_type = conflict.conflict_type.value
        
        analysis['severity_counts'][severity] = analysis['severity_counts'].get(severity, 0) + 1
        analysis['type_counts'][conflict_type] = analysis['type_counts'].get(conflict_type, 0) + 1
        
        # Flag high priority conflicts
        if conflict.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]:
            analysis['high_priority_conflicts'].append({
                'type': conflict_type,
                'severity': severity,
                'description': conflict.conflict_details,
                'suggestion': conflict.suggested_resolution
            })
    
    # Generate recommendations
    critical_count = analysis['severity_counts'].get('critical', 0)
    high_count = analysis['severity_counts'].get('high', 0)
    
    if critical_count > 0:
        analysis['recommendations'].append(f"⚠️ {critical_count} critical conflicts require immediate attention")
    
    if high_count > 0:
        analysis['recommendations'].append(f"⚡ {high_count} high-severity conflicts should be reviewed")
    
    id_conflicts = analysis['type_counts'].get('question_id', 0)
    if id_conflicts > 0:
        analysis['recommendations'].append(f"🆔 {id_conflicts} question ID conflicts detected")
    
    content_conflicts = analysis['type_counts'].get('content_duplicate', 0)
    if content_conflicts > 0:
        analysis['recommendations'].append(f"📝 {content_conflicts} content duplicates found")
    
    if not analysis['recommendations']:
        analysis['recommendations'].append("Conflicts detected but appear manageable")
    
    return analysis


def get_merge_strategy_description(strategy: MergeStrategy) -> Dict[str, str]:
    """
    Get user-friendly description of merge strategies.
    
    Args:
        strategy: MergeStrategy enum value
        
    Returns:
        Dictionary with title, description, and use_case
    """
    
    descriptions = {
        MergeStrategy.APPEND_ALL: {
            'title': 'Append All Questions',
            'description': 'Add all new questions to the database, including duplicates',
            'use_case': 'Use when you want to preserve all questions, even if they are duplicates',
            'pros': ['Simple and fast', 'No data loss', 'Preserves all information'],
            'cons': ['May create duplicate questions', 'Can lead to confusion', 'Larger database size']
        },
        MergeStrategy.SKIP_DUPLICATES: {
            'title': 'Skip Duplicate Questions',
            'description': 'Skip questions that are similar to existing ones',
            'use_case': 'Use when you want to avoid duplicate content in your database',
            'pros': ['Prevents duplicates', 'Cleaner database', 'Automatic conflict resolution'],
            'cons': ['May skip updated versions', 'Could miss important changes', 'Conservative approach']
        },
        MergeStrategy.REPLACE_DUPLICATES: {
            'title': 'Replace Duplicate Questions',
            'description': 'Replace existing questions with new versions when conflicts are detected',
            'use_case': 'Use when new questions are updated versions of existing ones',
            'pros': ['Updates existing content', 'Maintains database size', 'Keeps latest versions'],
            'cons': ['May lose original data', 'More complex operation', 'Risk of unintended changes']
        },
        MergeStrategy.RENAME_DUPLICATES: {
            'title': 'Rename Conflicting Questions',
            'description': 'Rename conflicting questions to avoid ID collisions',
            'use_case': 'Use when you want to keep both versions of similar questions',
            'pros': ['Preserves all data', 'Avoids ID conflicts', 'Allows manual review later'],
            'cons': ['Creates renamed questions', 'May need manual cleanup', 'Larger database']
        }
    }
    
    return descriptions.get(strategy, {
        'title': 'Unknown Strategy',
        'description': 'Unknown merge strategy',
        'use_case': 'Not recommended',
        'pros': [],
        'cons': ['Unknown behavior']
    })


# Global instance for easy access (similar to Phase 3B pattern)
default_merger = DatabaseMerger()


# Phase 3C Testing and Validation Functions
def validate_merge_result(result: MergeResult) -> List[str]:
    """
    Validate merge result for consistency and correctness.
    
    Args:
        result: MergeResult to validate
        
    Returns:
        List of validation issues (empty if all good)
    """
    issues = []
    
    if not result.success:
        if not result.error_message:
            issues.append("Failed merge result missing error message")
        return issues
    
    if result.merged_df is None:
        issues.append("Successful merge result missing merged DataFrame")
        return issues
    
    # Validate DataFrame structure
    if result.merged_df.empty:
        issues.append("Merged DataFrame is empty")
    
    # Check for required columns
    required_columns = ['question_text', 'correct_answer', 'type']
    missing_columns = [col for col in required_columns if col not in result.merged_df.columns]
    if missing_columns:
        issues.append(f"Merged DataFrame missing required columns: {missing_columns}")
    
    # Validate counts
    preview = result.merge_preview
    actual_count = len(result.merged_df)
    expected_count = preview.final_count
    
    if actual_count != expected_count:
        issues.append(f"Count mismatch: expected {expected_count}, got {actual_count}")
    
    # Check metadata consistency
    if not result.merge_metadata:
        issues.append("Missing merge metadata")
    
    return issues


def test_merge_compatibility(existing_df: pd.DataFrame, 
                           new_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Test compatibility between existing database and new questions.
    
    Args:
        existing_df: Existing database
        new_questions: New questions to test
        
    Returns:
        Compatibility report
    """
    
    report = {
        'compatible': True,
        'issues': [],
        'warnings': [],
        'recommendations': []
    }
    
    if existing_df.empty and not new_questions:
        report['issues'].append("Both existing database and new questions are empty")
        report['compatible'] = False
        return report
    
    if new_questions:
        # Check if new questions have basic required fields
        sample_question = new_questions[0]
        required_fields = ['question_text', 'correct_answer', 'type']
        
        missing_fields = [field for field in required_fields if field not in sample_question]
        if missing_fields:
            report['issues'].append(f"New questions missing required fields: {missing_fields}")
            report['compatible'] = False
    
    if not existing_df.empty:
        # Check column compatibility
        existing_columns = set(existing_df.columns)
        new_columns = set()
        
        for q in new_questions:
            new_columns.update(q.keys())
        
        # Check for major column differences
        if new_columns and not (new_columns & existing_columns):
            report['warnings'].append("No common columns between existing and new data")
            report['recommendations'].append("Review data structure compatibility")
    
    return report