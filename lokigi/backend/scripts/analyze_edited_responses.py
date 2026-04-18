#!/usr/bin/env python
"""
CLI Script: Analyze Edited Responses for Model Improvement
===========================================================

Usage:
    # Analyze specific user (last 90 days)
    python scripts/analyze_edited_responses.py --user-id <uuid> --days 90
    
    # Analyze all users (last 30 days)
    python scripts/analyze_edited_responses.py --all-users --days 30
    
    # Generate dataset for retraining
    python scripts/analyze_edited_responses.py --all-users --export-dataset model_training_data.jsonl
"""

import sys
import json
import argparse
from datetime import datetime
from uuid import UUID
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.nlp_edit_analysis import (
    analyze_user_edits,
    analyze_all_users_edits,
    analyze_single_edit,
)
from app.models import Review, GoogleConnection
from sqlalchemy import select, and_


def get_db_session() -> Session:
    """Create database session."""
    from app.database import get_db
    return next(get_db())


def main():
    parser = argparse.ArgumentParser(
        description="Analyze edited responses to improve AI model"
    )
    
    parser.add_argument(
        "--user-id",
        type=str,
        help="Analyze specific user (UUID format)"
    )
    
    parser.add_argument(
        "--all-users",
        action="store_true",
        help="Analyze ALL users (systemic patterns)"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Number of days to analyze (default: 90)"
    )
    
    parser.add_argument(
        "--export-dataset",
        type=str,
        help="Export dataset for model retraining as JSONL"
    )
    
    parser.add_argument(
        "--format",
        choices=['json', 'pretty', 'csv'],
        default='pretty',
        help="Output format"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.user_id and not args.all_users:
        print("❌ Error: Must provide either --user-id or --all-users")
        sys.exit(1)
    
    if args.user_id and args.all_users:
        print("❌ Error: Cannot use both --user-id and --all-users")
        sys.exit(1)
    
    try:
        db = get_db_session()
        
        if args.user_id:
            # Analyze specific user
            print(f"🔍 Analyzing edits for user {args.user_id} (last {args.days} days)...\n")
            
            result = analyze_user_edits(db, args.user_id, days=args.days)
            
            if args.format == 'json':
                print(json.dumps(result, indent=2))
            else:
                _print_user_analysis_pretty(result)
        
        else:
            # Analyze all users
            print(f"🔍 Analyzing ALL users' edits (last {args.days} days)...\n")
            
            result = analyze_all_users_edits(db, days=args.days)
            
            if args.format == 'json':
                print(json.dumps(result, indent=2))
            else:
                _print_all_users_analysis_pretty(result)
            
            # Export dataset if requested
            if args.export_dataset:
                _export_training_dataset(db, args.export_dataset, days=args.days)
    
    finally:
        db.close()


def _print_user_analysis_pretty(result: dict):
    """Pretty print user analysis results."""
    print("=" * 70)
    print(f"USER EDIT ANALYSIS")
    print("=" * 70)
    print(f"User ID: {result['user_id']}")
    print(f"Period: Last {result['period_days']} days")
    print(f"Total reviews: {result['total_reviews']}")
    print(f"Edited reviews: {result['edited_reviews']}")
    print(f"Edit rate: {result['edit_rate_pct']}%")
    
    if result.get('average_similarity_score'):
        print(f"Avg similarity (original vs edited): {result['average_similarity_score']}")
    
    print()
    print("=" * 70)
    print(f"ERROR PATTERNS ({len(result['error_patterns'])} types)")
    print("=" * 70)
    
    for i, error in enumerate(result['error_patterns'], 1):
        print(f"\n{i}. {error['error_type']} (frequency: {error['frequency']})")
        print(f"   Languages: {', '.join(error['languages'])}")
        print(f"   Ratings: {error['ratings']}")
        if error['sample_edits']:
            print(f"   Example: '{error['sample_edits'][0]['original'][:50]}...' → '{error['sample_edits'][0]['edited'][:50]}...'")
    
    print()
    print("=" * 70)
    print("SYSTEM PROMPT SUGGESTIONS")
    print("=" * 70)
    for suggestion in result['system_prompt_suggestions']:
        print(f"\n💡 {suggestion}")
    
    print("\n" + "=" * 70)


def _print_all_users_analysis_pretty(result: dict):
    """Pretty print all users analysis results."""
    print("=" * 70)
    print(f"SYSTEMIC EDIT ANALYSIS (ALL USERS)")
    print("=" * 70)
    print(f"Total edits analyzed: {result['total_edits_analyzed']}")
    print(f"Avg similarity score: {result['average_similarity_score']}")
    
    print()
    print("=" * 70)
    print(f"TOP 10 ERROR TYPES")
    print("=" * 70)
    
    for i, (error, count) in enumerate(sorted(
        result['most_common_errors'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10], 1):
        pct = count / result['total_edits_analyzed'] * 100
        print(f"{i:2}. {error:30} : {count:4} edits ({pct:5.1f}%)")
    
    print()
    print("=" * 70)
    print("DETECTED BIASES")
    print("=" * 70)
    
    for bias, count in sorted(
        result['most_common_biases'].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(f"- {bias}: {count} instances")
    
    print()
    print(result['recommended_prompt_overhaul'])


def _export_training_dataset(db: Session, output_file: str, days: int = 90):
    """Export dataset suitable for model retraining."""
    from datetime import timedelta
    
    print(f"\n📊 Exporting training dataset to {output_file}...")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all edits
    reviews = db.execute(
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
    
    # Convert to training format
    training_pairs = []
    for review in reviews:
        analysis = analyze_single_edit(review)
        if analysis:
            pair = {
                'original_response': analysis.original_reply,
                'edited_response': analysis.edited_reply,
                'rating': analysis.rating,
                'language': analysis.language,
                'error_types': analysis.error_categories,
                'bias_flags': analysis.bias_flags,
                'similarity_score': analysis.similarity_score,
            }
            training_pairs.append(pair)
    
    # Export as JSONL
    with open(output_file, 'w', encoding='utf-8') as f:
        for pair in training_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + '\n')
    
    print(f"✅ Exported {len(training_pairs)} training pairs")
    print(f"   Location: {output_file}")
    print(f"   Size: {len(training_pairs)} examples")
    print()
    print("Next steps:")
    print("1. Review the JSONL file for patterns")
    print("2. Use for fine-tuning your LLM (e.g., with OpenAI, Anthropic APIs)")
    print("3. Test improved model on sample reviews")


if __name__ == '__main__':
    main()
