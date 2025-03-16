from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from timeline.models import Timeline

class Command(BaseCommand):
    help = 'Creates the four default timelines if they do not exist'

    def handle(self, *args, **options):
        # Create default dates (just as examples)
        now = timezone.now()
        groups_start = now
        groups_end = now + timedelta(days=14)
        themes_start = groups_end
        themes_end = themes_start + timedelta(days=14)
        work_start = themes_end
        work_end = work_start + timedelta(days=60)
        soutenance_start = work_end
        soutenance_end = soutenance_start + timedelta(days=14)
        
        timelines = [
            {
                'slug': Timeline.GROUPS,
                'name': 'Groups Formation',
                'description': 'Timeline for forming project groups',
                'start_date': groups_start,
                'end_date': groups_end
            },
            {
                'slug': Timeline.THEMES,
                'name': 'Theme Selection',
                'description': 'Timeline for selecting project themes',
                'start_date': themes_start,
                'end_date': themes_end
            },
            {
                'slug': Timeline.WORK,
                'name': 'Project Work',
                'description': 'Timeline for project implementation and development',
                'start_date': work_start,
                'end_date': work_end
            },
            {
                'slug': Timeline.SOUTENANCE,
                'name': 'Soutenance',
                'description': 'Timeline for project defense and presentation',
                'start_date': soutenance_start,
                'end_date': soutenance_end
            }
        ]
        
        created_count = 0
        for timeline_data in timelines:
            timeline, created = Timeline.objects.get_or_create(
                slug=timeline_data['slug'],
                defaults={
                    'name': timeline_data['name'],
                    'description': timeline_data['description'],
                    'start_date': timeline_data['start_date'],
                    'end_date': timeline_data['end_date']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created timeline: {timeline.name}'))
            else:
                self.stdout.write(f'Timeline already exists: {timeline.name}')
                
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new timelines'))