import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes import mistbuddy_start_endpoint, mistbuddy_stop_endpoint


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("MistBuddy Lite application start")

    yield  # Run the application

    # Cleanup
    logger.info("MistBuddy Lite application shutdown")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(mistbuddy_start_endpoint.router, prefix="/api/v1", tags=["mistbuddy_start"])
app.include_router(mistbuddy_stop_endpoint.router, prefix="/api/v1", tags=["mistbuddy_stop"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mistbuddy_lite:app", host="0.0.0.0", port=8085, reload=True)