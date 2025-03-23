from django.core.management.base import BaseCommand
from django.db import transaction
from teams.models import TeamSettings

class Command(BaseCommand):
    help = 'Create team settings for specific academic program-year combinations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-members',
            type=int,
            default=TeamSettings.DEFAULT_MAX_MEMBERS,
            help=f'Maximum number of members for teams (default: {TeamSettings.DEFAULT_MAX_MEMBERS})',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if settings already exist',
        )

    def handle(self, *args, **options):
        # Define the specific program-year combinations we need
        program_year_combinations = [
            ('preparatory', 1),
            ('preparatory', 2),
            ('superior', 1),
            ('superior', 2),
            ('superior', 3),
        ]
        
        max_members = options['max_members']
        force_update = options['force']
        
        self.stdout.write(self.style.NOTICE('Creating or updating team settings for specific combinations:'))
        for program, year in program_year_combinations:
            self.stdout.write(self.style.NOTICE(f'- {program.capitalize()} Year {year}'))
        self.stdout.write(self.style.NOTICE(f'Maximum members: {max_members}'))
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for program, year in program_year_combinations:
                try:
                    # Try to get existing settings
                    settings, created = TeamSettings.objects.get_or_create(
                        academic_program=program,
                        academic_year=year,
                        defaults={
                            'maximum_members': max_members,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Created settings for {program.capitalize()} Year {year}')
                        )
                    elif force_update:
                        # Update existing settings
                        settings.maximum_members = max_members
                        settings.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'Updated settings for {program.capitalize()} Year {year}')
                        )
                    else:
                        skipped_count += 1
                        self.stdout.write(
                            self.style.NOTICE(f'Skipped existing settings for {program.capitalize()} Year {year} (use --force to update)')
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating settings for {program.capitalize()} Year {year}: {str(e)}')
                    )
        
        self.stdout.write(self.style.SUCCESS(f'Operation complete.'))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}'))