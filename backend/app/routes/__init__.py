from app.routes.auth import router as auth_router
from app.routes.students import router as students_router
from app.routes.teachers import router as teachers_router
from app.routes.parents import router as parents_router
from app.routes.ai_sessions import router as ai_router

__all__ = [
    "auth_router",
    "students_router", 
    "teachers_router",
    "parents_router",
    "ai_router"
]
