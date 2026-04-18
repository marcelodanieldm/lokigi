"""
NLP Analysis Engine: Post-Churn Model Improvement
=================================================

Analyzes edited responses (reply_public_text vs reply_approved_text) to identify:
1. Common patterns in user edits
2. Recurring errors in AI-generated content
3. Biases in the language model
4. Suggestions for system prompt adjustments

Usage:
    python -m backend.scripts.analyze_edited_responses --user_id <uuid> --days 90
    or
    python -m backend.scripts.analyze_edited_responses --all-users --days 30
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import json
import re
from collections import Counter, defaultdict

import numpy as np
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

# NLP libraries
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from difflib import SequenceMatcher, unified_diff

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from app.models import Review, GoogleConnection


# ─────────────────────────────────────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class EditPattern:
    """Single edit pattern from user edits."""
    edit_type: str  # 'deletion', 'addition', 'substitution', 'reordering'
    original_text: str
    edited_text: str
    reason: Optional[str] = None
    frequency: int = 1
    
    def to_dict(self):
        return {
            'type': self.edit_type,
            'original': self.original_text,
            'edited': self.edited_text,
            'reason': self.reason,
            'frequency': self.frequency,
        }


@dataclass
class EditAnalysis:
    """Analysis of edits for a single review."""
    review_id: str
    original_reply: str
    edited_reply: str
    rating: int
    language: str
    author_name: str
    business_name: str
    
    # Edit patterns
    edit_patterns: list[EditPattern]
    edit_distance: float  # Levenshtein-like metric
    similarity_score: float  # 0-1, how similar original vs edited
    
    # Classification
    error_categories: list[str]  # e.g., ['tone_too_formal', 'missing_context']
    bias_flags: list[str]  # e.g., ['gender_assumption']
    
    def to_dict(self):
        return {
            'review_id': self.review_id,
            'original': self.original_reply,
            'edited': self.edited_reply,
            'rating': self.rating,
            'language': self.language,
            'author_name': self.author_name,
            'business_name': self.business_name,
            'edit_patterns': [p.to_dict() for p in self.edit_patterns],
            'similarity_score': round(self.similarity_score, 2),
            'edit_distance': round(self.edit_distance, 2),
            'error_categories': self.error_categories,
            'bias_flags': self.bias_flags,
        }


@dataclass
class ErrorPattern:
    """Aggregated error pattern across multiple reviews."""
    error_type: str
    description: str
    frequency: int
    affected_languages: list[str]
    affected_tones: list[str]
    affected_ratings: list[int]
    sample_edits: list[dict]  # Top 3 examples
    suggested_fix: str
    
    def to_dict(self):
        return {
            'error_type': self.error_type,
            'description': self.description,
            'frequency': self.frequency,
            'languages': self.affected_languages,
            'tones': self.affected_tones,
            'ratings': self.affected_ratings,
            'sample_edits': self.sample_edits[:3],
            'suggested_fix': self.suggested_fix,
        }


@dataclass
class BiasAnalysis:
    """Detected biases in the language model."""
    bias_type: str  # 'gender', 'assumptions', 'cultural', 'formality'
    description: str
    frequency: int
    examples: list[dict]
    impact: str  # 'high', 'medium', 'low'
    mitigation_strategy: str
    
    def to_dict(self):
        return {
            'bias_type': self.bias_type,
            'description': self.description,
            'frequency': self.frequency,
            'examples': self.examples[:2],
            'impact': self.impact,
            'mitigation': self.mitigation_strategy,
        }


# ─────────────────────────────────────────────────────────────────────────────
# EDIT DETECTION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────


def _similarity_ratio(a: str, b: str) -> float:
    """Calculate similarity between two strings (0-1)."""
    return SequenceMatcher(None, a, b).ratio()


def _detect_word_changes(original: str, edited: str) -> tuple[list[str], list[str]]:
    """
    Detect word-level additions, deletions, modifications.
    
    Returns:
        (removed_words, added_words)
    """
    orig_words = set(word_tokenize(original.lower()))
    edit_words = set(word_tokenize(edited.lower()))
    
    removed = list(orig_words - edit_words)
    added = list(edit_words - orig_words)
    
    return removed, added


def _detect_sentence_changes(original: str, edited: str) -> dict:
    """
    Detect sentence-level changes using diff.
    
    Returns:
        {'added_sentences': [], 'removed_sentences': [], 'modified_sentences': []}
    """
    orig_sents = sent_tokenize(original)
    edit_sents = sent_tokenize(edited)
    
    changes = {
        'added_sentences': [],
        'removed_sentences': [],
        'modified_sentences': []
    }
    
    diff = list(unified_diff(orig_sents, edit_sents, lineterm=''))
    for line in diff:
        if line.startswith('+ '):
            changes['added_sentences'].append(line[2:])
        elif line.startswith('- '):
            changes['removed_sentences'].append(line[2:])
    
    return changes


def _classify_tone_change(original: str, edited: str, language: str) -> Optional[str]:
    """
    Detect if the user changed the tone.
    
    Returns: 'more_formal', 'more_casual', 'added_emotion', 'removed_emotion', None
    """
    # Casual markers
    casual_patterns = {
        'es': [r'\bjeje\b', r'\b😊\b', r'\b🙌\b', r'\b¡\w+!', r'\bgracias\b', r'\bvuelve\b'],
        'en': [r'\bhaha\b', r'\b😊\b', r'\b🙌\b', r'\bthank you\b', r'\bcome back\b'],
    }
    
    # Formal markers
    formal_patterns = {
        'es': [r'\bestimado\b', r'\bapreciamos\b', r'\bconfirmar\b', r'\bsinceramento\b'],
        'en': [r'\bDear\b', r'\bwe appreciate\b', r'\bconfirm\b', r'\bsincerely\b'],
    }
    
    lang = language[:2] if language else 'es'
    
    casual_orig = len(re.findall('|'.join(casual_patterns.get(lang, [])), original, re.I))
    casual_edit = len(re.findall('|'.join(casual_patterns.get(lang, [])), edited, re.I))
    
    formal_orig = len(re.findall('|'.join(formal_patterns.get(lang, [])), original, re.I))
    formal_edit = len(re.findall('|'.join(formal_patterns.get(lang, [])), edited, re.I))
    
    if casual_edit > casual_orig + 1:
        return 'more_casual'
    if formal_edit > formal_orig + 1:
        return 'more_formal'
    if casual_edit + formal_edit > casual_orig + formal_orig:
        return 'added_emotion'
    
    return None


def _detect_personalization_issues(original: str, edited: str, author_name: str, business_name: str) -> list[str]:
    """
    Detect if user had to fix personalization issues (name, business, etc).
    
    Returns: List of issues detected
    """
    issues = []
    
    # Check if author name appears
    if author_name and author_name not in original and author_name in edited:
        issues.append('missing_author_name')
    
    # Check if business name appears
    if business_name and business_name not in original and business_name in edited:
        issues.append('missing_business_name')
    
    # Check for generic placeholders
    if '[author]' in original or '{author}' in original:
        issues.append('unresolved_author_placeholder')
    if '[business]' in original or '{business}' in original:
        issues.append('unresolved_business_placeholder')
    
    return issues


def _detect_language_issues(original: str, edited: str, language: str) -> list[str]:
    """
    Detect language quality issues.
    
    Returns: List of issue types
    """
    issues = []
    
    # Grammar patterns (simplified)
    grammar_issues = {
        'es': [
            (r'que\s+que', 'double_que'),
            (r'accion', 'missing_accent'),  # Should be "acción"
            (r'informacion', 'missing_accent'),  # Should be "información"
        ],
        'en': [
            (r'their\s+their', 'double_word'),
            (r'recieved', 'spelling_error'),  # Should be "received"
        ]
    }
    
    lang = language[:2] if language else 'es'
    
    if original:
        for pattern, issue_type in grammar_issues.get(lang, []):
            if re.search(pattern, original, re.I):
                if edited and not re.search(pattern, edited, re.I):
                    issues.append(f'fixed_{issue_type}')
    
    return issues


def _detect_bias_patterns(original: str, edited: str, rating: int) -> list[dict]:
    """
    Detect potential biases in the original response.
    
    Returns: List of bias detections
    """
    biases = []
    
    # Gender assumptions
    gender_assumptions = {
        'es': [
            (r'señora\s+\w+', 'assumed_female_title'),
            (r'señor\s+\w+', 'assumed_male_title'),
        ],
        'en': [
            (r'Mr\.\s+\w+', 'assumed_male_title'),
            (r'Mrs\.\s+\w+', 'assumed_female_title'),
        ]
    }
    
    # Inappropriate assumptions
    inappropriate = {
        'es': [
            (r'seguro que eres', 'assumption_about_user'),
            (r'obviamente', 'condescending'),
        ],
        'en': [
            (r"I'm sure you", 'assumption_about_user'),
            (r'obviously', 'condescending'),
        ]
    }
    
    for pattern, bias_type in gender_assumptions.get('es', []):
        if re.search(pattern, original, re.I) and not re.search(pattern, edited, re.I):
            biases.append({
                'type': 'gender_bias',
                'subtype': bias_type,
                'original': original,
                'edited': edited,
            })
    
    for pattern, bias_type in inappropriate.get('es', []):
        if re.search(pattern, original, re.I) and not re.search(pattern, edited, re.I):
            biases.append({
                'type': 'inappropriate_assumption',
                'subtype': bias_type,
                'original': original,
                'edited': edited,
            })
    
    return biases


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ANALYSIS FUNCTION
# ─────────────────────────────────────────────────────────────────────────────


def analyze_single_edit(review: Review) -> Optional[EditAnalysis]:
    """
    Analyze a single edited review.
    
    Args:
        review: Review object with both reply_public_text and reply_approved_text
        
    Returns:
        EditAnalysis or None if no edit found
    """
    # Skip if no edit happened
    if not review.reply_public_text or not review.reply_approved_text:
        return None
    
    if review.reply_public_text == review.reply_approved_text:
        return None  # No actual edit
    
    original = review.reply_public_text.strip()
    edited = review.reply_approved_text.strip()
    
    # Calculate similarity
    similarity = _similarity_ratio(original, edited)
    
    # Detect changes
    removed_words, added_words = _detect_word_changes(original, edited)
    sentence_changes = _detect_sentence_changes(original, edited)
    
    # Classify errors
    error_categories = []
    
    # Tone change detection
    tone_change = _classify_tone_change(original, edited, review.reply_detected_language)
    if tone_change:
        error_categories.append(tone_change)
    
    # Personalization issues
    personalization_issues = _detect_personalization_issues(
        original, edited,
        review.author_display_name or "",
        "Business"  # TODO: get from connection
    )
    error_categories.extend(personalization_issues)
    
    # Language issues
    language_issues = _detect_language_issues(original, edited, review.reply_detected_language)
    error_categories.extend(language_issues)
    
    # Detect biases
    bias_flags = _detect_bias_patterns(original, edited, review.rating or 0)
    bias_flag_types = [b.get('type') for b in bias_flags]
    
    # Create edit patterns
    edit_patterns = []
    
    if removed_words:
        edit_patterns.append(EditPattern(
            edit_type='deletion',
            original_text=', '.join(removed_words[:5]),
            edited_text='',
            frequency=len(removed_words)
        ))
    
    if added_words:
        edit_patterns.append(EditPattern(
            edit_type='addition',
            original_text='',
            edited_text=', '.join(added_words[:5]),
            frequency=len(added_words)
        ))
    
    # Calculate edit distance
    edit_distance = 1.0 - similarity
    
    return EditAnalysis(
        review_id=str(review.id),
        original_reply=original,
        edited_reply=edited,
        rating=review.rating or 0,
        language=review.reply_detected_language or 'unknown',
        author_name=review.author_display_name or 'unknown',
        business_name='Business',  # TODO
        edit_patterns=edit_patterns,
        edit_distance=edit_distance,
        similarity_score=similarity,
        error_categories=list(set(error_categories)),
        bias_flags=bias_flag_types,
    )


def analyze_user_edits(
    db: Session,
    user_id: str,
    days: int = 90,
) -> dict:
    """
    Analyze all edited reviews for a user over N days.
    
    Returns:
        {
            'user_id': str,
            'period_days': int,
            'total_reviews': int,
            'edited_reviews': int,
            'edit_rate_pct': float,
            'error_patterns': [ErrorPattern],
            'bias_analysis': [BiasAnalysis],
            'system_prompt_suggestions': [str],
            'sample_edits': [EditAnalysis],
        }
    """
    from uuid import UUID
    
    user_uuid = UUID(user_id)
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all reviews for user
    reviews = db.execute(
        select(Review)
        .join(GoogleConnection, Review.connection_id == GoogleConnection.id)
        .where(
            and_(
                GoogleConnection.user_id == user_uuid,
                Review.reply_sent_at >= cutoff_date,
                Review.reply_sent_at.isnot(None),
            )
        )
        .order_by(Review.reply_sent_at.desc())
    ).scalars().all()
    
    # Analyze edits
    edits = []
    for review in reviews:
        analysis = analyze_single_edit(review)
        if analysis:
            edits.append(analysis)
    
    if not edits:
        return {
            'user_id': user_id,
            'period_days': days,
            'total_reviews': len(reviews),
            'edited_reviews': 0,
            'edit_rate_pct': 0.0,
            'error_patterns': [],
            'bias_analysis': [],
            'system_prompt_suggestions': ['No edits found for this user.'],
            'sample_edits': [],
        }
    
    # Aggregate error patterns
    error_counter = Counter()
    error_details = defaultdict(lambda: {
        'languages': set(),
        'ratings': set(),
        'examples': []
    })
    
    for edit in edits:
        for error in edit.error_categories:
            error_counter[error] += 1
            error_details[error]['languages'].add(edit.language)
            error_details[error]['ratings'].add(edit.rating)
            error_details[error]['examples'].append({
                'original': edit.original_reply[:100],
                'edited': edit.edited_reply[:100],
            })
    
    # Aggregate bias patterns
    bias_counter = Counter()
    bias_details = defaultdict(lambda: {'examples': []})
    
    for edit in edits:
        for bias_flag in edit.bias_flags:
            bias_counter[bias_flag] += 1
    
    # Generate suggestions
    suggestions = _generate_system_prompt_suggestions(error_counter, bias_counter, edits)
    
    return {
        'user_id': user_id,
        'period_days': days,
        'total_reviews': len(reviews),
        'edited_reviews': len(edits),
        'edit_rate_pct': round(len(edits) / len(reviews) * 100, 1) if reviews else 0.0,
        'average_similarity_score': round(
            np.mean([e.similarity_score for e in edits]), 2
        ),
        'error_patterns': [
            {
                'error_type': error,
                'frequency': count,
                'languages': list(error_details[error]['languages']),
                'ratings': list(error_details[error]['ratings']),
                'sample_edits': error_details[error]['examples'][:2],
            }
            for error, count in error_counter.most_common(10)
        ],
        'system_prompt_suggestions': suggestions,
        'sample_edits': [e.to_dict() for e in edits[:5]],
    }


def _generate_system_prompt_suggestions(
    error_counter: Counter,
    bias_counter: Counter,
    edits: list[EditAnalysis]
) -> list[str]:
    """
    Generate specific suggestions for system prompt based on errors.
    
    Returns:
        List of actionable suggestions
    """
    suggestions = []
    
    # Tone issues
    if 'more_formal' in dict(error_counter):
        suggestions.append(
            "TONE: Model generates overly formal responses. Consider adjusting tone prompt to be warmer and more personable, especially for mid-to-high ratings."
        )
    
    if 'more_casual' in dict(error_counter):
        suggestions.append(
            "TONE: Model generates responses that are too casual. Ensure professionalism is maintained, especially for critical feedback."
        )
    
    # Missing personalization
    if 'missing_author_name' in dict(error_counter):
        suggestions.append(
            "PERSONALIZATION: Model is missing author names. Ensure the system prompt emphasizes addressing the reviewer by name in every response."
        )
    
    if 'missing_business_name' in dict(error_counter):
        suggestions.append(
            "PERSONALIZATION: Model is missing business name in responses. Instruct model to reference business name naturally."
        )
    
    # Language quality
    if error_counter.get('missing_accent', 0) > 2:
        suggestions.append(
            "LANGUAGE: Model has spelling/accent issues in Spanish. Add example of correct Spanish accents to prompt."
        )
    
    # Bias mitigation
    if bias_counter.get('gender_bias', 0) > 0:
        suggestions.append(
            "BIAS: Detected gender assumptions in responses. Add instruction to avoid gendered language and use neutral terms."
        )
    
    if bias_counter.get('inappropriate_assumption', 0) > 0:
        suggestions.append(
            "BIAS: Model making inappropriate assumptions about users. Ensure prompt instructs model to remain neutral and not presume."
        )
    
    # Generic fallback
    if not suggestions:
        suggestions.append(
            "No major issues detected. Continue monitoring edit patterns for incremental improvements."
        )
    
    return suggestions


# ─────────────────────────────────────────────────────────────────────────────
# BATCH ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────


def analyze_all_users_edits(
    db: Session,
    days: int = 30,
    min_edits: int = 5,
) -> dict:
    """
    Analyze edits across ALL users to find systemic patterns.
    
    Returns:
        {
            'total_users_analyzed': int,
            'users_with_edits': int,
            'average_edit_rate_pct': float,
            'top_error_patterns': [ErrorPattern],
            'systemic_biases': [BiasAnalysis],
            'recommended_prompt_overhaul': str,
        }
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all reviews with edits
    all_edits = db.execute(
        select(Review)
        .where(
            and_(
                Review.reply_public_text.isnot(None),
                Review.reply_approved_text.isnot(None),
                Review.reply_approved_text != Review.reply_public_text,
                Review.reply_sent_at >= cutoff_date,
            )
        )
    ).scalars().all()
    
    # Analyze all
    analyses = []
    for review in all_edits:
        analysis = analyze_single_edit(review)
        if analysis:
            analyses.append(analysis)
    
    if not analyses:
        return {
            'total_users_analyzed': 0,
            'users_with_edits': 0,
            'average_edit_rate_pct': 0.0,
            'top_error_patterns': [],
            'systemic_biases': [],
            'recommended_prompt_overhaul': 'No edit data available.',
        }
    
    # Aggregate errors
    error_counter = Counter()
    for analysis in analyses:
        error_counter.update(analysis.error_categories)
    
    # Aggregate biases
    bias_counter = Counter()
    for analysis in analyses:
        bias_counter.update(analysis.bias_flags)
    
    # Rating distribution
    avg_similarity = np.mean([a.similarity_score for a in analyses])
    
    # Recommended overhaul
    overhaul = _generate_prompt_overhaul(error_counter, bias_counter, len(analyses))
    
    return {
        'total_edits_analyzed': len(analyses),
        'average_similarity_score': round(avg_similarity, 2),
        'most_common_errors': dict(error_counter.most_common(10)),
        'most_common_biases': dict(bias_counter.most_common(5)),
        'recommended_prompt_overhaul': overhaul,
    }


def _generate_prompt_overhaul(
    error_counter: Counter,
    bias_counter: Counter,
    total_edits: int
) -> str:
    """Generate recommendations for complete prompt overhaul."""
    
    sections = []
    
    # Calculate percentages
    total_errors = sum(error_counter.values())
    
    if total_errors > 0:
        error_pct = {k: v/total_errors*100 for k, v in error_counter.items()}
        
        # Top issues
        top_issues = sorted(error_pct.items(), key=lambda x: x[1], reverse=True)[:3]
        sections.append("## Top Issues by Frequency:")
        for issue, pct in top_issues:
            sections.append(f"- {issue}: {pct:.1f}% of edits")
    
    # Bias summary
    if bias_counter:
        sections.append("\n## Detected Biases:")
        for bias, count in bias_counter.most_common(3):
            sections.append(f"- {bias}: {count} instances")
    
    # Recommended changes
    sections.append("\n## Recommended System Prompt Changes:")
    sections.append("1. **Emphasis on Personalization**: Always include reviewer name and business name")
    sections.append("2. **Tone Calibration**: Adjust formality based on rating (high=warm, low=professional)")
    sections.append("3. **Bias Mitigation**: Remove gendered language, avoid assumptions")
    sections.append("4. **Language Quality**: Ensure proper grammar and accents for all supported languages")
    sections.append("5. **Brevity**: Responses should be concise but complete")
    
    return '\n'.join(sections)
