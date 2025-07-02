from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import Generator, Optional
import logging

from .models import Base
from config.settings import get_settings


class DatabaseManager:
    def __init__(self, database_url: Optional[str] = None):
        self.settings = get_settings()
        self.database_url = database_url or self.settings.database_url
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.logger = logging.getLogger(__name__)
        
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            self.logger.info("Database tables dropped successfully")
        except SQLAlchemyError as e:
            self.logger.error(f"Error dropping database tables: {e}")
            raise
    
    @contextmanager
    def get_db_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session(self) -> Session:
        """Get a new database session (manual management)"""
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            self.logger.info("Database connection test successful")
            return True
        except SQLAlchemyError as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_table_info(self) -> dict:
        """Get information about database tables"""
        try:
            metadata = MetaData()
            metadata.reflect(bind=self.engine)
            
            table_info = {}
            for table_name, table in metadata.tables.items():
                table_info[table_name] = {
                    "columns": [col.name for col in table.columns],
                    "primary_keys": [col.name for col in table.primary_key],
                    "foreign_keys": [
                        {
                            "column": fk.parent.name,
                            "references": f"{fk.column.table.name}.{fk.column.name}"
                        }
                        for fk in table.foreign_keys
                    ]
                }
            
            return table_info
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting table info: {e}")
            return {}
    
    def execute_raw_query(self, query: str, params: dict = None):
        """Execute raw SQL query"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(query, params or {})
                return result.fetchall()
        except SQLAlchemyError as e:
            self.logger.error(f"Error executing raw query: {e}")
            raise
    
    def backup_database(self, backup_path: str):
        """Create database backup (SQLite specific)"""
        if "sqlite" in self.database_url.lower():
            import shutil
            import os
            
            try:
                # Extract database file path from URL
                db_file = self.database_url.replace("sqlite:///", "")
                if os.path.exists(db_file):
                    shutil.copy2(db_file, backup_path)
                    self.logger.info(f"Database backed up to {backup_path}")
                else:
                    self.logger.warning(f"Database file not found: {db_file}")
            except Exception as e:
                self.logger.error(f"Error backing up database: {e}")
                raise
        else:
            self.logger.warning("Backup only supported for SQLite databases")
    
    def get_database_stats(self) -> dict:
        """Get database statistics"""
        try:
            stats = {}
            metadata = MetaData()
            metadata.reflect(bind=self.engine)
            
            with self.engine.connect() as connection:
                for table_name in metadata.tables.keys():
                    try:
                        result = connection.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = result.scalar()
                        stats[table_name] = count
                    except SQLAlchemyError:
                        stats[table_name] = "Error getting count"
            
            return stats
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}


# Global database manager instance
_db_manager = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def init_database():
    """Initialize the database (create tables)"""
    db_manager = get_database_manager()
    db_manager.create_tables()


def get_db_session():
    """Get database session (for dependency injection)"""
    db_manager = get_database_manager()
    return db_manager.get_db_session()