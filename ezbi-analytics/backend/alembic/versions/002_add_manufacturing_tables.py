"""Add manufacturing and ML tables

Revision ID: 002
Revises: 001
Create Date: 2024-07-14 14:52:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create manufacturing_data table
    op.create_table('manufacturing_data',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('machine_id', sa.String(), nullable=False),
        sa.Column('production_quantity', sa.Float(), default=0),
        sa.Column('quality_score', sa.Float(), default=0),
        sa.Column('efficiency', sa.Float(), default=0),
        sa.Column('energy_consumption', sa.Float(), default=0),
        sa.Column('maintenance_indicator', sa.Float(), default=0),
        sa.Column('temperature', sa.Float(), default=0),
        sa.Column('pressure', sa.Float(), default=0),
        sa.Column('vibration', sa.Float(), default=0),
        sa.Column('raw_data', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_manufacturing_data_timestamp', 'manufacturing_data', ['timestamp'])
    op.create_index('ix_manufacturing_data_machine_id', 'manufacturing_data', ['machine_id'])

    # Create cash_flow_data table
    op.create_table('cash_flow_data',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('company_identifier', sa.String(), nullable=False),
        sa.Column('net_cash_flow', sa.Float(), default=0),
        sa.Column('operating_cash_flow', sa.Float(), default=0),
        sa.Column('investment_cash_flow', sa.Float(), default=0),
        sa.Column('financing_cash_flow', sa.Float(), default=0),
        sa.Column('cash_flow_growth_rate', sa.Float(), default=0),
        sa.Column('operating_ratio', sa.Float(), default=0),
        sa.Column('investment_ratio', sa.Float(), default=0),
        sa.Column('financing_ratio', sa.Float(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cash_flow_data_date', 'cash_flow_data', ['date'])
    op.create_index('ix_cash_flow_data_company_identifier', 'cash_flow_data', ['company_identifier'])

    # Create ml_models table
    op.create_table('ml_models',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('model_type', sa.String(), nullable=False),
        sa.Column('hyperparameters', sa.JSON()),
        sa.Column('feature_columns', sa.JSON()),
        sa.Column('target_column', sa.String()),
        sa.Column('accuracy', sa.Float(), default=0),
        sa.Column('mse', sa.Float(), default=0),
        sa.Column('mae', sa.Float(), default=0),
        sa.Column('r2_score', sa.Float(), default=0),
        sa.Column('status', sa.String(), default='training'),
        sa.Column('training_data_size', sa.Integer(), default=0),
        sa.Column('training_start_time', sa.DateTime()),
        sa.Column('training_end_time', sa.DateTime()),
        sa.Column('model_path', sa.String()),
        sa.Column('scaler_path', sa.String()),
        sa.Column('description', sa.Text()),
        sa.Column('created_by', sa.String()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], )
    )

    # Create prediction_results table
    op.create_table('prediction_results',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('model_id', sa.String(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('model_version', sa.String(), default='1.0'),
        sa.Column('prediction_type', sa.String(), nullable=False),
        sa.Column('prediction_horizon', sa.Integer(), default=30),
        sa.Column('confidence_score', sa.Float(), default=0),
        sa.Column('input_data', sa.JSON()),
        sa.Column('prediction_value', sa.Float()),
        sa.Column('prediction_data', sa.JSON()),
        sa.Column('feature_importance', sa.JSON()),
        sa.Column('explanation', sa.Text()),
        sa.Column('processing_time_ms', sa.Integer(), default=0),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('user_id', sa.String()),
        sa.Column('company_id', sa.String()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    op.create_index('ix_prediction_results_model_id', 'prediction_results', ['model_id'])

    # Create data_uploads table
    op.create_table('data_uploads',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), default=0),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('upload_status', sa.String(), default='processing'),
        sa.Column('records_count', sa.Integer(), default=0),
        sa.Column('errors_count', sa.Integer(), default=0),
        sa.Column('validation_results', sa.JSON()),
        sa.Column('processing_log', sa.Text()),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('company_id', sa.String()),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

    # Create kpis table
    op.create_table('kpis',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('calculation_method', sa.String(), nullable=False),
        sa.Column('target_value', sa.Float()),
        sa.Column('unit', sa.String(), default=''),
        sa.Column('current_value', sa.Float(), default=0),
        sa.Column('previous_value', sa.Float(), default=0),
        sa.Column('trend_direction', sa.String(), default='stable'),
        sa.Column('warning_threshold', sa.Float()),
        sa.Column('critical_threshold', sa.Float()),
        sa.Column('last_calculated', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('calculation_frequency', sa.String(), default='daily'),
        sa.Column('company_id', sa.String()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('kpis')
    op.drop_table('data_uploads')
    op.drop_index('ix_prediction_results_model_id', table_name='prediction_results')
    op.drop_table('prediction_results')
    op.drop_table('ml_models')
    op.drop_index('ix_cash_flow_data_company_identifier', table_name='cash_flow_data')
    op.drop_index('ix_cash_flow_data_date', table_name='cash_flow_data')
    op.drop_table('cash_flow_data')
    op.drop_index('ix_manufacturing_data_machine_id', table_name='manufacturing_data')
    op.drop_index('ix_manufacturing_data_timestamp', table_name='manufacturing_data')
    op.drop_table('manufacturing_data')