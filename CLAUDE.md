# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

AI Invest Trend is an intelligent investment research platform that has been refactored from a monolithic architecture to a modern layered architecture using Domain-Driven Design (DDD) principles. The system provides AI-powered news analysis, vector similarity search, and investment report generation.

## Architecture

### Phase 1 (Current): PostgreSQL + pgvector
The codebase uses a layered DDD architecture with:
- **Domain Layer**: Core business entities and repository interfaces (`domain/`)
- **Application Layer**: Use cases and business workflows (`application/`)
- **Infrastructure Layer**: Database models, repositories, and external services (`infrastructure/`)
- **Presentation Layer**: FastAPI endpoints (`main_new.py`)

### Phase 2 (Planned): Hybrid PostgreSQL + Qdrant
The architecture is designed to support migration to a hybrid vector storage system using the factory pattern and abstract interfaces.

FOCUS PHASE 1， ONLY push infor of phase 1 in the related doc and code. PHASE 2 infor only in docs/roadmap.md

### Key Architectural Components

**Vector Storage Factory**: `src/infrastructure/config/vector_storage_factory.py`
- Provides pluggable architecture for switching vector storage backends
- Currently supports PostgreSQL + pgvector with preparation for Qdrant
- Uses environment variables for configuration switching

**Abstract Repository Pattern**: `src/domain/repositories/vector_repository.py`
- Defines unified interface for vector operations
- Enables seamless backend switching without application logic changes
- Supports similarity search, CRUD operations, and bulk operations

**Domain Entities**: 
- `NewsArticle` with processing status tracking (`src/domain/entities/`)
- `VectorDocument` with data tier management for Phase 2
- Rich domain objects with business logic encapsulation

## Development Setup

### Environment Variables
Copy `env.template` to `.env` and configure:
```bash
cp env.template .env
```

Essential variables:
- `DATABASE_URL`: PostgreSQL connection (for local: `postgresql+asyncpg://ai_invest:ai_invest_password@localhost:5432/ai_invest`)
- `VECTOR_STORAGE_PROVIDER`: Set to `postgresql` for Phase 1
- `VECTOR_DIMENSION`: Set to `1536` for OpenAI embeddings
- `OPENAI_API_KEY`: Required for AI analysis features

### Database Setup
PostgreSQL with pgvector extension:
```bash
# Start PostgreSQL with Docker Compose
cd docker && docker-compose up -d postgres

# Or start full environment
cd docker && docker-compose up --build
```

## Common Commands

### Development
```bash
# Run the application (main entry point)
uvicorn main:app --reload

# Or run directly with Python
python main.py

# Test the new architecture
python scripts/database/test_architecture.py
```

### Testing
```bash
# Run basic tests
python tests/test_run_report.py
python tests/test_run_report_simple.py

# Test new architecture components
python -m pytest tests/ -v
```

### Database Operations
```bash
# Database migrations (if using Alembic)
alembic upgrade head

# Reset database
cd docker && docker-compose down -v postgres
cd docker && docker-compose up -d postgres
```

## API Endpoints

### Current Architecture (main.py → src/presentation/api/main.py)
- `GET /`: Application status and info
- `GET /health`: Comprehensive health check for database and vector storage
- `GET /info/vector-storage`: Vector storage configuration and statistics
- `GET /test/vector-storage`: Complete vector storage functionality test
- `GET /test/vector-search`: Simple vector similarity search test
- `GET /run/weekly-full-report`: Legacy endpoint (will be migrated to use cases)

## Key Design Patterns

### Factory Pattern
`VectorStorageFactory` manages creation of vector storage instances and supports multiple backends through environment configuration.

### Repository Pattern
Abstract `VectorRepository` interface allows switching between PostgreSQL and future Qdrant implementations without changing business logic.

### Domain-Driven Design
- Entities contain business logic and validation
- Value objects ensure data consistency
- Repositories abstract data persistence
- Use cases orchestrate business workflows

## File Structure Understanding

### Source Code (`src/`)

#### Domain Layer (`src/domain/`)
- `entities/`: Core business objects (NewsArticle, VectorDocument, AnalysisResult)
- `repositories/`: Abstract interfaces for data access
- `value_objects/`: Immutable objects representing business concepts

#### Application Layer (`src/application/`)
- `use_cases/`: Business workflows and orchestration
- `services/`: Application services
- `dtos/`: Data transfer objects

#### Infrastructure Layer (`src/infrastructure/`)
- `database/`: SQLAlchemy models and PostgreSQL repositories
- `config/`: Factory classes and configuration management
- `external/`: External services integration
  - `data_sources/`: News and data fetching (formerly `fetchers/`)
  - `notifications/`: Slack and report utilities (formerly `utils/`)
  - `openai/`: AI analysis services (formerly `analyzers/`)

#### Presentation Layer (`src/presentation/`)
- `api/`: FastAPI routes and main application
- `schemas/`: Request/response models
- `middleware/`: Application middleware

### Supporting Directories
- `docker/`: Docker and Docker Compose configuration
- `deployment/`: Azure and production deployment files
- `scripts/`: Database and deployment scripts
- `resources/`: Prompts and templates
- `tests/`: Test files

## Vector Storage Operations

The system uses PostgreSQL with pgvector extension for vector similarity search:
- Embeddings stored with HNSW indexing for performance
- Support for cosine similarity search
- Batch operations for bulk vector insertions
- Prepared for Phase 2 migration to hybrid storage

## Configuration Management

Environment-based configuration with template:
- Development: Uses Docker Compose PostgreSQL
- Production: Designed for Azure Container Apps
- Flexible vector storage provider switching
- Comprehensive logging and monitoring setup

## Migration Notes

When working with this codebase:
1. All code is now organized under the `src/` directory following DDD patterns
2. Use abstract repository interfaces for data access (`src/domain/repositories/`)
3. Follow DDD patterns for new business logic
4. Test vector storage functionality with provided test endpoints
5. Environment variables control backend selection and configuration
6. Import paths now start with `src.` (e.g., `from src.domain.entities import ...`)

## Development Guidelines

1. **New Features**: Add new business logic in the domain layer, orchestrate in use cases
2. **External Integrations**: Place in `src/infrastructure/external/` with proper abstraction
3. **API Changes**: Modify routes in `src/presentation/api/` and add schemas in `schemas/`
4. **Testing**: Use the architecture test script in `scripts/database/test_architecture.py`
5. **Dependencies**: All external services should be accessed through repository interfaces
6. 相关的架构变更和数据模型变更,需要同步更新到architect.md和architecture-cn.md文档中

## Dependencies

Key libraries:
- **FastAPI**: Web framework
- **SQLAlchemy**: ORM with async support
- **pgvector**: PostgreSQL vector extension
- **OpenAI**: AI model integration
- **LangChain**: LLM workflow management
- **Docker Compose**: Development environment
