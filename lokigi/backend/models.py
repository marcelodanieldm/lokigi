from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Competitor(Base):
    __tablename__ = "competitors"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    is_client = Column(Integer, default=0)  # 1=cliente, 0=competidor
    reviews = relationship("ReviewSentiment", back_populates="competitor", cascade="all, delete-orphan")
    keywords = relationship("KeywordRanking", back_populates="competitor", cascade="all, delete-orphan")

class ReviewSentiment(Base):
    __tablename__ = "review_sentiments"
    id = Column(Integer, primary_key=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False)
    review_date = Column(DateTime, default=datetime.utcnow)
    sentiment = Column(Float, nullable=False)  # -1 a 1
    review_text = Column(String)
    competitor = relationship("Competitor", back_populates="reviews")

class KeywordRanking(Base):
    __tablename__ = "keyword_rankings"
    id = Column(Integer, primary_key=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False)
    keyword = Column(String, nullable=False)
    ranking = Column(Integer, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    competitor = relationship("Competitor", back_populates="keywords")
    __table_args__ = (UniqueConstraint('competitor_id', 'keyword', 'date', name='_competitor_keyword_date_uc'),)
