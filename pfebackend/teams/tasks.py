from celery import shared_task
import time
import logging
from .services.auto_team_assignment_service import AutoTeamAssignmentService

logger = logging.getLogger(__name__)

@shared_task
def reassign_students_task(academic_year, min_members, max_members):
    """
    Celery task to automatically reassign students to teams
    based on minimum and maximum team size requirements.
    
    Args:
        academic_year (str): The academic year code ('2', '3', '4siw', etc.)
        min_members (int): Minimum number of members required per team
        max_members (int): Maximum number of members allowed per team
        
    Returns:
        dict: Statistics about the reassignments made
    """
    logger.info(f"Starting scheduled auto team assignment task for {academic_year} with min={min_members}, max={max_members}")
    
    try:
        result = AutoTeamAssignmentService.reassign_students_for_year(
            academic_year, min_members, max_members
        )
        
        if "error" in result:
            logger.error(f"Error in auto team assignment: {result['error']}")
            return {"status": "error", "error": result["error"]}
            
        logger.info(f"Auto team assignment completed: {result['students_reassigned']} students reassigned to {result['teams_created']} teams")
        return {
            "status": "success", 
            "academic_year": academic_year,
            "results": result
        }
        
    except Exception as e:
        logger.exception(f"Exception in auto team assignment task: {str(e)}")
        return {"status": "error", "error": str(e)}

