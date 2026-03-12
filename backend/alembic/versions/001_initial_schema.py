"""Create initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    sa.Enum('uploaded', 'processing', 'completed', 'failed', name='tenderstatus').create(op.get_bind(), checkfirst=True)
    sa.Enum('eligible', 'partially_eligible', 'not_eligible', name='eligibilityverdict').create(op.get_bind(), checkfirst=True)
    sa.Enum('low', 'medium', 'high', name='risklevel').create(op.get_bind(), checkfirst=True)
    sa.Enum('low', 'medium', 'high', name='effortlevel').create(op.get_bind(), checkfirst=True)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create company_profiles table
    op.create_table(
        'company_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('annual_turnover', sa.Numeric(), nullable=True),
        sa.Column('certifications', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('past_experience_years', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create tenders table
    op.create_table(
        'tenders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('language_detected', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('uploaded', 'processing', 'completed', 'failed', name='tenderstatus'), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['company_profiles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create tender_sections table
    op.create_table(
        'tender_sections',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tender_id', sa.UUID(), nullable=False),
        sa.Column('section_name', sa.String(), nullable=False),
        sa.Column('section_text', sa.Text(), nullable=False),
        sa.Column('page_range', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create clauses table
    op.create_table(
        'clauses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('section_id', sa.UUID(), nullable=False),
        sa.Column('clause_text', sa.Text(), nullable=False),
        sa.Column('clause_order', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['section_id'], ['tender_sections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create evaluations table
    op.create_table(
        'evaluations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tender_id', sa.UUID(), nullable=False),
        sa.Column('eligibility_verdict', sa.Enum('eligible', 'partially_eligible', 'not_eligible', name='eligibilityverdict'), nullable=False),
        sa.Column('eligibility_score', sa.Integer(), nullable=True),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('risk_level', sa.Enum('low', 'medium', 'high', name='risklevel'), nullable=True),
        sa.Column('effort_score', sa.Integer(), nullable=True),
        sa.Column('effort_level', sa.Enum('low', 'medium', 'high', name='effortlevel'), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('missing_documents', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('risk_factors', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tender_id')
    )
    
    # Create clause_evaluations table
    op.create_table(
        'clause_evaluations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('evaluation_id', sa.UUID(), nullable=False),
        sa.Column('clause_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['clause_id'], ['clauses.id'], ),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('clause_evaluations')
    op.drop_table('evaluations')
    op.drop_table('clauses')
    op.drop_table('tender_sections')
    op.drop_table('tenders')
    op.drop_table('company_profiles')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
