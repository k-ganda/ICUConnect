"""Initial migration

Revision ID: ce1727cb3f09
Revises: 
Create Date: 2025-06-08 15:29:01.360693

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce1727cb3f09'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('hospitals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('verification_code', sa.String(length=20), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.Column('level', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('verification_code')
    )
    op.create_table('admins',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hospital_id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('privilege_level', sa.String(length=20), nullable=True),
    sa.Column('verification_docs', sa.String(length=200), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('beds',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hospital_id', sa.Integer(), nullable=False),
    sa.Column('bed_number', sa.Integer(), nullable=False),
    sa.Column('is_occupied', sa.Boolean(), nullable=True),
    sa.Column('bed_type', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('hospital_id', 'bed_number', name='_hospital_bed_uc')
    )
    op.create_table('discharges',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hospital_id', sa.Integer(), nullable=False),
    sa.Column('patient_name', sa.String(length=100), nullable=False),
    sa.Column('bed_number', sa.Integer(), nullable=False),
    sa.Column('admission_time', sa.DateTime(), nullable=False),
    sa.Column('discharge_time', sa.DateTime(), nullable=True),
    sa.Column('discharging_doctor', sa.String(length=100), nullable=False),
    sa.Column('discharge_type', sa.String(length=50), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('admissions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hospital_id', sa.Integer(), nullable=False),
    sa.Column('patient_name', sa.String(length=100), nullable=False),
    sa.Column('bed_id', sa.Integer(), nullable=False),
    sa.Column('doctor', sa.String(length=100), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('priority', sa.String(length=20), nullable=True),
    sa.Column('admission_time', sa.DateTime(), nullable=True),
    sa.Column('discharge_time', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['bed_id'], ['beds.id'], ),
    sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hospital_id', sa.Integer(), nullable=False),
    sa.Column('admin_id', sa.Integer(), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('employee_id', sa.String(length=50), nullable=False),
    sa.Column('role', sa.String(length=30), nullable=True),
    sa.Column('is_approved', sa.Boolean(), nullable=True),
    sa.Column('approval_date', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ),
    sa.ForeignKeyConstraint(['hospital_id'], ['hospitals.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    op.drop_table('admissions')
    op.drop_table('discharges')
    op.drop_table('beds')
    op.drop_table('admins')
    op.drop_table('hospitals')
    # ### end Alembic commands ###
