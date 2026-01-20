"""
Search service for Elasticsearch integration.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import es_client
from app.config import get_settings
from models.email import Email
from models.client import Client

settings = get_settings()


class SearchService:
    """Elasticsearch-based search service for emails."""
    
    INDEX_NAME = "emails"
    
    def __init__(self, db: Session):
        """
        Initialize search service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.es = es_client
        
        # Ensure index exists
        self._ensure_index()
    
    def _ensure_index(self) -> None:
        """Create Elasticsearch index if it doesn't exist."""
        try:
            if not self.es.indices.exists(index=self.INDEX_NAME):
                self.es.indices.create(
                    index=self.INDEX_NAME,
                    body={
                        "settings": {
                            "number_of_shards": 1,
                            "number_of_replicas": 0,
                            "analysis": {
                                "analyzer": {
                                    "email_analyzer": {
                                        "type": "custom",
                                        "tokenizer": "standard",
                                        "filter": ["lowercase", "stop", "snowball"]
                                    }
                                }
                            }
                        },
                        "mappings": {
                            "properties": {
                                "email_id": {"type": "keyword"},
                                "thread_id": {"type": "keyword"},
                                "user_id": {"type": "keyword"},
                                "client_id": {"type": "keyword"},
                                "subject": {
                                    "type": "text",
                                    "analyzer": "email_analyzer",
                                    "fields": {
                                        "keyword": {"type": "keyword"}
                                    }
                                },
                                "body": {
                                    "type": "text",
                                    "analyzer": "email_analyzer"
                                },
                                "from_address": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {"type": "keyword"}
                                    }
                                },
                                "from_name": {"type": "text"},
                                "to_recipients": {"type": "keyword"},
                                "cc_recipients": {"type": "keyword"},
                                "email_type": {"type": "keyword"},
                                "direction": {"type": "keyword"},
                                "received_date_time": {"type": "date"},
                                "has_attachments": {"type": "boolean"},
                                "is_read": {"type": "boolean"},
                                "is_flagged": {"type": "boolean"},
                            }
                        }
                    }
                )
        except Exception as e:
            print(f"Warning: Could not create Elasticsearch index: {e}")
    
    def index_email(self, email: Email) -> bool:
        """
        Index a single email to Elasticsearch.
        
        Args:
            email: Email model instance
            
        Returns:
            True if successful
        """
        try:
            doc = {
                "email_id": email.id,
                "thread_id": email.thread_id,
                "user_id": email.user_id,
                "client_id": email.client_id,
                "subject": email.subject,
                "body": email.body or email.body_preview or "",
                "from_address": email.from_address,
                "from_name": email.from_name,
                "to_recipients": email.to_recipients or [],
                "cc_recipients": email.cc_recipients or [],
                "email_type": email.email_type,
                "direction": email.direction,
                "received_date_time": email.received_date_time.isoformat() if email.received_date_time else None,
                "has_attachments": email.has_attachments,
                "is_read": email.is_read,
                "is_flagged": email.is_flagged,
            }
            
            self.es.index(
                index=self.INDEX_NAME,
                id=email.id,
                document=doc
            )
            
            return True
            
        except Exception as e:
            print(f"Error indexing email {email.id}: {e}")
            return False
    
    def search_emails(
        self,
        user_id: str,
        query: str,
        email_type: Optional[str] = None,
        client_id: Optional[str] = None,
        from_address: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        is_read: Optional[bool] = None,
        has_attachments: Optional[bool] = None,
        direction: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Full-text search across emails.
        
        Args:
            user_id: Current user ID
            query: Search query
            ... filters
            
        Returns:
            Search results with total count
        """
        try:
            # Build Elasticsearch query
            must_clauses = [
                {"term": {"user_id": user_id}},
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["subject^3", "body", "from_address^2", "from_name"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                }
            ]
            
            # Add filters
            filter_clauses = []
            
            if email_type:
                filter_clauses.append({"term": {"email_type": email_type}})
            
            if client_id:
                filter_clauses.append({"term": {"client_id": client_id}})
            
            if from_address:
                filter_clauses.append({"term": {"from_address.keyword": from_address}})
            
            if is_read is not None:
                filter_clauses.append({"term": {"is_read": is_read}})
            
            if has_attachments is not None:
                filter_clauses.append({"term": {"has_attachments": has_attachments}})
            
            if direction:
                filter_clauses.append({"term": {"direction": direction}})
            
            # Date range
            if date_from or date_to:
                date_range = {}
                if date_from:
                    date_range["gte"] = date_from.isoformat()
                if date_to:
                    date_range["lte"] = date_to.isoformat()
                filter_clauses.append({"range": {"received_date_time": date_range}})
            
            # Build final query
            es_query = {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses
                }
            }
            
            # Execute search
            result = self.es.search(
                index=self.INDEX_NAME,
                body={
                    "query": es_query,
                    "from": offset,
                    "size": limit,
                    "sort": [
                        {"_score": "desc"},
                        {"received_date_time": "desc"}
                    ],
                    "highlight": {
                        "fields": {
                            "subject": {},
                            "body": {"fragment_size": 150}
                        }
                    }
                }
            )
            
            # Parse results
            hits = result["hits"]["hits"]
            total = result["hits"]["total"]["value"]
            
            emails = []
            for hit in hits:
                source = hit["_source"]
                email_data = {
                    "id": source["email_id"],
                    "thread_id": source.get("thread_id"),
                    "subject": source.get("subject"),
                    "from_address": source.get("from_address"),
                    "from_name": source.get("from_name"),
                    "email_type": source.get("email_type"),
                    "direction": source.get("direction"),
                    "received_date_time": source.get("received_date_time"),
                    "has_attachments": source.get("has_attachments"),
                    "is_read": source.get("is_read"),
                    "score": hit["_score"],
                }
                
                # Add highlights
                if "highlight" in hit:
                    email_data["highlights"] = hit["highlight"]
                
                emails.append(email_data)
            
            return {
                "total": total,
                "query": query,
                "limit": limit,
                "offset": offset,
                "results": emails
            }
            
        except Exception as e:
            print(f"Elasticsearch search error: {e}")
            
            # Fallback to database search
            return self._database_search(
                user_id=user_id,
                query=query,
                email_type=email_type,
                client_id=client_id,
                limit=limit,
                offset=offset
            )
    
    def _database_search(
        self,
        user_id: str,
        query: str,
        email_type: Optional[str] = None,
        client_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Fallback PostgreSQL search if Elasticsearch is unavailable."""
        search_term = f"%{query}%"
        
        db_query = self.db.query(Email).filter(
            Email.user_id == user_id,
            (Email.subject.ilike(search_term)) |
            (Email.body_preview.ilike(search_term)) |
            (Email.from_address.ilike(search_term))
        )
        
        if email_type:
            db_query = db_query.filter(Email.email_type == email_type)
        
        if client_id:
            db_query = db_query.filter(Email.client_id == client_id)
        
        total = db_query.count()
        
        emails = db_query.order_by(
            Email.received_date_time.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "total": total,
            "query": query,
            "limit": limit,
            "offset": offset,
            "results": [e.to_dict(include_body=False) for e in emails],
            "source": "database"
        }
    
    def get_suggestions(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> Dict[str, List[str]]:
        """Get search suggestions based on partial query."""
        try:
            # Get subject suggestions
            subject_result = self.es.search(
                index=self.INDEX_NAME,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"user_id": user_id}},
                                {"prefix": {"subject.keyword": query.lower()}}
                            ]
                        }
                    },
                    "size": 0,
                    "aggs": {
                        "subjects": {
                            "terms": {
                                "field": "subject.keyword",
                                "size": limit
                            }
                        }
                    }
                }
            )
            
            subjects = [
                bucket["key"]
                for bucket in subject_result["aggregations"]["subjects"]["buckets"]
            ]
            
            # Get sender suggestions
            sender_result = self.es.search(
                index=self.INDEX_NAME,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"user_id": user_id}},
                                {"prefix": {"from_address.keyword": query.lower()}}
                            ]
                        }
                    },
                    "size": 0,
                    "aggs": {
                        "senders": {
                            "terms": {
                                "field": "from_address.keyword",
                                "size": limit
                            }
                        }
                    }
                }
            )
            
            senders = [
                bucket["key"]
                for bucket in sender_result["aggregations"]["senders"]["buckets"]
            ]
            
            return {
                "subjects": subjects,
                "senders": senders
            }
            
        except Exception:
            return {"subjects": [], "senders": []}
    
    def get_filter_options(self, user_id: str) -> Dict[str, Any]:
        """Get available filter options for search."""
        # Get unique email types
        email_types = self.db.query(Email.email_type).filter(
            Email.user_id == user_id,
            Email.email_type.isnot(None)
        ).distinct().all()
        
        # Get unique senders
        senders = self.db.query(Email.from_address, Email.from_name).filter(
            Email.user_id == user_id
        ).distinct().limit(100).all()
        
        # Get clients
        clients = self.db.query(Client).limit(100).all()
        
        return {
            "email_types": [t[0] for t in email_types if t[0]],
            "senders": [
                {"address": s[0], "name": s[1]}
                for s in senders if s[0]
            ],
            "clients": [
                {"id": c.id, "name": c.name}
                for c in clients
            ],
            "directions": ["incoming", "outgoing"]
        }
    
    def reindex_user_emails(self, user_id: str) -> Dict[str, Any]:
        """Reindex all emails for a user."""
        emails = self.db.query(Email).filter(
            Email.user_id == user_id
        ).all()
        
        indexed = 0
        errors = 0
        
        for email in emails:
            if self.index_email(email):
                indexed += 1
            else:
                errors += 1
        
        return {
            "message": "Reindexing complete",
            "total": len(emails),
            "indexed": indexed,
            "errors": errors
        }
    
    def delete_email_index(self, email_id: str) -> bool:
        """Delete an email from the search index."""
        try:
            self.es.delete(index=self.INDEX_NAME, id=email_id)
            return True
        except Exception:
            return False
