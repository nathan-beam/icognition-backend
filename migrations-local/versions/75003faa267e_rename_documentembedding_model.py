"""Rename DocumentEmbedding Model

Revision ID: 75003faa267e
Revises: d8d421a2e063
Create Date: 2024-04-04 18:17:29.525513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import pgvector
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '75003faa267e'
down_revision: Union[str, None] = 'd8d421a2e063'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('document_embeddings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('field', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('embeddings', pgvector.sqlalchemy.Vector(dim=384), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('documentembeddings')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('documentembeddings',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('document_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('field', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('embeddings', pgvector.sqlalchemy.Vector(dim=384), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='documentembeddings_pkey')
    )
    op.drop_table('document_embeddings')
    # ### end Alembic commands ###
