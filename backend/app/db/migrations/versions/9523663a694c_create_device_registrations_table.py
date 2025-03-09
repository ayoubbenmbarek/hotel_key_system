"""Create device_registrations table

Revision ID: 9523663a694c
Revises: 63d3900ae203
Create Date: 2025-03-06 23:25:29.586600

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9523663a694c'
down_revision = '63d3900ae203'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE TABLE device_registrations (
        id VARCHAR NOT NULL PRIMARY KEY,
        device_library_id VARCHAR NOT NULL,
        pass_type_id VARCHAR NOT NULL,
        serial_number VARCHAR NOT NULL,
        push_token VARCHAR NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        active BOOLEAN DEFAULT TRUE,
        digital_key_id VARCHAR REFERENCES digitalkey(id),
        CONSTRAINT device_pass_unique UNIQUE (device_library_id, pass_type_id, serial_number)
    );
    """)

def downgrade():
    op.execute("DROP TABLE device_registrations;")
    # ### end Alembic commands ###
