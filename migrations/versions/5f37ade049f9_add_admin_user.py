"""add admin user

Revision ID: 5f37ade049f9
Revises: fc830860648d
Create Date: 2025-04-03 22:25:47.139531

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.sql import table, column
from passlib.context import CryptContext


revision: str = "5f37ade049f9"
down_revision: Union[str, None] = "fc830860648d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def upgrade() -> None:
    users = table(
        "users",
        column("id", sa.Integer),
        column("username", sa.String),
        column("email", sa.String),
        column("full_name", sa.String),
        column("hashed_password", sa.String),
        column(
            "role",
            sa.Enum("ADMIN", "SERVICE_OWNER", "DEVELOPER", "VIEWER", name="userrole"),
        ),
        column("is_active", sa.Boolean),
    )

    op.bulk_insert(
        users,
        [
            {
                "username": "admin",
                "email": "admin@example.com",
                "full_name": "System Administrator",
                "hashed_password": get_password_hash("admin123"),
                "role": "ADMIN",
                "is_active": True,
            }
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM users WHERE email = 'admin@example.com'")
