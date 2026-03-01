"""add open_days to locations

Revision ID: b7a5c08978be
Revises: 6d7546e47693
Create Date: 2026-01-19 19:22:53.955691

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7a5c08978be'
down_revision: Union[str, Sequence[str], None] = '6d7546e47693'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
