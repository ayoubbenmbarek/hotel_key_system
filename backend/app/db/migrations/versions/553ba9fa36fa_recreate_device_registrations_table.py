"""Recreate device_registrations table

Revision ID: 553ba9fa36fa
Revises: 9523663a694c
Create Date: 2025-03-06 23:29:29.614905

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '553ba9fa36fa'
down_revision = '9523663a694c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('device_registrations',
        sa.Column('id', sa.VARCHAR(), nullable=False),
        sa.Column('device_library_id', sa.VARCHAR(), nullable=False),
        sa.Column('pass_type_id', sa.VARCHAR(), nullable=False),
        sa.Column('serial_number', sa.VARCHAR(), nullable=False),
        sa.Column('push_token', sa.VARCHAR(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('active', sa.BOOLEAN(), server_default=sa.text('true'), nullable=True),
        sa.Column('digital_key_id', sa.VARCHAR(), nullable=True),
        sa.ForeignKeyConstraint(['digital_key_id'], ['digitalkey.id'], name='device_registrations_digital_key_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='device_registrations_pkey'),
        sa.UniqueConstraint('device_library_id', 'pass_type_id', 'serial_number', name='device_pass_unique')
    )

def downgrade():
    op.drop_table('device_registrations')
