
import logging
import os
import argparse
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import config
from src.service.mistbuddy_manager import get_mistbuddy_manager
from src.routes.routes import router
from pydantic import ValidationError
from yaml import YAMLError
from fastapi.exceptions import FastAPIError

logger = logging.getLogger(__name__)

class AppCreationError(Exception):
    """Base exception for errors during app creation"""

class ConfigLoadError(AppCreationError):
    """Raised when there's an error loading the configuration"""

class MiddlewareError(AppCreationError):
    """Raised when there's an error adding middleware"""

class RouterInclusionError(AppCreationError):
    """Raised when there's an error including the router"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - Runs before the app can accept requests.
    app.state.mistbuddy_manager = get_mistbuddy_manager()
    yield
    # Shutdown - Runs after the app has stopped accepting requests.
    await app.state.mistbuddy_manager.stop_mistbuddy()

def create_app(config_file: str=None) -> FastAPI:
    '''The create_app function creates/returns a FastAPI application setup with CORS middleware, routes, and settings as state within app.state.'''
    try:
        if config_file is None:
            config_file = os.getenv('CONFIG_FILE', 'config.yaml')
        logger.debug(f"Config file: {config_file}")
        app = FastAPI(lifespan=lifespan)


        try:
            # Load the settings. The settings are for all clients who call into the /start endpoint.
            config.load_settings(config_file)
        except (FileNotFoundError, PermissionError) as e:
            logger.error(f"Failed to access config file {config_file}: {str(e)}", exc_info=True)
            raise ConfigLoadError(f"Config file access error: {str(e)}") from e
        except YAMLError as e:
            logger.error(f"Invalid YAML in config file {config_file}: {str(e)}", exc_info=True)
            raise ConfigLoadError(f"Config file parsing error: {str(e)}") from e
        except ValidationError as e:
            logger.error(f"Config validation failed for {config_file}: {str(e)}", exc_info=True)
            raise ConfigLoadError(f"Config validation error: {str(e)}") from e
        # Set CORS configuration (to default)
        try:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],  # Allows all origins
                allow_credentials=True,
                allow_methods=["*"],  # Allows all methods
                allow_headers=["*"],  # Allows all headers
            )
            logger.debug(f"CORS middleware added {app.user_middleware}")
        except FastAPIError as e:
            logger.error(f"Failed to add CORS middleware: {str(e)}", exc_info=True)
            raise MiddlewareError(f"CORS middleware error: {str(e)}") from e

        # Include router
        try:
            app.include_router(router, prefix="/api/v1")
            logger.debug(f"Router included: {router}")
        except FastAPIError as e:
            logger.error(f"Failed to include router: {str(e)}", exc_info=True)
            raise RouterInclusionError(f"Router inclusion error: {str(e)}") from e

        return app
    except AppCreationError as e:
        logger.error(f"Failed to create application: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during app creation: {str(e)}", exc_info=True)
        raise AppCreationError(f"Unexpected error: {str(e)}") from e

def main():
    parser = argparse.ArgumentParser(description="Run MistBuddy Lite server")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to the configuration file")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8085, help="Port to run the server on")
    args = parser.parse_args()

    try:
        if not os.path.exists(args.config):
            raise FileNotFoundError(f"Config file not found: {args.config}")

        app = create_app(args.config)

        logger.info(f"Starting server on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)

    except FileNotFoundError as e:
        logger.error(str(e))
    except ValueError as e:
        logger.error(f"Invalid argument: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error("An unexpected error occurred", exc_info=True)
    finally:
        logger.info("Server shutting down")

if __name__ == "__main__":
    main()