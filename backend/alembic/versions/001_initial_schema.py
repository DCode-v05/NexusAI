"""Initial schema — all NexusAI tables

Revision ID: 001
Revises:
Create Date: 2026-03-14
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("student", "counselor", "admin", name="userrole"), nullable=False, server_default="student"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # students
    op.create_table(
        "students",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("program", sa.String(200), nullable=True),
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("cgpa", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_students_user_id", "students", ["user_id"])

    # behavior_logs
    op.create_table(
        "behavior_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id"), nullable=False),
        sa.Column("session_gap_days", sa.Float, nullable=False, server_default="0"),
        sa.Column("survey_skip_streak", sa.Integer, nullable=False, server_default="0"),
        sa.Column("avg_session_length", sa.Float, nullable=False, server_default="0"),
        sa.Column("assignment_delay_hrs", sa.Float, nullable=False, server_default="0"),
        sa.Column("chat_initiation_freq", sa.Float, nullable=False, server_default="0"),
        sa.Column("mood_score_trend", sa.Float, nullable=False, server_default="0"),
        sa.Column("login_hour_variance", sa.Float, nullable=False, server_default="0"),
        sa.Column("logged_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_behavior_logs_student_id", "behavior_logs", ["student_id"])

    # mood_surveys
    op.create_table(
        "mood_surveys",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id"), nullable=False),
        sa.Column("q1_score", sa.Integer, nullable=False),
        sa.Column("q2_score", sa.Integer, nullable=False),
        sa.Column("q3_score", sa.Integer, nullable=False),
        sa.Column("composite_score", sa.Float, nullable=False),
        sa.Column("free_text", sa.String(2000), nullable=True),
        sa.Column("submitted_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_mood_surveys_student_id", "mood_surveys", ["student_id"])

    # wellbeing_alerts
    op.create_table(
        "wellbeing_alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id"), nullable=False),
        sa.Column("risk_score", sa.Float, nullable=False),
        sa.Column("anomaly_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("sentiment_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("survey_decline", sa.Float, nullable=False, server_default="0"),
        sa.Column("tier", sa.Enum("low", "moderate", "high", "crisis", name="risktier"), nullable=False),
        sa.Column("is_resolved", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_wellbeing_alerts_student_id", "wellbeing_alerts", ["student_id"])

    # skill_profiles
    op.create_table(
        "skill_profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id"), nullable=False, unique=True),
        sa.Column("skills", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("target_role", sa.String(200), nullable=True),
        sa.Column("target_location", sa.String(200), nullable=True),
        sa.Column("raw_resume_text", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # career_roadmaps
    op.create_table(
        "career_roadmaps",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("skill_profile_id", sa.Integer, sa.ForeignKey("skill_profiles.id"), nullable=False),
        sa.Column("target_role", sa.String(200), nullable=False),
        sa.Column("roadmap_json", sa.JSON, nullable=False),
        sa.Column("generated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # counselor_alerts
    op.create_table(
        "counselor_alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id"), nullable=False),
        sa.Column("risk_score", sa.Float, nullable=False),
        sa.Column("anomaly_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("sentiment_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("survey_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("triggered_keywords", sa.String(500), nullable=True),
        sa.Column("is_resolved", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_counselor_alerts_student_id", "counselor_alerts", ["student_id"])

    # case_notes
    op.create_table(
        "case_notes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("alert_id", sa.Integer, sa.ForeignKey("counselor_alerts.id"), nullable=False),
        sa.Column("counselor_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("note_text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("case_notes")
    op.drop_table("counselor_alerts")
    op.drop_table("career_roadmaps")
    op.drop_table("skill_profiles")
    op.drop_table("wellbeing_alerts")
    op.drop_table("mood_surveys")
    op.drop_table("behavior_logs")
    op.drop_table("students")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS risktier")
