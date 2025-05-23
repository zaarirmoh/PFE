from django.core.management.base import BaseCommand, CommandError
from teams.services.auto_team_assignment_service import AutoTeamAssignmentService

# example usage : 
# python manage.py auto_assign_teams 4siw --min_members 3 --max_members 5
class Command(BaseCommand):
    help = 'Automatically assign teamless students to teams for a specific academic year'

    def add_arguments(self, parser):
        parser.add_argument('academic_year', type=str, help='The academic year to process (e.g., "4siw")')
        parser.add_argument(
            '--min_members',
            type=int,
            default=3,
            help='Minimum number of members per team',
        )
        parser.add_argument(
            '--max_members',
            type=int,
            default=5,
            help='Maximum number of members per team',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would happen without making actual changes',
        )

    def handle(self, *args, **options):
        academic_year = options['academic_year']
        min_members = options['min_members']
        max_members = options['max_members']
        dry_run = options.get('dry_run', False)

        self.stdout.write(self.style.SUCCESS(
            f"Running auto team assignment for academic year '{academic_year}' "
            f"with min_members={min_members}, max_members={max_members}"
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE: No actual changes will be made"))

        try:
            if not dry_run:
                result = AutoTeamAssignmentService.reassign_students_for_year(
                    academic_year, min_members, max_members
                )
            else:
                self.stdout.write("DRY RUN: Would run reassign_students_for_year")
                return

            if "error" in result:
                self.stdout.write(self.style.ERROR(f"Error: {result['error']}"))
                return

            self.stdout.write(self.style.SUCCESS("\nAssignment Results:"))
            self.stdout.write(f"Academic Year: {result['academic_year']}")
            self.stdout.write(f"Min Members: {result['min_members']}")
            self.stdout.write(f"Max Members: {result['max_members']}")
            self.stdout.write(f"Teams Deleted: {result['teams_deleted']}")
            self.stdout.write(f"Students Freed from Deleted Teams: {result['students_freed']}")
            self.stdout.write(f"New Teams Created: {result['teams_created']}")
            self.stdout.write(f"Students Reassigned: {result['students_reassigned']}")
            self.stdout.write(f"Students Remaining Unassigned: {result['students_remaining']}")

            if 'team_distribution' in result and result['team_distribution']:
                self.stdout.write("\nTeam Size Distribution:")
                for size, count in result['team_distribution'].items():
                    self.stdout.write(f"  Teams with {size} members: {count}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to perform assignment: {str(e)}"))