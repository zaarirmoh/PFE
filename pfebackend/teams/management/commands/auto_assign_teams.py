from django.core.management.base import BaseCommand, CommandError
from teams.services.auto_team_assignment_service import AutoTeamAssignmentService

# example usage : python manage.py auto_assign_teams timeline_slug
class Command(BaseCommand):
    help = 'Automatically assign teamless students to teams when a timeline ends'

    def add_arguments(self, parser):
        parser.add_argument('timeline_slug', type=str, help='The slug of the timeline that has ended')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would happen without making actual changes',
        )

    def handle(self, *args, **options):
        timeline_slug = options['timeline_slug']
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS(f"Running auto team assignment for timeline '{timeline_slug}'"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE: No actual changes will be made"))
            
        try:
            # Run the assignment process
            if not dry_run:
                result = AutoTeamAssignmentService.assign_students_after_timeline(timeline_slug)
            else:
                # Just get the counts without making assignments
                # Note: In a real implementation, you might want to add a dry_run parameter to the service
                self.stdout.write("Dry run not implemented in this version. Would call auto-assignment service here.")
                return
                
            if "error" in result:
                self.stdout.write(self.style.ERROR(f"Error: {result['error']}"))
                return
                
            # Display results
            self.stdout.write(self.style.SUCCESS("\nAssignment Results:"))
            self.stdout.write(f"Total students assigned: {result['total_assigned']}")
            self.stdout.write(f"Total students unassigned: {result['total_unassigned']}")
            
            for program, program_result in result['assignments_by_program'].items():
                self.stdout.write(f"\nProgram {program}:")
                self.stdout.write(f"  Available teams: {program_result['available_teams']}")
                self.stdout.write(f"  Teamless students: {program_result['teamless_students']}")
                self.stdout.write(f"  Students assigned: {program_result['assigned_count']}")
                self.stdout.write(f"  Students unassigned: {program_result['unassigned_count']}")
                
                if program_result['team_assignments']:
                    self.stdout.write("  Team assignments:")
                    for team_name, count in program_result['team_assignments'].items():
                        self.stdout.write(f"    {team_name}: {count} students")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to perform assignment: {str(e)}"))