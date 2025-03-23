from django.db import transaction
from django.db.models import Count, Q, F
import random
import logging
from users.models import Student
from teams.models import Team, TeamMembership
from timelines.models import Timeline

logger = logging.getLogger(__name__)

class AutoTeamAssignmentService:
    """
    Service for automatically assigning students without teams to existing teams
    when a specific timeline ends.
    """
    
    @classmethod
    def assign_students_after_timeline(cls, timeline_slug):
        """
        Main entry point to assign teamless students after a specific timeline ends.
        
        Args:
            timeline_slug (str): The slug of the timeline that ended
            
        Returns:
            dict: Statistics about the assignments made
        """
        try:
            timeline = Timeline.objects.get(slug=timeline_slug)
            if timeline.status != 'expired':
                logger.warning(f"Timeline '{timeline_slug}' has not ended yet.")
                return {"error": "Timeline has not ended yet"}
            
            if timeline.slug != Timeline.GROUPS:
                logger.warning(f"Auto team assignment is not supported for timeline '{timeline_slug}'")
                return {"error": "Auto team assignment is not supported for this timeline"}
                
            logger.info(f"Starting auto team assignment for timeline '{timeline_slug}'")
            
            # Get all active academic years and programs combinations from existing teams
            team_academic_configs = Team.objects.values('academic_year', 'academic_program').distinct()
            
            stats = {
                "timeline": timeline_slug,
                "assignments_by_program": {},
                "total_assigned": 0,
                "total_unassigned": 0,
            }
            
            # Process each academic year and program combination
            for config in team_academic_configs:
                year = config['academic_year']
                program = config['academic_program']
                
                result = cls._assign_students_for_year_program(year, program)
                stats["assignments_by_program"][f"{year}_{program}"] = result
                stats["total_assigned"] += result["assigned_count"]
                stats["total_unassigned"] += result["unassigned_count"]
                
            logger.info(f"Auto team assignment completed: {stats['total_assigned']} students assigned")
            return stats
            
        except Timeline.DoesNotExist:
            logger.error(f"Timeline '{timeline_slug}' does not exist.")
            return {"error": f"Timeline '{timeline_slug}' does not exist"}
        except Exception as e:
            logger.exception(f"Error during auto team assignment: {str(e)}")
            return {"error": str(e)}
    
    @classmethod
    @transaction.atomic
    def _assign_students_for_year_program(cls, academic_year, academic_program):
        """
        Assign teamless students to teams with capacity for a specific academic year and program.
        Uses a database transaction to ensure consistency.
        
        Args:
            academic_year (int): The academic year
            academic_program (str): The academic program code
            
        Returns:
            dict: Statistics about the assignments made
        """
        # Find students without teams for this year/program
        teamless_students = cls._get_teamless_students(academic_year, academic_program)
        
        # Find teams with capacity for this year/program
        available_teams = cls._get_teams_with_capacity(academic_year, academic_program)
        
        # Track assignment results
        result = {
            "academic_year": academic_year,
            "academic_program": academic_program,
            "available_teams": len(available_teams),
            "teamless_students": len(teamless_students),
            "assigned_count": 0,
            "unassigned_count": 0,
            "team_assignments": {}
        }
        
        if not teamless_students:
            logger.info(f"No teamless students found for year {academic_year}, program {academic_program}")
            return result
            
        if not available_teams:
            logger.warning(f"No teams with capacity found for year {academic_year}, program {academic_program}")
            result["unassigned_count"] = len(teamless_students)
            return result
        
        # Shuffle students for randomization
        random.shuffle(teamless_students)
        
        # Track remaining capacity for each team
        team_capacities = {team.id: team.maximum_members - team.current_member_count for team in available_teams}
        team_names = {team.id: team.name for team in available_teams}
        
        # Assign students to teams
        for student in teamless_students:
            # Get teams that still have capacity
            teams_with_space = [team_id for team_id, capacity in team_capacities.items() if capacity > 0]
            
            if not teams_with_space:
                # No more teams with space
                result["unassigned_count"] += 1
                continue
                
            # Randomly select a team
            chosen_team_id = random.choice(teams_with_space)
            
            # Create the membership
            try:
                TeamMembership.objects.create(
                    user=student.user,
                    team_id=chosen_team_id,
                    role=TeamMembership.ROLE_MEMBER
                )
                
                # Update capacity tracking
                team_capacities[chosen_team_id] -= 1
                result["assigned_count"] += 1
                
                # Track assignments for reporting
                team_name = team_names[chosen_team_id]
                if team_name not in result["team_assignments"]:
                    result["team_assignments"][team_name] = 0
                result["team_assignments"][team_name] += 1
                
                logger.debug(f"Assigned student {student.user.username} to team {team_name}")
                
            except Exception as e:
                logger.error(f"Failed to assign student {student.user.username}: {str(e)}")
                result["unassigned_count"] += 1
        
        return result
    
    @staticmethod
    def _get_teamless_students(academic_year, academic_program):
        """
        Get active students for the given year and program who don't have a team.
        
        Returns:
            list: Student objects without teams
        """
        # Get students in this year/program who are active
        all_students = Student.objects.filter(
            current_year=academic_year,
            academic_program=academic_program,
            academic_status='active'
        ).select_related('user')
        
        # Find students who are not in any team for this year/program
        students_with_teams = Student.objects.filter(
            current_year=academic_year,
            academic_program=academic_program,
            user__teams__academic_year=academic_year,
            user__teams__academic_program=academic_program
        ).values_list('user_id', flat=True).distinct()
        
        # Filter out students who already have teams
        teamless_students = [s for s in all_students if s.user_id not in students_with_teams]
        
        return teamless_students
    
    @staticmethod
    def _get_teams_with_capacity(academic_year, academic_program):
        """
        Get teams for the given year and program that have capacity for more members.
        
        Returns:
            list: Team objects with available capacity
        """
        # Get teams for this year/program
        teams = Team.objects.filter(
            academic_year=academic_year,
            academic_program=academic_program
        ).annotate(
            member_count=Count('members')
        ).filter(
            member_count__lt=F('maximum_members')
        )
        
        return list(teams)