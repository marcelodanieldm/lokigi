#!/usr/bin/env python
"""
Example: Running the NLP Edit Analysis
======================================

This example shows how to use the NLP analysis engine in your code.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# For demo purposes only - use your actual database
# from app.database import get_db


def example_1_single_user_analysis():
    """Example 1: Analyze a specific user's edits."""
    print("=" * 70)
    print("EXAMPLE 1: Analyze Single User")
    print("=" * 70)
    
    # from app.nlp_edit_analysis import analyze_user_edits
    # from app.database import get_db
    # from uuid import UUID
    
    # user_id = "123e4567-e89b-12d3-a456-426614174000"
    # db = next(get_db())
    
    # result = analyze_user_edits(db, user_id, days=90)
    
    # print(f"User: {result['user_id']}")
    # print(f"Period: {result['period_days']} days")
    # print(f"Total reviews: {result['total_reviews']}")
    # print(f"Edited reviews: {result['edited_reviews']}")
    # print(f"Edit rate: {result['edit_rate_pct']}%")
    # print()
    # print("Top error patterns:")
    # for error in result['error_patterns'][:5]:
    #     print(f"  - {error['error_type']}: {error['frequency']} times")
    # print()
    # print("Suggestions:")
    # for suggestion in result['system_prompt_suggestions']:
    #     print(f"  💡 {suggestion}")
    
    print("✅ See script for usage with actual database")


def example_2_systemic_analysis():
    """Example 2: Analyze all users to find systemic issues."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Systemic Analysis (All Users)")
    print("=" * 70)
    
    # from app.nlp_edit_analysis import analyze_all_users_edits
    # from app.database import get_db
    
    # db = next(get_db())
    # result = analyze_all_users_edits(db, days=30)
    
    # print(f"Total edits analyzed: {result['total_edits_analyzed']}")
    # print(f"Average similarity: {result['average_similarity_score']}")
    # print()
    # print("Most common errors:")
    # for error, count in sorted(result['most_common_errors'].items(), 
    #                             key=lambda x: x[1], reverse=True)[:5]:
    #     pct = count / result['total_edits_analyzed'] * 100
    #     print(f"  - {error}: {count} ({pct:.1f}%)")
    # print()
    # print("Detected biases:")
    # for bias, count in sorted(result['most_common_biases'].items(),
    #                           key=lambda x: x[1], reverse=True):
    #     print(f"  - {bias}: {count} instances")
    
    print("✅ See script for usage with actual database")


def example_3_analyzing_single_edit():
    """Example 3: Analyze a single edit in detail."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Analyze Single Edit")
    print("=" * 70)
    
    # from app.nlp_edit_analysis import analyze_single_edit
    # from app.models import Review
    # from app.database import get_db
    
    # db = next(get_db())
    # review = db.query(Review).filter(
    #     Review.reply_public_text != Review.reply_approved_text
    # ).first()
    
    # if review:
    #     analysis = analyze_single_edit(review)
    #     
    #     print(f"Review ID: {analysis.review_id}")
    #     print(f"Rating: {analysis.rating} stars")
    #     print(f"Language: {analysis.language}")
    #     print(f"Similarity: {analysis.similarity_score:.2%}")
    #     print()
    #     print("Original:")
    #     print(f"  {analysis.original_reply}")
    #     print()
    #     print("Edited:")
    #     print(f"  {analysis.edited_reply}")
    #     print()
    #     print(f"Error categories: {', '.join(analysis.error_categories)}")
    #     print(f"Bias flags: {', '.join(analysis.bias_flags)}")
    
    print("✅ See script for usage with actual database")


def example_4_export_training_data():
    """Example 4: Export data for model retraining."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Export Training Dataset")
    print("=" * 70)
    
    # from app.nlp_edit_analysis import analyze_single_edit
    # from app.models import Review
    # from app.database import get_db
    # from datetime import datetime, timedelta
    # from sqlalchemy import select, and_
    # import json
    # from pathlib import Path
    
    # db = next(get_db())
    # days = 90
    # cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # # Get all edits
    # reviews = db.execute(
    #     select(Review)
    #     .where(
    #         and_(
    #             Review.reply_public_text.isnot(None),
    #             Review.reply_approved_text.isnot(None),
    #             Review.reply_approved_text != Review.reply_public_text,
    #             Review.reply_sent_at >= cutoff_date,
    #         )
    #     )
    # ).scalars().all()
    
    # # Convert to training format
    # training_pairs = []
    # for review in reviews:
    #     analysis = analyze_single_edit(review)
    #     if analysis:
    #         pair = {
    #             'original_response': analysis.original_reply,
    #             'edited_response': analysis.edited_reply,
    #             'rating': analysis.rating,
    #             'language': analysis.language,
    #             'error_types': analysis.error_categories,
    #             'bias_flags': analysis.bias_flags,
    #             'similarity_score': round(analysis.similarity_score, 3),
    #         }
    #         training_pairs.append(pair)
    
    # # Export as JSONL
    # output_file = Path("training_data_export.jsonl")
    # with open(output_file, 'w', encoding='utf-8') as f:
    #     for pair in training_pairs:
    #         f.write(json.dumps(pair, ensure_ascii=False) + '\n')
    
    # print(f"✅ Exported {len(training_pairs)} training pairs")
    # print(f"📄 Location: {output_file}")
    
    print("✅ See script for usage with actual database")


def example_5_tracking_edits_over_time():
    """Example 5: Track how edit patterns evolve."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Track Edits Over Time")
    print("=" * 70)
    
    # from app.nlp_edit_analysis import analyze_user_edits
    # from app.database import get_db
    
    # db = next(get_db())
    # user_id = "123e4567-e89b-12d3-a456-426614174000"
    
    # # Week 1
    # week1 = analyze_user_edits(db, user_id, days=7)
    # print(f"Week 1 edit rate: {week1['edit_rate_pct']}%")
    
    # # Week 2
    # week2 = analyze_user_edits(db, user_id, days=14)
    # print(f"Week 2 edit rate: {week2['edit_rate_pct']}%")
    
    # # Week 3
    # week3 = analyze_user_edits(db, user_id, days=21)
    # print(f"Week 3 edit rate: {week3['edit_rate_pct']}%")
    
    # print()
    # print("If edit rate is decreasing over time:")
    # print("✅ Users are getting more comfortable with AI suggestions")
    # print("✅ Onboarding is progressing well")
    
    print("✅ See script for usage with actual database")


def example_6_monitoring_bias():
    """Example 6: Monitor for bias in responses."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Monitor Bias Detection")
    print("=" * 70)
    
    # from app.nlp_edit_analysis import analyze_all_users_edits
    # from app.database import get_db
    
    # db = next(get_db())
    # result = analyze_all_users_edits(db, days=30)
    
    # biases = result['most_common_biases']
    
    # if not biases:
    #     print("✅ No bias detected - model is performing well")
    # else:
    #     print("⚠️ Biases detected:")
    #     for bias_type, count in biases.items():
    #         print(f"  - {bias_type}: {count} instances")
    #     print()
    #     print("Recommended action:")
    #     print("1. Review examples of each bias")
    #     print("2. Update system prompt with bias mitigation")
    #     print("3. Run A/B test with updated prompt")
    
    print("✅ See script for usage with actual database")


def main():
    """Run all examples."""
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║        NLP Edit Analysis - Usage Examples                             ║
║        Lokigi AI Review Engine Model Improvement                       ║
╚════════════════════════════════════════════════════════════════════════╝

These examples demonstrate how to use the analysis engine.

Note: Uncomment the code in each example to run with your actual database.
    """)
    
    example_1_single_user_analysis()
    example_2_systemic_analysis()
    example_3_analyzing_single_edit()
    example_4_export_training_data()
    example_5_tracking_edits_over_time()
    example_6_monitoring_bias()
    
    print("\n" + "=" * 70)
    print("QUICK START")
    print("=" * 70)
    print("""
1. CLI Usage (Recommended for Data Scientists):
   python scripts/analyze_edited_responses.py --all-users --days 30
   
2. API Usage (For Dashboards):
   curl http://localhost:8000/api/nlp/systemic-analysis?days=30
   
3. Python Integration (For Backend):
   from app.nlp_edit_analysis import analyze_all_users_edits
   result = analyze_all_users_edits(db, days=30)
   print(result['recommended_prompt_overhaul'])
    """)


if __name__ == '__main__':
    main()
