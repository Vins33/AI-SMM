# src/api/admin.py
"""Admin API endpoints for CRUD operations and database management."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_sysadmin_user, get_db
from src.services.auth_models import User, UserRole
from src.services.auth_service import (
    create_user,
    delete_user,
    get_all_users,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    update_user,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


# --- Pydantic Schemas ---


class UserCreateAdmin(BaseModel):
    """Schema for admin user creation."""

    username: str
    email: EmailStr
    password: str
    role: str = "user"


class UserUpdateAdmin(BaseModel):
    """Schema for admin user update."""

    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserResponseAdmin(BaseModel):
    """Schema for admin user response."""

    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str
    last_login: str | None = None

    class Config:
        from_attributes = True


class TableInfo(BaseModel):
    """Schema for table information."""

    name: str
    columns: list[dict[str, Any]]
    row_count: int


class QueryRequest(BaseModel):
    """Schema for SQL query request."""

    query: str


class QueryResponse(BaseModel):
    """Schema for SQL query response."""

    success: bool
    data: list[dict[str, Any]] | None = None
    affected_rows: int | None = None
    error: str | None = None


class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""

    total_users: int
    active_users: int
    total_conversations: int
    total_messages: int
    users_by_role: dict[str, int]


# --- User CRUD Endpoints ---


@router.get("/users", response_model=list[UserResponseAdmin])
async def list_users(
    _: Annotated[User, Depends(get_current_sysadmin_user)],
    session: AsyncSession = Depends(get_db),
):
    """Get all users (sysadmin only)."""
    users = await get_all_users(session)
    return [
        UserResponseAdmin(
            id=u.id,
            username=u.username,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at.isoformat() if u.created_at else "",
            updated_at=u.updated_at.isoformat() if u.updated_at else "",
            last_login=u.last_login.isoformat() if u.last_login else None,
        )
        for u in users
    ]


@router.get("/users/{user_id}", response_model=UserResponseAdmin)
async def get_user(
    user_id: int,
    _: Annotated[User, Depends(get_current_sysadmin_user)],
    session: AsyncSession = Depends(get_db),
):
    """Get a specific user by ID (sysadmin only)."""
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponseAdmin(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else "",
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@router.post("/users", response_model=UserResponseAdmin, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    user_data: UserCreateAdmin,
    _: Annotated[User, Depends(get_current_sysadmin_user)],
    session: AsyncSession = Depends(get_db),
):
    """Create a new user (sysadmin only)."""
    # Check if username exists
    existing_user = await get_user_by_username(session, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    existing_email = await get_user_by_email(session, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Validate role
    try:
        role = UserRole(user_data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}",
        )

    user = await create_user(
        session,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        role=role,
    )

    return UserResponseAdmin(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else "",
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@router.put("/users/{user_id}", response_model=UserResponseAdmin)
async def update_user_admin(
    user_id: int,
    user_data: UserUpdateAdmin,
    current_user: Annotated[User, Depends(get_current_sysadmin_user)],
    session: AsyncSession = Depends(get_db),
):
    """Update a user (sysadmin only)."""
    # Prevent self-demotion
    if user_id == current_user.id and user_data.role and user_data.role != UserRole.SYSADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself",
        )

    # Validate role if provided
    role = None
    if user_data.role:
        try:
            role = UserRole(user_data.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}",
            )

    user = await update_user(
        session,
        user_id=user_id,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        role=role,
        is_active=user_data.is_active,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponseAdmin(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else "",
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_admin(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_sysadmin_user)],
    session: AsyncSession = Depends(get_db),
):
    """Delete a user (sysadmin only)."""
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    deleted = await delete_user(session, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


# --- Database Introspection Endpoints ---


@router.get("/database/tables", response_model=list[TableInfo])
async def list_tables(
    _: Annotated[User, Depends(get_current_sysadmin_user)],
    session: AsyncSession = Depends(get_db),
):
    """Get list of all database tables with their columns (sysadmin only)."""
    tables = []

    # Get table names using raw SQL for PostgreSQL
    result = await session.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
        )
    )
    table_names = [row[0] for row in result.fetchall()]

    for table_name in table_names:
        # Get columns
        col_result = await session.execute(
            text(
                "SELECT column_name, data_type, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_name = :table_name"
            ),
            {"table_name": table_name},
        )
        columns = [
            {"name": row[0], "type": row[1], "nullable": row[2] == "YES"}
            for row in col_result.fetchall()
        ]

        # Get row count
        count_result = await session.execute(
            text(f'SELECT COUNT(*) FROM "{table_name}"')
        )
        row_count = count_result.scalar() or 0

        tables.append(
            TableInfo(name=table_name, columns=columns, row_count=row_count)
        )

    return tables


@router.get("/database/tables/{table_name}")
async def get_table_data(
    table_name: str,
    _: Annotated[User, Depends(get_current_sysadmin_user)],
    session: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """Get data from a specific table (sysadmin only)."""
    # Validate table exists
    result = await session.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = :table_name"
        ),
        {"table_name": table_name},
    )
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found",
        )

    # Get data with pagination
    data_result = await session.execute(
        text(f'SELECT * FROM "{table_name}" LIMIT :limit OFFSET :offset'),
        {"limit": limit, "offset": offset},
    )

    rows = data_result.fetchall()
    columns = data_result.keys()

    return {
        "table": table_name,
        "columns": list(columns),
        "data": [dict(zip(columns, row)) for row in rows],
        "limit": limit,
        "offset": offset,
    }


@router.post("/database/query", response_model=QueryResponse)
async def execute_query(
    query_request: QueryRequest,
    _: Annotated[User, Depends(get_current_sysadmin_user)],
    session: AsyncSession = Depends(get_db),
):
    """Execute a raw SQL query (sysadmin only). Use with caution!"""
    query = query_request.query.strip()

    # Security: Block dangerous operations
    dangerous_keywords = ["DROP DATABASE", "DROP SCHEMA", "TRUNCATE"]
    for keyword in dangerous_keywords:
        if keyword.upper() in query.upper():
            return QueryResponse(
                success=False,
                error=f"Query contains forbidden keyword: {keyword}",
            )

    try:
        result = await session.execute(text(query))

        # Check if it's a SELECT query
        if query.upper().startswith("SELECT"):
            rows = result.fetchall()
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]
            return QueryResponse(success=True, data=data)
        else:
            # For INSERT, UPDATE, DELETE
            await session.commit()
            return QueryResponse(success=True, affected_rows=result.rowcount)

    except Exception as e:
        await session.rollback()
        return QueryResponse(success=False, error=str(e))


# --- Dashboard Statistics ---


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    _: Annotated[User, Depends(get_current_sysadmin_user)],
    session: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics (sysadmin only)."""
    # Total users
    total_users_result = await session.execute(text("SELECT COUNT(*) FROM users"))
    total_users = total_users_result.scalar() or 0

    # Active users
    active_users_result = await session.execute(
        text("SELECT COUNT(*) FROM users WHERE is_active = true")
    )
    active_users = active_users_result.scalar() or 0

    # Users by role
    roles_result = await session.execute(
        text("SELECT role, COUNT(*) FROM users GROUP BY role")
    )
    users_by_role = {row[0]: row[1] for row in roles_result.fetchall()}

    # Total conversations (if table exists)
    try:
        conv_result = await session.execute(text("SELECT COUNT(*) FROM conversations"))
        total_conversations = conv_result.scalar() or 0
    except Exception:
        total_conversations = 0

    # Total messages (if table exists)
    try:
        msg_result = await session.execute(text("SELECT COUNT(*) FROM messages"))
        total_messages = msg_result.scalar() or 0
    except Exception:
        total_messages = 0

    return DashboardStats(
        total_users=total_users,
        active_users=active_users,
        total_conversations=total_conversations,
        total_messages=total_messages,
        users_by_role=users_by_role,
    )
