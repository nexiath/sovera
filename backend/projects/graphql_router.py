"""
GraphQL router for dynamic project APIs in Sovera.
Provides automatically generated GraphQL APIs for project tables.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.types import ExecutionResult

from auth.dependencies import get_current_user
from database.session import get_session
from models.user import User
from models.project import Project
from services.graphql_schema import (
    get_project_schema, 
    clear_project_schema_cache, 
    get_schema_stats,
    GraphQLSchemaError
)
from utils.rbac import require_project_viewer

logger = logging.getLogger(__name__)
router = APIRouter()

# Custom context class for GraphQL
class GraphQLContext:
    def __init__(self, user: User, session: Session, project: Project):
        self.user = user
        self.session = session
        self.project = project

async def get_graphql_context(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_viewer)
) -> GraphQLContext:
    """Create GraphQL context with user and project info"""
    return GraphQLContext(current_user, session, project)

@router.post("/projects/{project_id}/graphql")
@router.get("/projects/{project_id}/graphql")
async def graphql_endpoint(
    request: Request,
    project_id: int = Path(..., description="Project ID", gt=0),
    context: GraphQLContext = Depends(get_graphql_context)
):
    """
    GraphQL endpoint for project-specific API.
    
    **Features:**
    - Automatically generated schema based on project tables
    - Full CRUD operations for all tables
    - Role-based access control
    - Real-time updates integration
    - Type-safe queries and mutations
    
    **Authentication:**
    - Requires valid JWT token
    - Permissions checked per operation
    
    **Generated Operations:**
    
    **Queries:**
    - `list_{table_name}(limit: Int, offset: Int)` - List records with pagination
    - `get_{table_name}(id: Int!)` - Get single record by ID
    
    **Mutations:**
    - `create_{table_name}(input: {Table}CreateInput!)` - Create new record
    - `update_{table_name}(id: Int!, input: {Table}UpdateInput!)` - Update record
    - `delete_{table_name}(id: Int!)` - Delete record
    
    **Example Query:**
    ```graphql
    query {
      list_customers(limit: 10) {
        id
        name
        email
        created_at
      }
    }
    ```
    
    **Example Mutation:**
    ```graphql
    mutation {
      create_customer(input: {
        name: "John Doe"
        email: "john@example.com"
        age: 30
      }) {
        id
        name
        email
      }
    }
    ```
    """
    try:
        # Get project schema
        schema = await get_project_schema(context.project)
        
        # Create GraphQL router with dynamic schema
        graphql_app = GraphQLRouter(
            schema,
            context_getter=lambda: {
                'user': context.user,
                'session': context.session,
                'project': context.project
            }
        )
        
        # Handle the request
        if request.method == "GET":
            # Return GraphiQL interface for GET requests
            return HTMLResponse(content=get_graphiql_html(project_id))
        else:
            # Handle GraphQL POST requests
            return await graphql_app.handle_request(request)
            
    except GraphQLSchemaError as e:
        logger.warning(f"GraphQL schema error for project {project_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"GraphQL endpoint error for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/projects/{project_id}/graphql/schema")
async def get_schema_sdl(
    project_id: int = Path(..., description="Project ID", gt=0),
    context: GraphQLContext = Depends(get_graphql_context)
):
    """
    Get the GraphQL Schema Definition Language (SDL) for the project.
    
    Returns the complete schema in SDL format, useful for:
    - Client code generation
    - API documentation
    - Schema introspection
    """
    try:
        schema = await get_project_schema(context.project)
        sdl = strawberry.export_schema.export_schema_as_string(schema)
        
        return {
            "project_id": project_id,
            "project_name": context.project.name,
            "schema_sdl": sdl,
            "endpoint_url": f"/projects/{project_id}/graphql"
        }
        
    except GraphQLSchemaError as e:
        logger.warning(f"Schema SDL generation failed for project {project_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Schema SDL error for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/projects/{project_id}/graphql/refresh")
async def refresh_schema(
    project_id: int = Path(..., description="Project ID", gt=0),
    context: GraphQLContext = Depends(get_graphql_context)
):
    """
    Refresh the GraphQL schema for the project.
    
    Use this endpoint when:
    - New tables are created
    - Table structure changes
    - Schema needs to be regenerated
    
    **Permissions Required:** Editor or Owner
    """
    try:
        # Check if user has permission to refresh schema
        from utils.rbac import PermissionManager
        user_role = PermissionManager.get_user_role(context.user.id, project_id, context.session)
        if not user_role or not PermissionManager.has_permission(user_role, "tables:create"):
            raise HTTPException(status_code=403, detail="Access denied: Missing tables:create permission")
        
        # Clear cache and regenerate schema
        clear_project_schema_cache(project_id)
        schema = await get_project_schema(context.project, force_refresh=True)
        
        logger.info(f"Refreshed GraphQL schema for project {project_id}")
        
        return {
            "message": "GraphQL schema refreshed successfully",
            "project_id": project_id,
            "project_name": context.project.name,
            "endpoint_url": f"/projects/{project_id}/graphql"
        }
        
    except HTTPException:
        raise
    except GraphQLSchemaError as e:
        logger.warning(f"Schema refresh failed for project {project_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Schema refresh error for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/projects/{project_id}/graphql/playground")
async def graphql_playground(
    project_id: int = Path(..., description="Project ID", gt=0),
    context: GraphQLContext = Depends(get_graphql_context)
):
    """
    GraphQL Playground interface for interactive schema exploration.
    
    Provides a rich IDE for:
    - Writing and testing queries
    - Exploring schema documentation
    - Query autocompletion
    - Real-time results
    """
    return HTMLResponse(content=get_playground_html(project_id))

@router.get("/graphql/stats")
async def get_graphql_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get GraphQL service statistics.
    
    Returns information about:
    - Cached schemas
    - Active projects
    - Performance metrics
    """
    stats = get_schema_stats()
    
    return {
        "stats": stats,
        "timestamp": "now"
    }

def get_graphiql_html(project_id: int) -> str:
    """Generate GraphiQL HTML interface"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>GraphiQL - Project {project_id}</title>
        <link href="https://unpkg.com/graphiql/graphiql.min.css" rel="stylesheet" />
        <style>
            body {{ height: 100vh; margin: 0; }}
            #graphiql {{ height: 100vh; }}
        </style>
    </head>
    <body>
        <div id="graphiql">Loading...</div>
        <script
            crossorigin
            src="https://unpkg.com/react@17/umd/react.production.min.js"
        ></script>
        <script
            crossorigin
            src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"
        ></script>
        <script
            crossorigin
            src="https://unpkg.com/graphiql/graphiql.min.js"
        ></script>
        <script>
            const fetcher = GraphiQL.createFetcher({{
                url: '/projects/{project_id}/graphql',
                headers: {{
                    'Authorization': 'Bearer ' + getCookie('auth_token')
                }}
            }});
            
            function getCookie(name) {{
                const value = `; ${{document.cookie}}`;
                const parts = value.split(`; ${{name}}=`);
                if (parts.length === 2) return parts.pop().split(';').shift();
            }}
            
            ReactDOM.render(
                React.createElement(GraphiQL, {{ 
                    fetcher: fetcher,
                    defaultQuery: `# Welcome to GraphiQL for Project {project_id}
# 
# GraphiQL is an in-browser tool for writing, validating, and
# testing GraphQL queries.
#
# Type queries into this side of the screen, and you will see intelligent
# typeaheads aware of the current GraphQL type schema and live syntax and
# validation errors highlighted within the text.
#
# Example query:

query ExampleQuery {{
  # List tables available in your project
  # Replace with actual table names from your project
}}

mutation ExampleMutation {{
  # Create, update, or delete records
  # Replace with actual table operations
}}`
                }}),
                document.getElementById('graphiql'),
            );
        </script>
    </body>
    </html>
    """

def get_playground_html(project_id: int) -> str:
    """Generate GraphQL Playground HTML interface"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset=utf-8/>
        <meta name="viewport" content="user-scalable=no, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, minimal-ui">
        <title>GraphQL Playground - Project {project_id}</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/css/index.css" />
        <link rel="shortcut icon" href="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/favicon.png" />
        <script src="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/js/middleware.js"></script>
    </head>
    <body>
        <div id="root">
            <style>
                body {{
                    background-color: rgb(23, 42, 58);
                    font-family: Open Sans, sans-serif;
                    height: 90vh;
                }}
                #root {{
                    height: 100%;
                    width: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .loading {{
                    font-size: 32px;
                    font-weight: 200;
                    color: rgba(255, 255, 255, .6);
                    margin-left: 20px;
                }}
                img {{
                    width: 78px;
                    height: 78px;
                }}
                .title {{
                    font-weight: 400;
                }}
            </style>
            <img src="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/logo.png" alt="">
            <div class="loading"> Loading
                <span class="title">GraphQL Playground</span>
            </div>
        </div>
        <script>
            window.addEventListener('load', function (event) {{
                function getCookie(name) {{
                    const value = `; ${{document.cookie}}`;
                    const parts = value.split(`; ${{name}}=`);
                    if (parts.length === 2) return parts.pop().split(';').shift();
                }}
                
                GraphQLPlayground.init(document.getElementById('root'), {{
                    endpoint: '/projects/{project_id}/graphql',
                    headers: {{
                        'Authorization': 'Bearer ' + getCookie('auth_token')
                    }},
                    settings: {{
                        'editor.theme': 'dark',
                        'editor.cursorShape': 'line',
                        'editor.fontSize': 14,
                        'editor.fontFamily': '"Source Code Pro", "Consolas", "Inconsolata", "Droid Sans Mono", "Monaco", monospace',
                        'editor.reuseHeaders': true,
                        'tracing.hideTracingResponse': true,
                        'editor.cursorShape': 'line',
                        'request.credentials': 'include',
                    }},
                    tabs: [
                        {{
                            endpoint: '/projects/{project_id}/graphql',
                            query: `# Welcome to GraphQL Playground
# GraphQL Playground is a graphical, interactive, in-browser GraphQL IDE.
#
# This is your project's dynamic GraphQL API endpoint.
# The schema is automatically generated from your project tables.
#
# Example queries:

query ListData {{
  # Replace 'tableName' with your actual table names
  # list_tableName(limit: 10) {{
  #   id
  #   # other fields...
  # }}
}}

mutation CreateData {{
  # create_tableName(input: {{
  #   field1: "value1"
  #   field2: "value2"
  # }}) {{
  #   id
  #   # other fields...
  # }}
}}`
                        }}
                    ]
                }})
            }})
        </script>
    </body>
    </html>
    """