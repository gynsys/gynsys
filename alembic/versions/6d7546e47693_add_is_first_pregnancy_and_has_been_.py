"""add_is_first_pregnancy_and_has_been_pregnant_to_appointments

Revision ID: 6d7546e47693
Revises: 2beee8aa174b
Create Date: 2025-11-24 01:12:45.252249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d7546e47693'
down_revision: Union[str, Sequence[str], None] = '2beee8aa174b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Agregar columnas para determinar el flujo obstétrico (HO)
    op.add_column('appointments', sa.Column('is_first_pregnancy', sa.Boolean(), nullable=True))
    op.add_column('appointments', sa.Column('has_been_pregnant', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Eliminar las columnas agregadas
    op.drop_column('appointments', 'has_been_pregnant')
    op.drop_column('appointments', 'is_first_pregnancy')
