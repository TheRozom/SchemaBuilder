from abc import ABC, abstractmethod

from src.bl.builder import SchemaBuilderService
from src.bl.generator import MockDataGenerator
from src.domain.interfaces import ISchemaService


class ServiceFactory(ABC):
    @abstractmethod
    def create_schema_service(self) -> ISchemaService:
        pass

    @abstractmethod
    def create_mock_generator(self) -> MockDataGenerator:
        pass


class ProductionServiceFactory(ServiceFactory):
    def create_schema_service(self) -> ISchemaService:
        return SchemaBuilderService()

    def create_mock_generator(self) -> MockDataGenerator:
        return MockDataGenerator()


class MockServiceFactory(ServiceFactory):
    def __init__(
        self,
        schema_service: ISchemaService = None,
        mock_generator: MockDataGenerator = None,
    ):
        self._schema_service = schema_service
        self._mock_generator = mock_generator

    def create_schema_service(self) -> ISchemaService:
        if self._schema_service is None:
            return SchemaBuilderService()
        return self._schema_service

    def create_mock_generator(self) -> MockDataGenerator:
        if self._mock_generator is None:
            return MockDataGenerator()
        return self._mock_generator


_factory: ServiceFactory = ProductionServiceFactory()


def get_factory() -> ServiceFactory:
    return _factory


def set_factory(factory: ServiceFactory) -> None:
    global _factory
    _factory = factory


def reset_factory() -> None:
    global _factory
    _factory = ProductionServiceFactory()
