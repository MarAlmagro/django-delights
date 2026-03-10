# Generated migration for AuditLog model enhancements

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("delights", "0003_add_performance_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="object_repr",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="user_agent",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.AlterField(
            model_name="auditlog",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="audit_logs",
                to="auth.user",
            ),
        ),
    ]
