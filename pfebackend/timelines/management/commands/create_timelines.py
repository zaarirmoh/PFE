from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from timelines.models import Timeline

class Command(BaseCommand):
    help = 'Creates timelines for all academic program and year combinations'

    def handle(self, *args, **options):
        # Academic year configurations
        academic_years = [
            '2',       # 2nd Year
            '3',       # 3rd Year
            '4siw',    # 4th Year SIW
            '4isi',    # 4th Year ISI
            '4iasd',   # 4th Year IASD
            '5siw',    # 5th Year SIW
            '5isi',    # 5th Year ISI
            '5iasd',   # 5th Year IASD
        ]
        
        # Timeline types and defaults
        timeline_types = [
            {
                'type': Timeline.GROUPS,
                'name_template': 'Year {year} - Groups Formation',
                'description': 'Timeline for forming project groups',
                'duration': 14  # days
            },
            {
                'type': Timeline.THEMES,
                'name_template': 'Year {year} - Theme Selection',
                'description': 'Timeline for selecting project themes',
                'duration': 14  # days
            },
            {
                'type': Timeline.WORK,
                'name_template': 'Year {year} - Project Work',
                'description': 'Timeline for project implementation and development',
                'duration': 60  # days
            },
            {
                'type': Timeline.SOUTENANCE,
                'name_template': 'Year {year} - Soutenance',
                'description': 'Timeline for project defense and presentation',
                'duration': 14  # days
            }
        ]

        created_count = 0
        updated_count = 0
        
        # Set base start date
        now = timezone.now()
        
        for academic_year in academic_years:
            # Get display name for the academic year
            academic_year_display = dict(Timeline.ACADEMIC_YEAR_CHOICES).get(academic_year, academic_year)
            
            # Starting date for this academic year
            start_date = now
            
            for timeline_info in timeline_types:
                # Generate timeline data
                timeline_type = timeline_info['type']
                name = timeline_info['name_template'].format(year=academic_year_display)
                description = timeline_info['description']
                duration = timeline_info['duration']
                
                # Set dates
                end_date = start_date + timedelta(days=duration)
                
                # Generate slug
                slug = f"{timeline_type}-{academic_year}"
                
                # Create or update timeline
                timeline, created = Timeline.objects.update_or_create(
                    timeline_type=timeline_type,
                    academic_year=academic_year,
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
                
                # Update start date for next timeline in this academic year
                start_date = end_date
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new timelines, updated {updated_count} existing timelines'))