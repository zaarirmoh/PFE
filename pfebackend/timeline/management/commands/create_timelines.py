from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from timeline.models import Timeline

class Command(BaseCommand):
    help = 'Creates timelines for all academic program and year combinations'

    def handle(self, *args, **options):
        # Program-year combinations
        combinations = [
            {'program': Timeline.PREPARATORY, 'year': 1},
            {'program': Timeline.PREPARATORY, 'year': 2},
            {'program': Timeline.SUPERIOR, 'year': 1},
            {'program': Timeline.SUPERIOR, 'year': 2},
            {'program': Timeline.SUPERIOR, 'year': 3},
        ]
        
        # Timeline types and defaults
        timeline_types = [
            {
                'type': Timeline.GROUPS,
                'name_template': '{program} Year {year} - Groups Formation',
                'description': 'Timeline for forming project groups',
                'duration': 14  # days
            },
            {
                'type': Timeline.THEMES,
                'name_template': '{program} Year {year} - Theme Selection',
                'description': 'Timeline for selecting project themes',
                'duration': 14  # days
            },
            {
                'type': Timeline.WORK,
                'name_template': '{program} Year {year} - Project Work',
                'description': 'Timeline for project implementation and development',
                'duration': 60  # days
            },
            {
                'type': Timeline.SOUTENANCE,
                'name_template': '{program} Year {year} - Soutenance',
                'description': 'Timeline for project defense and presentation',
                'duration': 14  # days
            }
        ]

        # Define timeline types
        timeline_types = [
            {"slug": Timeline.GROUPS, "name": "Groups Formation", "description": "Timeline for forming project groups"},
            {"slug": Timeline.THEMES, "name": "Theme Selection", "description": "Timeline for selecting project themes"},
            {"slug": Timeline.WORK, "name": "Project Work", "description": "Timeline for project implementation and development"},
            {"slug": Timeline.SOUTENANCE, "name": "Soutenance", "description": "Timeline for project defense and presentation"}
        ]

        created_count = 0
        updated_count = 0
        
        # Set base start date
        now = timezone.now()
        
        for combination in combinations:
            program = combination['program']
            year = combination['year']
            program_display = 'Preparatory' if program == Timeline.PREPARATORY else 'Superior'
            
            # Starting date for this program-year combination
            start_date = now
            
            for timeline_info in timeline_types:
                # Generate timeline data
                timeline_type = timeline_info['type']
                name = timeline_info['name_template'].format(program=program_display, year=year)
                description = timeline_info['description']
                duration = timeline_info['duration']
                
                # Set dates
                end_date = start_date + timedelta(days=duration)
                
                # Generate slug
                slug = f"{timeline_type}-{program}-{year}"
                
                # Create or update timeline
                timeline, created = Timeline.objects.update_or_create(
                    timeline_type=timeline_type,
                    academic_program=program,
                    academic_year=year,
                    defaults={
                        'slug': slug,
                        'name': name,
                        'description': description,
                        'start_date': start_date,
                        'end_date': end_date,
                        'is_active': True
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Created timeline: {timeline.name}'))
                else:
                    updated_count += 1
                    self.stdout.write(f'Updated timeline: {timeline.name}')
                
                # Update start date for next timeline in this program-year
                start_date = end_date
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new timelines, updated {updated_count} existing timelines'))
