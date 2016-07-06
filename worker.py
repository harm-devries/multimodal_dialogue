from database.db_utils import get_recent_worker_stats
from sqlalchemy.sql import text
from psiturk.amt_services import MTurkServices
from boto.mturk.connection import MTurkConnection


def check_qualified(conn, player):
    if player.role == 'QualifyOracle':
        stats = get_recent_worker_stats(conn, player.worker_id,
                                        limit=100, questioner=False)
        if stats['success'] >= 10 and (stats['failure'] + stats['oracle_disconnect']) <= 3:
            conn.execute(text('UPDATE worker SET oracle_status = :status, '
                              'o_ass_id = :ass_id WHERE id = :worker_id'),
                         status='qualified', worker_id=player.worker_id,
                         ass_id=player.assignment_id)
            return stats, True
    else:
        stats = get_recent_worker_stats(conn, player.worker_id,
                                        limit=100, questioner=True)

        if stats['success'] >= 10 and (stats['failure'] + stats['questioner_disconnect']) <= 3:
            conn.execute(text('UPDATE worker SET questioner_status = :status, '
                              'q_ass_id = :ass_id WHERE id = :worker_id'),
                         status='qualified', worker_id=player.worker_id,
                         ass_id=player.assignment_id)
            return (stats, True)
    return (stats, False)


def check_blocked(conn, player):
    if player.role == 'QualifyOracle':
        stats = get_recent_worker_stats(conn, player.worker_id,
                                        limit=100, questioner=False)
        if (stats['failure'] + stats['oracle_disconnect']) > 3:
            conn.execute(text('UPDATE worker SET oracle_status = :status WHERE '
                              'id = :worker_id'),
                         status='blocked', worker_id=player.worker_id)
            return stats, True
    elif player.role == 'QualifyQuestioner':
        stats = get_recent_worker_stats(conn, player.worker_id,
                                        limit=100, questioner=True)
        if (stats['failure'] + stats['questioner_disconnect']) > 3:
            conn.execute(text('UPDATE worker SET questioner_status = :status WHERE '
                              'id = :worker_id'),
                         status='blocked', worker_id=player.worker_id)
            return stats, True
    return stats, False

def pay_oracle(conn, player, reward):
    res = conn.execute(text("SELECT dialogue_id FROM dialogue WHERE oracle_paid = :oracle_paid "
                            "AND status = :status AND oracle_session_id IN "
                            "(SELECT id FROM session WHERE worker_id = :worker_id)"),
                       oracle_paid=False, status='success', worker_id=player.worker_id)
    if res.rowcount > 0:
        dialogue_id = res.first()[0]
        r = conn.execute(text("SELECT o_ass_id, o_approved FROM worker WHERE id = :worker_id"),
                         worker_id=player.worker_id)

        if r.rowcount > 0:
            ass_id = r.first()[0]
            o_approved = r.first()[1]

            sandbox = True
            amt_services = MTurkServices('AKIAJO3RIMIRNSW3NZAA',
                                         'SGweeGX+EMF7sUWGiJEwRt2gIytVuXY1iOBjOMa3',
                                         sandbox)
            amt_services.connect_to_turk()

            if not o_approved:
                try:
                    amt_services.mtc.approve_assignment(ass_id)
                    conn.execute(text('UPDATE worker SET o_approved = :o_approved WHERE id = :worker_id'),
                                 o_approved=True, worker_id=player.worker_id)
                except Exception as e:
                    print e
                    return False

            bonus = MTurkConnection.get_price_as_price(reward)
            amt_services.mtc.grant_bonus(player.worker_id, ass_id,
                                         bonus, "dialogue_id:" + str(dialogue_id))
            conn.execute(text("UPDATE dialogue SET oracle_paid = :oracle_paid "
                              "WHERE dialogue_id = :id"),
                         oracle_paid=True, id=dialogue_id)
            return True
    return False

def pay_questioner(conn, player, reward):
    res = conn.execute(text("SELECT dialogue_id FROM dialogue WHERE "
                            "questioner_paid = :questioner_paid "
                            "AND status = :status AND"
                            " questioner_session_id IN "
                            "(SELECT id FROM session WHERE worker_id = :worker_id)"),
                       questioner_paid=False, status='success', worker_id=player.worker_id)
    if res.rowcount > 0:
        dialogue_id = res.first()[0]
        r = conn.execute(text("SELECT q_ass_id, q_approved FROM worker WHERE id = :worker_id"),
                         worker_id=player.worker_id)

        if r.rowcount > 0:
            ass_id = r.first()[0]
            o_approved = r.first()[1]

            sandbox = True
            amt_services = MTurkServices('AKIAJO3RIMIRNSW3NZAA',
                                         'SGweeGX+EMF7sUWGiJEwRt2gIytVuXY1iOBjOMa3',
                                         sandbox)
            amt_services.connect_to_turk()

            if not o_approved:
                try:
                    amt_services.mtc.approve_assignment(ass_id)
                    conn.execute(text('UPDATE worker SET q_approved = :q_approved WHERE id = :worker_id'),
                                 q_approved=True, worker_id=player.worker_id)
                except Exception as e:
                    print e
                    return False

            bonus = MTurkConnection.get_price_as_price(reward)
            amt_services.mtc.grant_bonus(player.worker_id, ass_id,
                                         bonus, "dialogue_id:" + str(dialogue_id))
            conn.execute(text("UPDATE dialogue SET questioner_paid = :questioner_paid "
                              "WHERE dialogue_id = :id"),
                         questioner_paid=True, id=dialogue_id)
            return True
    return False


def get_oracle_reward(conn, worker_id):
    stats = get_recent_worker_stats(conn, worker_id,
                                    limit=10, questioner=False)
    success = stats['success']
    if success == 10:
        return 0.05
    if success == 9:
        return 0.04
    if success in [6, 7, 8]:
        return 0.03
    return 0.0

def get_questioner_reward(conn, worker_id):
    stats = get_recent_worker_stats(conn, worker_id,
                                    limit=10, questioner=True)
    success = stats['success']
    if success == 10:
        return 0.07
    if success == 9:
        return 0.06
    if success in [6, 7, 8]:
        return 0.04
    return 0.0