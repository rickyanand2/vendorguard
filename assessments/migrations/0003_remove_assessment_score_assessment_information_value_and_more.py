# Generated by Django 5.2.3 on 2025-07-14 08:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0002_answer_created_at_answer_created_by_answer_evidence_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assessment',
            name='score',
        ),
        migrations.AddField(
            model_name='assessment',
            name='information_value',
            field=models.CharField(choices=[('low', 'Low - Public or non-sensitive'), ('moderate', 'Moderate - Internal or confidential'), ('high', 'High - Regulated or sensitive'), ('critical', 'Critical - Highly sensitive or life-impacting')], default='moderate', help_text='Based on criticality of the data/function being assessed', max_length=20),
        ),
        migrations.AddField(
            model_name='assessment',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='assessment',
            name='recommended_score',
            field=models.FloatField(default=0.0, help_text='System-generated score from answers (0–100 scale)'),
        ),
        migrations.AddField(
            model_name='assessment',
            name='risk_level',
            field=models.CharField(choices=[('undetermined', 'Undetermined'), ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='undetermined', help_text='Risk level decided after manual review or tagging', max_length=20),
        ),
        migrations.AddField(
            model_name='certification',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='question',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='question',
            name='tags',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='question',
            name='category',
            field=models.CharField(choices=[('data_protection', 'Data Protection'), ('access_control', 'Access Control'), ('incident_response', 'Incident Response'), ('compliance', 'Regulatory Compliance'), ('bc_dr', 'Business Continuity & DR'), ('third_party', 'Third-Party Risk'), ('cloud_security', 'Cloud Security'), ('vuln_mgmt', 'Vulnerability Management')], default='data_protection', max_length=50),
        ),
        migrations.AlterField(
            model_name='question',
            name='questionnaire',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='assessments.questionnaire'),
        ),
    ]
