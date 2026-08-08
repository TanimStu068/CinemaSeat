"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-08-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('movies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.Column('poster_url', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_movies_id'), 'movies', ['id'], unique=False)
    
    op.create_table('theatres',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('location', sa.String(length=255), nullable=True),
    sa.Column('rows', sa.Integer(), nullable=False),
    sa.Column('cols', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_theatres_id'), 'theatres', ['id'], unique=False)
    
    op.create_table('showtimes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('movie_id', sa.Integer(), nullable=True),
    sa.Column('theatre_id', sa.Integer(), nullable=True),
    sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('price', sa.Numeric(precision=8, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['movie_id'], ['movies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['theatre_id'], ['theatres.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_showtimes_id'), 'showtimes', ['id'], unique=False)
    
    op.create_table('seats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('showtime_id', sa.Integer(), nullable=True),
    sa.Column('row_label', sa.String(length=5), nullable=False),
    sa.Column('col_number', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('held_by', sa.String(length=255), nullable=True),
    sa.Column('held_until', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['showtime_id'], ['showtimes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('showtime_id', 'row_label', 'col_number')
    )
    op.create_index(op.f('ix_seats_id'), 'seats', ['id'], unique=False)
    
    op.create_table('bookings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('booking_ref', sa.String(length=255), nullable=False),
    sa.Column('seat_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('payment_id', sa.String(length=255), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('event_id', sa.String(length=255), nullable=True),
    sa.Column('amount', sa.Numeric(precision=8, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['seat_id'], ['seats.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('event_id')
    )
    op.create_index(op.f('ix_bookings_booking_ref'), 'bookings', ['booking_ref'], unique=True)
    op.create_index(op.f('ix_bookings_id'), 'bookings', ['id'], unique=False)
    op.create_index(op.f('ix_bookings_status'), 'bookings', ['status'], unique=False)

def downgrade() -> None:
    op.drop_table('bookings')
    op.drop_table('seats')
    op.drop_table('showtimes')
    op.drop_table('theatres')
    op.drop_table('movies')
