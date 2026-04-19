"""
Alembic migration script for initial schema: Competitor, ReviewSentiment, KeywordRanking
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'competitors',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, unique=True, nullable=False),
        sa.Column('is_client', sa.Integer, default=0),
    )
    op.create_table(
        'review_sentiments',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('competitor_id', sa.Integer, sa.ForeignKey('competitors.id'), nullable=False),
        sa.Column('review_date', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('sentiment', sa.Float, nullable=False),
        sa.Column('review_text', sa.String),
    )
    op.create_table(
        'keyword_rankings',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('competitor_id', sa.Integer, sa.ForeignKey('competitors.id'), nullable=False),
        sa.Column('keyword', sa.String, nullable=False),
        sa.Column('ranking', sa.Integer, nullable=False),
        sa.Column('date', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('competitor_id', 'keyword', 'date', name='_competitor_keyword_date_uc'),
    )

def downgrade():
    op.drop_table('keyword_rankings')
    op.drop_table('review_sentiments')
    op.drop_table('competitors')
