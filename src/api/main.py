from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import generator_router, schemas_router
from src.core import get_logger
from src.core.config import settings
from src.shared import SchemaBuilderError, ValidationException

logger = get_logger(__name__)

app = FastAPI(
    title="Schema Builder API",
    description="Secure JSON Schema generator",
    version="0.1.0",
)

# Security check for CORS configuration
if settings.CORS_ORIGINS == ["*"]:
    logger.warning(
        "SECURITY WARNING: CORS is configured to allow all origins. "
        "This is insecure for production. Set CORS_ORIGINS explicitly in your environment."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


@app.exception_handler(SchemaBuilderError)
async def schema_builder_error_handler(_request: Request, exc: SchemaBuilderError) -> JSONResponse:
    logger.error("SchemaBuilderError: %s", exc.message)

    return JSONResponse(
        status_code=400,
        content=exc.to_dict(),
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(_request: Request, exc: ValidationException) -> JSONResponse:
    logger.error("ValidationException: %s", exc.message)

    return JSONResponse(
        status_code=422,
        content=exc.to_dict(),
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


app.include_router(schemas_router)

app.include_router(generator_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
