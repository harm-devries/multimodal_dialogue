from database.db_utils import get_recent_worker_stats
from sqlalchemy.sql import text


def check_qualified(conn, player):
    if player.role == 'QualifyOracle':
        stats = get_recent_worker_stats(conn, player.worker_id,
                                        limit=100, questioner=False)
        if stats['success'] > 10 and stats['failure'] <= 3 and stats['oracle_disconnect'] <= 3:
            conn.execute(text('UPDATE worker SET questioner_status = :status, '
                              'o_ass_id = :ass_id WHERE id = :worker_id'),
                         status='qualified', worker_id=player.worker_id,
                         ass_id=player.assignment_id)
            return stats, True
    else:
        stats = get_recent_worker_stats(conn, player.worker_id,
                                        limit=100, questioner=True)
        if stats['success'] > 10 and stats['failure'] <= 3 and stats['questioner_disconnect'] <= 3:
            conn.execute(text('UPDATE worker SET questioner_status = :status, '
                              'q_ass_id = :ass_id WHERE id = :worker_id'),
                         status='qualified', worker_id=player.worker_id,
                         ass_id=player.assignment_id)
        return stats, True
    return stats, False


def check_blocked(conn, player):
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
