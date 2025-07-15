import logging
import time
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from database.session import create_db_and_tables
from auth.router import router as auth_router
from projects.router import router as projects_router
# from projects.items_router import router as project_items_router  # Disabled for now
from projects.tables_router import router as tables_router
from projects.table_rows_router import router as table_rows_router
from projects.members_router import router as members_router
from projects.files_router import router as files_router
from projects.websocket_router import router as websocket_router
from projects.graphql_router import router as graphql_router
from items.router import router as items_router
from monitoring.router import router as monitoring_router
from admin.users_router import router as admin_users_router

app = FastAPI(
    title="Sovera Backend API",
    description="Backend API pour Sovera - Une seedbox souveraine",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permettre toutes les origines en développement
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logging.info(f"Request: {request.method} {request.url} - Processed in {process_time:.4f}s - Status: {response.status_code}")
        return response

app.add_middleware(LoggingMiddleware)

@app.on_event("startup")
async def on_startup():
    create_db_and_tables()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(projects_router, prefix="/projects", tags=["projects"])
# app.include_router(project_items_router, prefix="", tags=["project-items"])  # Multi-tenant items
app.include_router(tables_router, prefix="", tags=["tables"])
app.include_router(table_rows_router, prefix="", tags=["table-rows"])
app.include_router(members_router, prefix="", tags=["members"])
app.include_router(files_router, prefix="", tags=["files"])
app.include_router(websocket_router, prefix="", tags=["websocket"])
app.include_router(graphql_router, prefix="", tags=["graphql"])
app.include_router(items_router, prefix="/items", tags=["items"])
app.include_router(monitoring_router, prefix="/system", tags=["system"])
app.include_router(admin_users_router, prefix="/admin", tags=["admin"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Sovera"}
