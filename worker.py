import requests
from psiturk.amt_services import MTurkServices
from database.db_utils import get_recent_worker_stats
from sqlalchemy.sql import text

def check_qualification(conn, player):
    if player.role == 'QualifyOracle':
        stats = get_recent_worker_stats(conn, player.worker_id,
                                        limit=100, questioner=False)
        if stats['success'] == 10 and stats['failure'] <= 3 and stats['oracle_disconnect'] <= 3:
            approve_hit(player.assignment_id)
            conn.execute(text('UPDATE worker SET oracle_status = :status WHERE '
                              'worker_id = :worker_id'),
                         status='qualified', worker_id=player.worker_id)
            return stats, True
    else:
        stats = get_recent_worker_stats(conn, player.worker_id,
                                        limit=100, questioner=True)
        if stats['success'] == 10 and stats['failure'] <= 3 and stats['questioner_disconnect'] <= 3:
            approve_hit(player.assignment_id)
            conn.execute(text('UPDATE worker SET questioner_status = :status WHERE '
                              'worker_id = :worker_id'),
                         status='qualified', worker_id=player.worker_id)
        return stats, True
    return stats, False

def update_worker_status(conn, player):
    if player.role == 'QualifyOracle':
        stats = get_recent_worker_stats(conn, player.worker_id,
                                        limit=100, questioner=False)
        if stats['failure'] > 3 or stats['oracle_disconnect'] > 3:
            conn.execute(text('UPDATE worker SET oracle_status = :status WHERE '
                              'id = :worker_id'),
                         status='blocked', worker_id=player.worker_id)
            return stats, True
    elif player.role == 'QualifyQuestioner':
        stats = get_recent_worker_stats(conn, player.worker_id,
                                        limit=100, questioner=True)
        if stats['failure'] > 3 or stats['questioner_disconnect'] > 3:
            conn.execute(text('UPDATE worker SET questioner_status = :status WHERE '
                              'id = :worker_id'),
                         status='blocked', worker_id=player.worker_id)
            return stats, True
    return stats, False

def approve_hit(assignment_id):
    requests.post('https://workersandbox.mturk.com/mturk/externalSubmit',
                  data={'assignmentId': assignment_id})
    amt_services = MTurkServices('AKIAJO3RIMIRNSW3NZAA',
                                 'SGweeGX+EMF7sUWGiJEwRt2gIytVuXY1iOBjOMa3',
                                 True)
    amt_services.approve_worker(assignment_id)
