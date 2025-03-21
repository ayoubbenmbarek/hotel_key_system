"""Initial migration

Revision ID: 3cd6d1045857
Revises: 73cd78d7b427
Create Date: 2025-03-05 21:36:16.564937

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3cd6d1045857'
down_revision = '73cd78d7b427'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('device_registrations')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('device_registrations',
    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('device_library_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('pass_type_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('serial_number', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('push_token', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('active', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('digital_key_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['digital_key_id'], ['digitalkey.id'], name='device_registrations_digital_key_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='device_registrations_pkey'),
    sa.UniqueConstraint('device_library_id', 'pass_type_id', 'serial_number', name='device_pass_unique')
    )
    # ### end Alembic commands ###
