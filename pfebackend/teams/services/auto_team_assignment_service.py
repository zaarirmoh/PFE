from django.db import transaction
from django.db.models import Count, Q, F
import random
import logging
from users.models import Student
from teams.models import Team, TeamMembership

logger = logging.getLogger(__name__)

class AutoTeamAssignmentService:
    """
    Service for automatically reassigning students to teams based on min/max team size requirements.
    This service will:
    1. Delete teams below minimum size (making those students teamless)
    2. Find all teamless students for a given year
    3. Create new teams with random sizes between min and max
    """
    
    @classmethod
    @transaction.atomic
    def reassign_students_for_year(cls, academic_year, min_members, max_members):
        """
        Main entry point to reassign students for a specific academic year based on team size requirements.
        
        Args:
            academic_year (str): The academic year code ('2', '3', '4siw', etc.)
            min_members (int): Minimum number of members required per team
            max_members (int): Maximum number of members allowed per team
            
        Returns:
            dict: Statistics about the reassignments made
        """
        try:
            if min_members <= 0 or max_members <= 0 or min_members > max_members:
                return {"error": "Invalid min/max values. Min must be positive and less than or equal to max."}
            
            logger.info(f"Starting team reassignment for year '{academic_year}' with min={min_members}, max={max_members}")
            
            stats = {
                "academic_year": academic_year,
                "min_members": min_members,
                "max_members": max_members,
                "teams_deleted": 0,
                "teams_created": 0,
                "students_reassigned": 0,
                "students_remaining": 0,
                "team_distribution": {}
            }
            
            # Step 1: Delete teams with fewer members than the minimum
            deleted_teams = cls._delete_undersized_teams(academic_year, min_members)
            stats["teams_deleted"] = deleted_teams["count"]
            stats["students_freed"] = deleted_teams["students_freed"]
            
            # Step 2: Get all teamless students for this year
            teamless_students = cls._get_teamless_students(academic_year)
            
            # Step 3: Create new teams with random sizes and assign students
            if teamless_students:
                result = cls._create_teams_and_assign_students(teamless_students, academic_year, min_members, max_members)
                stats.update(result)
            
            logger.info(f"Team reassignment completed: {stats['students_reassigned']} students reassigned to {stats['teams_created']} teams")
            return stats
            
        except Exception as e:
            logger.exception(f"Error during team reassignment: {str(e)}")
            return {"error": str(e)}
    
    @classmethod
    def _delete_undersized_teams(cls, academic_year, min_members):
        """
        Delete teams that have fewer members than the minimum required.
        
        Args:
            academic_year (str): The academic year code
            min_members (int): Minimum number of members required
            
        Returns:
            dict: Statistics about the deletion
        """
        # Find teams below minimum size
        undersized_teams = Team.objects.filter(
            academic_year=academic_year
        ).annotate(
            member_count=Count('members')
        ).filter(
            member_count__lt=min_members
        )
        
        deleted_count = 0
        students_freed = 0
        
        for team in undersized_teams:
            # Count members before deletion for statistics
            member_count = team.members.count()
            students_freed += member_count
            
            # Delete team memberships (will free the students)
            TeamMembership.objects.filter(team=team).delete()
            
            # Delete the team
            team.delete()
            deleted_count += 1
            
            logger.debug(f"Deleted undersized team '{team.name}' with {member_count} members")
        
        logger.info(f"Deleted {deleted_count} undersized teams, freeing {students_freed} students")
        
        return {
            "count": deleted_count,
            "students_freed": students_freed
        }
    
    @staticmethod
    def _get_teamless_students(academic_year):
        """
        Get active students for the given year who don't have a team.
        
        Args:
            academic_year (str): The academic year code
            
        Returns:
            list: Student objects without teams
        """
        # Get students in this year who are active
        all_students = Student.objects.filter(
            current_year=academic_year,
            academic_status='active'
        ).select_related('user')
        
        # Find students who are in any team for this year
        students_with_teams = Student.objects.filter(
            current_year=academic_year,
            user__teams__academic_year=academic_year
        ).values_list('id', flat=True).distinct()
        
        # Filter out students who already have teams
        teamless_students = [s for s in all_students if s.id not in students_with_teams]
        
        logger.info(f"Found {len(teamless_students)} teamless students for year {academic_year}")
        
        return teamless_students
    
    @classmethod
    def _create_teams_and_assign_students(cls, students, academic_year, min_members, max_members):
        """
        Create new teams with random sizes between min and max, and assign students to them.
        
        Args:
            students (list): List of Student objects to assign
            academic_year (str): The academic year code
            min_members (int): Minimum number of members per team
            max_members (int): Maximum number of members per team
            
        Returns:
            dict: Statistics about the assignments made
        """
        if not students:
            return {
                "teams_created": 0,
                "students_reassigned": 0,
                "students_remaining": 0,
                "team_distribution": {}
            }
        
        # Shuffle students for randomization
        random.shuffle(students)
        
        teams_created = 0
        students_reassigned = 0
        team_distribution = {}
        
        # Keep track of remaining students
        remaining_students = students.copy()
        
        # Create teams until we run out of students or can't form a minimum-sized team
        while len(remaining_students) >= min_members:
            # Randomly decide team size between min and max
            # But don't exceed available students
            team_size = min(random.randint(min_members, max_members), len(remaining_students))
            
            # Create team
            team_name = f"Auto-Team-{academic_year}-{teams_created + 1}"
            team = Team(
                name=team_name,
                description=f"Automatically created team for {academic_year} academic year",
                academic_year=academic_year,
                maximum_members=max_members,
                # You might need to set created_by and updated_by if these are required
                # Use a system user or get it from elsewhere
            )
            team.save()
            
            # Take team_size students from remaining_students
            team_members = remaining_students[:team_size]
            remaining_students = remaining_students[team_size:]
            
            # Create memberships for these students
            first_student = True
            for student in team_members:
                role = TeamMembership.ROLE_OWNER if first_student else TeamMembership.ROLE_MEMBER
                TeamMembership.objects.create(
                    user=student.user,
                    team=team,
                    role=role
                )
                first_student = False
            
            # Update statistics
            teams_created += 1
            students_reassigned += team_size
            
            # Track team size distribution
            if team_size not in team_distribution:
                team_distribution[team_size] = 0
            team_distribution[team_size] += 1
            
            logger.debug(f"Created team '{team_name}' with {team_size} members")
        
        # Return statistics
        return {
            "teams_created": teams_created,
            "students_reassigned": students_reassigned, 
            "students_remaining": len(remaining_students),
            "team_distribution": team_distribution
        }