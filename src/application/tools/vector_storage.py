"""
Vector Storage Tool for AI Invest platform.

Provides vector operations including embedding generation and similarity search.
"""
import os
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import openai
from openai import OpenAI

from .base_tool import BaseTool, ToolResult, ToolStatus
from ...domain.entities.vector_document import VectorDocument, VectorSourceType
from ...infrastructure.database.unified_repository import UnifiedDatabaseRepository


class VectorStorage(BaseTool):
    """Real vector storage tool with OpenAI embeddings and pgvector."""
    
    def __init__(self, repository: Optional[UnifiedDatabaseRepository] = None):
        super().__init__(
            name="vector_storage", 
            description="Generate embeddings and store/search vectors using OpenAI and pgvector"
        )
        self.repository = repository or UnifiedDatabaseRepository()
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.logger.warning("OPENAI_API_KEY not set - embedding operations will fail")
            self.openai_client = None
        else:
            self.openai_client = OpenAI(api_key=api_key)
        
        # Embedding configuration
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.embedding_dimension = int(os.getenv("VECTOR_DIMENSION", "1536"))
        self.max_chunk_size = 8000  # Max tokens for embeddings
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute vector operations."""
        try:
            operation = kwargs.get("operation", "count")
            
            if operation == "count":
                return await self._get_count()
            elif operation == "generate_embedding":
                return await self._generate_embedding(**kwargs)
            elif operation == "store_vector":
                return await self._store_vector(**kwargs)
            elif operation == "store_vectors_batch":
                return await self._store_vectors_batch(**kwargs)
            elif operation == "search_similar":
                return await self._search_similar(**kwargs)
            elif operation == "search_by_text":
                return await self._search_by_text(**kwargs)
            elif operation == "get_vector_by_id":
                return await self._get_vector_by_id(**kwargs)
            elif operation == "process_news_for_vectors":
                return await self._process_news_for_vectors(**kwargs)
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=f"Unknown vector operation: {operation}"
                )
                
        except Exception as e:
            self.logger.error(f"Vector operation failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Vector operation failed: {str(e)}"
            )
    
    async def _get_count(self) -> ToolResult:
        """Get total vector count."""
        try:
            count = await self.repository.get_vector_count()
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "total_vectors": count,
                    "storage_type": "postgresql+pgvector",
                    "embedding_model": self.embedding_model,
                    "dimension": self.embedding_dimension
                }
            )
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to get vector count: {str(e)}"
            )
    
    async def _generate_embedding(self, **kwargs) -> ToolResult:
        """Generate embedding for text."""
        try:
            if not self.openai_client:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="OpenAI API key not configured"
                )
            
            text = kwargs.get("text", "")
            if not text or not text.strip():
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="Text parameter is required and cannot be empty"
                )
            
            # Truncate text if too long
            if len(text) > self.max_chunk_size:
                text = text[:self.max_chunk_size]
                self.logger.warning(f"Text truncated to {self.max_chunk_size} characters")
            
            # Generate embedding
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=text,
                    encoding_format="float"
                )
            )
            
            embedding = response.data[0].embedding
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "embedding": embedding,
                    "dimension": len(embedding),
                    "model": self.embedding_model,
                    "input_length": len(text),
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to generate embedding: {str(e)}"
            )
    
    async def _store_vector(self, **kwargs) -> ToolResult:
        """Store a single vector."""
        try:
            vector_data = kwargs.get("vector_data")
            if not vector_data:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="Missing vector_data parameter"
                )
            
            # Convert dict to VectorDocument if needed
            if isinstance(vector_data, dict):
                # Generate embedding if not provided
                embedding = vector_data.get("embedding")
                if not embedding and vector_data.get("text"):
                    embedding_result = await self._generate_embedding(text=vector_data["text"])
                    if not embedding_result.is_success:
                        return embedding_result
                    embedding = embedding_result.data["embedding"]
                
                vector_doc = VectorDocument(
                    source_type=VectorSourceType(vector_data.get("source_type", "news")),
                    source_id=vector_data.get("source_id", ""),
                    content_hash=vector_data.get("content_hash", ""),
                    embedding=embedding,
                    embedding_model=self.embedding_model,
                    metadata=vector_data.get("metadata", {})
                )
            else:
                vector_doc = vector_data
            
            saved_vector = await self.repository.save_vector(vector_doc)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "vector_id": saved_vector.id,
                    "source_type": saved_vector.source_type.value,
                    "source_id": saved_vector.source_id,
                    "dimension": saved_vector.dimension,
                    "stored": True,
                    "created_at": saved_vector.created_at.isoformat() if saved_vector.created_at else None
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store vector: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to store vector: {str(e)}"
            )
    
    async def _store_vectors_batch(self, **kwargs) -> ToolResult:
        """Store multiple vectors."""
        try:
            vectors_data = kwargs.get("vectors_data", [])
            if not vectors_data:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="Missing vectors_data parameter"
                )
            
            stored_vectors = []
            errors = []
            
            # Process vectors with concurrency control
            semaphore = asyncio.Semaphore(3)  # Limit concurrent operations
            
            async def store_single_vector(vector_data):
                async with semaphore:
                    try:
                        result = await self._store_vector(vector_data=vector_data)
                        if result.is_success:
                            return {"success": True, "data": result.data}
                        else:
                            return {"success": False, "error": result.error_message}
                    except Exception as e:
                        return {"success": False, "error": str(e)}
            
            # Execute all stores
            results = await asyncio.gather(
                *[store_single_vector(vector_data) for vector_data in vectors_data],
                return_exceptions=True
            )
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    errors.append(f"Vector {i}: Unexpected error: {str(result)}")
                elif result["success"]:
                    stored_vectors.append(result["data"])
                else:
                    errors.append(f"Vector {i}: {result['error']}")
            
            return ToolResult(
                status=ToolStatus.SUCCESS if stored_vectors else ToolStatus.ERROR,
                data={
                    "total_processed": len(vectors_data),
                    "successfully_stored": len(stored_vectors),
                    "errors": len(errors),
                    "stored_vectors": stored_vectors,
                    "error_details": errors
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store vectors batch: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to store vectors batch: {str(e)}"
            )
    
    async def _search_similar(self, **kwargs) -> ToolResult:
        """Search for similar vectors."""
        try:
            query_vector = kwargs.get("query_vector")
            if not query_vector:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="Missing query_vector parameter"
                )
            
            top_k = kwargs.get("top_k", 5)
            source_type = kwargs.get("source_type")
            
            search_results = await self.repository.search_vectors(
                query_vector=query_vector,
                top_k=top_k,
                source_type=source_type
            )
            
            # Convert to serializable format
            results_data = []
            for result in search_results:
                results_data.append({
                    "vector_id": result.document.id,
                    "source_type": result.document.source_type.value,
                    "source_id": result.document.source_id,
                    "content_hash": result.document.content_hash,
                    "similarity_score": result.similarity_score,
                    "distance": result.distance,
                    "metadata": result.document.metadata,
                    "created_at": result.document.created_at.isoformat() if result.document.created_at else None
                })
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "results": results_data,
                    "count": len(results_data),
                    "top_k": top_k,
                    "source_type_filter": source_type
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to search vectors: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to search vectors: {str(e)}"
            )
    
    async def _search_by_text(self, **kwargs) -> ToolResult:
        """Search for similar vectors using text query."""
        try:
            query_text = kwargs.get("query_text", "")
            if not query_text.strip():
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="query_text parameter is required and cannot be empty"
                )
            
            # Generate embedding for query text
            embedding_result = await self._generate_embedding(text=query_text)
            if not embedding_result.is_success:
                return embedding_result
            
            query_vector = embedding_result.data["embedding"]
            
            # Perform vector search
            return await self._search_similar(
                query_vector=query_vector,
                top_k=kwargs.get("top_k", 5),
                source_type=kwargs.get("source_type")
            )
            
        except Exception as e:
            self.logger.error(f"Failed to search by text: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to search by text: {str(e)}"
            )
    
    async def _get_vector_by_id(self, **kwargs) -> ToolResult:
        """Get vector by ID (placeholder - would need repository method)."""
        try:
            vector_id = kwargs.get("vector_id")
            if not vector_id:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="Missing vector_id parameter"
                )
            
            # Note: This would require adding a method to the repository
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message="get_vector_by_id not yet implemented in repository"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get vector by ID: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to get vector by ID: {str(e)}"
            )
    
    async def _process_news_for_vectors(self, **kwargs) -> ToolResult:
        """Process news articles to create vector embeddings."""
        try:
            days_back = kwargs.get("days_back", 7)
            limit = kwargs.get("limit", 50)
            
            # Get recent news articles
            news_articles = await self.repository.find_recent_news(days=days_back, limit=limit)
            
            if not news_articles:
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "processed": 0,
                        "message": "No news articles found to process"
                    }
                )
            
            processed_vectors = []
            errors = []
            
            # Process each article
            for article in news_articles:
                try:
                    # Create text for embedding (title + content)
                    text_content = f"{article.title}\n\n{article.content}" if article.content else article.title
                    
                    # Generate embedding
                    embedding_result = await self._generate_embedding(text=text_content)
                    if not embedding_result.is_success:
                        errors.append(f"Article {article.id}: Failed to generate embedding")
                        continue
                    
                    # Create vector document
                    vector_doc = VectorDocument(
                        source_type=VectorSourceType.NEWS,
                        source_id=str(article.id),
                        content_hash=article.content_hash,
                        embedding=embedding_result.data["embedding"],
                        embedding_model=self.embedding_model,
                        metadata={
                            "title": article.title,
                            "source": article.source,
                            "url": article.url,
                            "published_at": article.published_at.isoformat() if article.published_at else None
                        }
                    )
                    
                    # Store vector
                    saved_vector = await self.repository.save_vector(vector_doc)
                    processed_vectors.append({
                        "article_id": article.id,
                        "vector_id": saved_vector.id,
                        "title": article.title
                    })
                    
                except Exception as e:
                    errors.append(f"Article {article.id}: {str(e)}")
                    continue
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "total_articles": len(news_articles),
                    "processed_successfully": len(processed_vectors),
                    "errors": len(errors),
                    "processed_vectors": processed_vectors,
                    "error_details": errors
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process news for vectors: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to process news for vectors: {str(e)}"
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the parameter schema for this tool."""
        return {
            "parameters": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "count", "generate_embedding", "store_vector", "store_vectors_batch",
                        "search_similar", "search_by_text", "get_vector_by_id", "process_news_for_vectors"
                    ],
                    "description": "Vector operation to perform"
                },
                "text": {
                    "type": "string",
                    "description": "Text to generate embedding for"
                },
                "vector_data": {
                    "type": "object",
                    "description": "Vector document data for storage"
                },
                "vectors_data": {
                    "type": "array",
                    "description": "Array of vector documents for batch storage"
                },
                "query_vector": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Query vector for similarity search"
                },
                "query_text": {
                    "type": "string",
                    "description": "Query text for text-based similarity search"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of similar results to return",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 100
                },
                "source_type": {
                    "type": "string",
                    "description": "Filter results by source type"
                },
                "vector_id": {
                    "type": "integer",
                    "description": "Vector ID for lookup operations"
                },
                "days_back": {
                    "type": "integer",
                    "description": "Number of days to look back for processing",
                    "default": 7
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of items to process",
                    "default": 50
                }
            },
            "required": ["operation"]
        }