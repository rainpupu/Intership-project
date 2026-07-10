"""add checkpoint fields to training_tasks

Revision ID: a3f2b1c8d901
Revises: 8145fdcd9bdd
Create Date: 2026-07-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a3f2b1c8d901'
down_revision: Union[str, Sequence[str], None] = '8145fdcd9bdd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('training_tasks', sa.Column('checkpoint_path', sa.String(length=500), nullable=True, comment='checkpoint 文件路径'))
    op.add_column('training_tasks', sa.Column('last_checkpoint_epoch', sa.Integer(), nullable=True, comment='最后 checkpoint epoch'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('training_tasks', 'last_checkpoint_epoch')
    op.drop_column('training_tasks', 'checkpoint_path')
