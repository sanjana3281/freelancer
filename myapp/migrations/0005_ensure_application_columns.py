from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0004_job_jobskill_job_skills_required_application"),
    ]

    operations = [
        # Ensure `created_at` exists in DB (no-op if it already exists),
        # and make Django's STATE match the model (auto_now_add=True).
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE myapp_application
                        ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT NOW();
                        ALTER TABLE myapp_application
                        ALTER COLUMN created_at DROP DEFAULT;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="application",
                    name="created_at",
                    field=models.DateTimeField(auto_now_add=True),
                ),
            ],
        ),

        # Ensure `resume` exists in DB (this is your missing column)
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE myapp_application
                        ADD COLUMN IF NOT EXISTS resume varchar(100);
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="application",
                    name="resume",
                    field=models.FileField(upload_to="applications/resumes/", blank=True, null=True),
                ),
            ],
        ),

        # (Optional) Drop legacy columns if they linger; keep state consistent
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE myapp_application DROP COLUMN IF EXISTS submitted_at;",
                    reverse_sql="ALTER TABLE myapp_application ADD COLUMN submitted_at timestamp with time zone;",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE myapp_application DROP COLUMN IF EXISTS updated_at;",
                    reverse_sql="ALTER TABLE myapp_application ADD COLUMN updated_at timestamp with time zone;",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE myapp_application DROP COLUMN IF EXISTS status;",
                    reverse_sql="ALTER TABLE myapp_application ADD COLUMN status varchar(20);",
                ),
            ],
            state_operations=[
                # These are safe even if the fields aren't in the current model
                # If you never had them in your model, you can omit these three lines.
                # Keeping them here makes state match DB if they used to exist.
                # If Django complains, just remove the corresponding RemoveField.
                # migrations.RemoveField(model_name="application", name="submitted_at"),
                # migrations.RemoveField(model_name="application", name="updated_at"),
                # migrations.RemoveField(model_name="application", name="status"),
            ],
        ),
    ]

