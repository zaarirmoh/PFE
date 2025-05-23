from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from themes.services import AutoThemeAssignmentService

User = get_user_model()

# example usage : 
# python manage.py auto_assign_teams 4siw --min_members 3 --max_members 5
class Command(BaseCommand):
    help = 'Automatically assigns themes to teams based on academic year matching'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=str,
            required=True,
            help='Academic year to process (e.g., "2", "3", "4siw")'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            required=True,
            help='ID of the user performing the assignment (typically admin)'
        )
        parser.add_argument(
            '--max_teams_per_theme',
            type=int,
            default=10,
            help='Maximum number of teams per theme (optional)'
        )

    def handle(self, *args, **options):
        academic_year = options['year']
        user_id = options['user_id']
        max_teams_per_theme = options['max_teams_per_theme']

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"User with ID {user_id} does not exist"))
            return

        self.stdout.write(self.style.SUCCESS(f"Starting theme assignment for year {academic_year}..."))
        
        result = AutoThemeAssignmentService.assign_themes_for_year(academic_year, user, max_teams_per_theme)
        
        if 'error' in result:
            self.stderr.write(self.style.ERROR(result['error']))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Successfully assigned {result['assignments_created']} themes to teams\n"
            f"Teams without theme: {result['remaining_teams']}\n"
            f"Themes remaining: {result['remaining_themes']}"
        ))