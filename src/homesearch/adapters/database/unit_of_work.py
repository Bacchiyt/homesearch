"""Explicit SQLAlchemy transaction ownership for application use cases."""

from __future__ import annotations

from sqlalchemy.engine import Connection, Engine, RootTransaction

from homesearch.adapters.database.repositories import (
    SqlAlchemyFoundationRepository,
    SqlAlchemyIngestionRepository,
)
from homesearch.application import FoundationRepository, IngestionRepository


class SqlAlchemyUnitOfWork:
    """One connection and transaction, created and closed per application use case."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._connection: Connection | None = None
        self._transaction: RootTransaction | None = None
        self._foundation: SqlAlchemyFoundationRepository | None = None
        self._ingestion: SqlAlchemyIngestionRepository | None = None

    @property
    def foundation(self) -> FoundationRepository:
        if self._foundation is None:
            raise RuntimeError("Unit of work is not active")
        return self._foundation

    @property
    def ingestion(self) -> IngestionRepository:
        if self._ingestion is None:
            raise RuntimeError("Unit of work is not active")
        return self._ingestion

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        if self._connection is not None:
            raise RuntimeError("Unit of work is already active")
        self._connection = self._engine.connect()
        self._transaction = self._connection.begin()
        self._foundation = SqlAlchemyFoundationRepository(self._connection)
        self._ingestion = SqlAlchemyIngestionRepository(self._connection)
        return self

    def commit(self) -> None:
        transaction = self._active_transaction()
        transaction.commit()
        self._transaction = None
        self._foundation = None
        self._ingestion = None

    def rollback(self) -> None:
        transaction = self._active_transaction()
        transaction.rollback()
        self._transaction = None
        self._foundation = None
        self._ingestion = None

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        try:
            if self._transaction is not None and self._transaction.is_active:
                self._transaction.rollback()
        finally:
            self._transaction = None
            self._foundation = None
            self._ingestion = None
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    def _active_transaction(self) -> RootTransaction:
        if self._transaction is None or not self._transaction.is_active:
            raise RuntimeError("Unit of work has no active transaction")
        return self._transaction
