# Generated by Django 5.1.6 on 2025-05-22 18:25

import django.db.models.deletion
import teams.mixins
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('documents', '0001_initial'),
        ('teams', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation Date')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Update Date')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('tools', models.TextField(help_text='Enter tools')),
                ('is_verified', models.BooleanField(default=False, help_text='Indicates if the theme has been verified by the administration.')),
                ('academic_year', models.CharField(choices=[('2', '2nd Year'), ('3', '3rd Year'), ('4siw', '4th Year SIW'), ('4isi', '4th Year ISI'), ('4iasd', '4th Year IASD'), ('5siw', '5th Year SIW'), ('5isi', '5th Year ISI'), ('5iasd', '5th Year IASD')], help_text='Academic year for which the theme is proposed', max_length=5)),
                ('co_supervisors', models.ManyToManyField(blank=True, related_name='co_supervised_themes', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL, verbose_name='Created by')),
                ('documents', models.ManyToManyField(blank=True, related_name='themes', to='documents.document')),
                ('proposed_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proposed_themes', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated by')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ThemeAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation Date')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Update Date')),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
                ('assigned_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='theme_assignments', to=settings.AUTH_USER_MODEL)),
                ('team', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_theme', to='teams.team')),
                ('theme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_teams', to='themes.theme')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('team',), name='unique_team_assignment')],
            },
        ),
        migrations.CreateModel(
            name='ThemeSupervisionRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation Date')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Update Date')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('expired', 'Expired'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('message', models.TextField(blank=True, help_text='Optional message from the team')),
                ('response_message', models.TextField(blank=True, help_text='Optional response message from the supervisor')),
                ('invitee', models.ForeignKey(help_text='The supervisor being invited to supervise the theme', on_delete=django.db.models.deletion.CASCADE, related_name='received_supervision_requests', to=settings.AUTH_USER_MODEL)),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_supervision_requests', to=settings.AUTH_USER_MODEL)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supervision_requests', to='teams.team')),
                ('theme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supervision_requests', to='themes.theme')),
            ],
            options={
                'constraints': [models.UniqueConstraint(condition=models.Q(('status__in', ['PENDING', 'ACCEPTED'])), fields=('team', 'theme'), name='unique_active_supervision_request')],
            },
            bases=(teams.mixins.TeamRequestStatusMixin, models.Model),
        ),
    ]
