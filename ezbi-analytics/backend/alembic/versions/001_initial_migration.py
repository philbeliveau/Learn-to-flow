"""Initial migration with all models

Revision ID: 001
Revises: 
Create Date: 2024-07-14 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('role', sa.Enum('admin', 'manager', 'analyst', 'user', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('siret', sa.String(length=14), nullable=False),
        sa.Column('siren', sa.String(length=9), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=10), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_companies_siret'), 'companies', ['siret'], unique=True)
    op.create_index(op.f('ix_companies_siren'), 'companies', ['siren'], unique=False)

    # Create manufacturing_processes table
    op.create_table(
        'manufacturing_processes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('process_name', sa.String(length=255), nullable=False),
        sa.Column('process_type', sa.String(length=100), nullable=False),
        sa.Column('stage', sa.String(length=100), nullable=False),
        sa.Column('machine_id', sa.String(length=100), nullable=True),
        sa.Column('operator_id', sa.String(length=100), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('pressure', sa.Float(), nullable=True),
        sa.Column('humidity', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('vibration', sa.Float(), nullable=True),
        sa.Column('power_consumption', sa.Float(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('defect_rate', sa.Float(), nullable=True),
        sa.Column('production_volume', sa.Integer(), nullable=True),
        sa.Column('cycle_time', sa.Float(), nullable=True),
        sa.Column('downtime_minutes', sa.Float(), nullable=True),
        sa.Column('efficiency_score', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_manufacturing_processes_timestamp'), 'manufacturing_processes', ['timestamp'], unique=False)

    # Create manufacturing_costs table
    op.create_table(
        'manufacturing_costs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('cost_category', sa.String(length=100), nullable=False),
        sa.Column('cost_type', sa.String(length=100), nullable=False),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('product_line', sa.String(length=100), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('allocation_method', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_manufacturing_costs_period_start'), 'manufacturing_costs', ['period_start'], unique=False)

    # Create cash_flow_data table
    op.create_table(
        'cash_flow_data',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('operating_cash_flow', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('investing_cash_flow', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('financing_cash_flow', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('net_cash_flow', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('cash_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('accounts_receivable', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('accounts_payable', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('inventory_value', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('revenue', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('expenses', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cash_flow_data_date'), 'cash_flow_data', ['date'], unique=False)

    # Create ml_models table
    op.create_table(
        'ml_models',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('model_type', sa.String(length=100), nullable=False),
        sa.Column('target_variable', sa.String(length=100), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=True),
        sa.Column('model_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('training_data_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('performance_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('model_file_path', sa.String(length=500), nullable=True),
        sa.Column('feature_columns', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('trained_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create predictions table
    op.create_table(
        'predictions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('model_id', sa.UUID(), nullable=False),
        sa.Column('company_id', sa.UUID(), nullable=False),
        sa.Column('prediction_type', sa.String(length=100), nullable=False),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('predicted_value', sa.Float(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('confidence_interval_lower', sa.Float(), nullable=True),
        sa.Column('confidence_interval_upper', sa.Float(), nullable=True),
        sa.Column('prediction_date', sa.Date(), nullable=False),
        sa.Column('horizon_days', sa.Integer(), nullable=True),
        sa.Column('explanation', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['model_id'], ['ml_models.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_predictions_prediction_date'), 'predictions', ['prediction_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_predictions_prediction_date'), table_name='predictions')
    op.drop_table('predictions')
    op.drop_table('ml_models')
    op.drop_index(op.f('ix_cash_flow_data_date'), table_name='cash_flow_data')
    op.drop_table('cash_flow_data')
    op.drop_index(op.f('ix_manufacturing_costs_period_start'), table_name='manufacturing_costs')
    op.drop_table('manufacturing_costs')
    op.drop_index(op.f('ix_manufacturing_processes_timestamp'), table_name='manufacturing_processes')
    op.drop_table('manufacturing_processes')
    op.drop_index(op.f('ix_companies_siren'), table_name='companies')
    op.drop_index(op.f('ix_companies_siret'), table_name='companies')
    op.drop_table('companies')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')