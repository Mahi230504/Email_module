"""
Database connection and session management.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import redis
from elasticsearch import Elasticsearch

from app.config import get_settings

settings = get_settings()

# SQLAlchemy Engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug
)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Redis Client
def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    return redis.from_url(settings.redis_url, decode_responses=True)


# Elasticsearch Client
def get_elasticsearch_client() -> Elasticsearch:
    """Get Elasticsearch client instance."""
    return Elasticsearch(
        hosts=[{
            'host': settings.elasticsearch_host,
            'port': settings.elasticsearch_port,
            'scheme': 'http'
        }]
    )


# Initialize clients
redis_client = get_redis_client()
es_client = get_elasticsearch_client()
