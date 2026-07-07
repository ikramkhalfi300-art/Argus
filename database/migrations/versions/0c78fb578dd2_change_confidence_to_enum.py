"""change_confidence_to_enum

Revision ID: 0c78fb578dd2
Revises: 373592706c86
Create Date: 2026-07-05 23:40:36.362983

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c78fb578dd2'
down_revision: Union[str, None] = '373592706c86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        bind.execute(sa.text("CREATE TYPE confidence AS ENUM('Low', 'Medium', 'High')"))
    with op.batch_alter_table('agent_outputs', schema=None) as batch_op:
        batch_op.alter_column('confidence',
               existing_type=sa.FLOAT(),
               type_=sa.Enum('Low', 'Medium', 'High', name='confidence', create_type=False),
               existing_nullable=True,
               postgresql_using='confidence::text::confidence')


def downgrade() -> None:
    with op.batch_alter_table('agent_outputs', schema=None) as batch_op:
        batch_op.alter_column('confidence',
               existing_type=sa.Enum('Low', 'Medium', 'High', name='confidence', create_type=False),
               type_=sa.FLOAT(),
               existing_nullable=True,
               postgresql_using='confidence::float')
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        bind.execute(sa.text("DROP TYPE IF EXISTS confidence"))
