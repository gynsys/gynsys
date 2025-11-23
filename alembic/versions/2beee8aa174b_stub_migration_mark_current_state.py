"""Stub migration - mark current state

Esta migración marca el estado actual de la base de datos sin hacer cambios.
La mayoría de los cambios detectados por Alembic son cosméticos (TEXT vs String)
y no son necesarios en SQLite donde ambos son equivalentes.

Revision ID: 2beee8aa174b
Revises: 
Create Date: 2025-11-22 17:39:19.521632

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2beee8aa174b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
