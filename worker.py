from database.db_utils import get_assignment_stats
from sqlalchemy.sql import text
from psiturk.amt_services import MTurkServices
from boto.mturk.connection import MTurkConnection


def check_qualified(conn, player):
    if player.role == 'QualifyOracle':
        stats = get_assignment_stats(conn, player.assignment_id,
                                     questioner=False)
        if stats['success'] >= 10 and (stats['failure'] + stats['oracle_disconnect'] + stats['oracle_timeout'] + stats['oracle_reported']) <= 3:
            conn.execute(text('UPDATE worker SET oracle_status = :status, '
                              'o_ass_id = :ass_id WHERE id = :worker_id'),
                         status='qualified', worker_id=player.worker_id,
                         ass_id=player.assignment_id)
            conn.execute(text('UPDATE assignment SET completed = :completed '
                              'WHERE assignment_id = :ass_id AND worker_id = :wid'),
                         completed=True, wid=player.worker_id,
                         ass_id=player.assignment_id)
            conn.execute("UPDATE money SET money = money + 0.3")
            return stats, True
    else:
        stats = get_assignment_stats(conn, player.assignment_id,
                                     questioner=True)

        if stats['success'] >= 10 and (stats['failure'] + stats['questioner_disconnect'] + stats['questioner_timeout'] + stats['oracle_reported']) <= 3:
            conn.execute(text('UPDATE worker SET questioner_status = :status, '
                              'q_ass_id = :ass_id WHERE id = :worker_id'),
                         status='qualified', worker_id=player.worker_id,
                         ass_id=player.assignment_id)
            conn.execute(text('UPDATE assignment SET completed = :completed '
                              'WHERE assignment_id = :ass_id AND worker_id = :wid'),
                         completed=True, wid=player.worker_id,
                         ass_id=player.assignment_id)
            conn.execute("UPDATE money SET money = money + 0.48")
            return (stats, True)
    return (stats, False)


def check_blocked(conn, player):
    if player.role == 'QualifyOracle':
        stats = get_assignment_stats(conn, player.assignment_id,
                                     questioner=False)
        if (stats['failure'] + stats['oracle_disconnect'] + stats['oracle_timeout'] + stats['oracle_reported']) > 3:
            conn.execute(text('UPDATE worker SET oracle_status = :status WHERE '
                              'id = :worker_id'),
                         status='blocked', worker_id=player.worker_id)
            return stats, True
    elif player.role == 'QualifyQuestioner':
        stats = get_assignment_stats(conn, player.assignment_id,
                                     questioner=True)
        if (stats['failure'] + stats['questioner_disconnect'] + stats['questioner_timeout'] + stats['oracle_reported']) > 3:
            conn.execute(text('UPDATE worker SET questioner_status = :status WHERE '
                              'id = :worker_id'),
                         status='blocked', worker_id=player.worker_id)
            return stats, True
    else:
        stats = {}
    return stats, False


def check_assignment_completed(conn, player):
    if player.role == 'Oracle':
        stats = get_assignment_stats(conn, player.assignment_id,
                                     questioner=False)
        if stats['success'] >= 10 and (stats['failure'] + stats['oracle_disconnect'] + stats['oracle_timeout'] + stats['oracle_reported']) <= 3:
            conn.execute(text('UPDATE assignment SET completed = :completed '
                              'WHERE assignment_id = :ass_id AND worker_id = :wid'),
                         completed=True, wid=player.worker_id,
                         ass_id=player.assignment_id)
            return stats, True
    else:
        stats = get_assignment_stats(conn, player.assignment_id,
                                     questioner=True)

        if stats['success'] >= 10 and (stats['failure'] + stats['questioner_disconnect'] + stats['questioner_timeout'] + stats['oracle_reported']) <= 3:
            conn.execute(text('UPDATE assignment SET completed = :completed '
                              'WHERE assignment_id = :ass_id AND worker_id = :wid'),
                         completed=True, wid=player.worker_id,
                         ass_id=player.assignment_id)
            return (stats, True)
    return (stats, False)


def pay_oracle_bonus(conn, player):
    r = conn.execute(text("SELECT o_ass_id, o_approved FROM worker WHERE id = :worker_id"),
                     worker_id=player.worker_id)
    if r.rowcount > 0:
        ass_id, o_approved = r.first()

        sandbox = False
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

        reward = get_oracle_reward(conn, player.assignment_id)
        if reward > 0.0:
            bonus = MTurkConnection.get_price_as_price(reward)
            amt_services.mtc.grant_bonus(player.worker_id, ass_id,
                                         bonus, "Bonus for assignment " + str(player.assignment_id))
            conn.execute(text('UPDATE assignment SET bonus = :bonus, bonus_paid = :bonus_paid'
                              ' WHERE assignment_id = :ass_id AND worker_id = :worker_id'),
                         bonus=reward, ass_id=player.assignment_id,
                         bonus_paid=True, worker_id=player.worker_id)


def pay_questioner_bonus(conn, player):
    r = conn.execute(text("SELECT q_ass_id, q_approved FROM worker WHERE id = :worker_id"),
                     worker_id=player.worker_id)
    if r.rowcount > 0:
        ass_id, q_approved = r.first()

        sandbox = False
        amt_services = MTurkServices('AKIAJO3RIMIRNSW3NZAA',
                                     'SGweeGX+EMF7sUWGiJEwRt2gIytVuXY1iOBjOMa3',
                                     sandbox)
        amt_services.connect_to_turk()

        if not q_approved:
            try:
                amt_services.mtc.approve_assignment(ass_id)
                conn.execute(text('UPDATE worker SET q_approved = :q_approved WHERE id = :worker_id'),
                             q_approved=True, worker_id=player.worker_id)
            except Exception as e:
                print e
                return False

        reward = get_questioner_reward(conn, player.assignment_id)
        if reward > 0.0:
            bonus = MTurkConnection.get_price_as_price(reward)
            amt_services.mtc.grant_bonus(player.worker_id, ass_id,
                                         bonus, "Bonus for assignment " + str(player.assignment_id))
            conn.execute(text('UPDATE assignment SET bonus = :bonus, bonus_paid = :bonus_paid'
                              ' WHERE assignment_id = :ass_id AND worker_id = :worker_id'),
                         bonus=reward, ass_id=player.assignment_id,
                         bonus_paid=True, worker_id=player.worker_id)

# def pay_oracle(conn, player, reward):
#     res = conn.execute(text("SELECT dialogue_id FROM dialogue WHERE oracle_paid = :oracle_paid "
#                             " AND mode = :mode AND status = :status AND oracle_session_id IN "
#                             "(SELECT id FROM session WHERE worker_id = :worker_id)"),
#                        oracle_paid=False, status='success',
#                        mode='normal', worker_id=player.worker_id)
#     if res.rowcount > 0:
#         dialogue_id = res.first()[0]
#         r = conn.execute(text("SELECT o_ass_id, o_approved FROM worker WHERE id = :worker_id"),
#                          worker_id=player.worker_id)

#         if r.rowcount > 0:
#             ass_id, o_approved = r.first()

#             sandbox = False
#             amt_services = MTurkServices('AKIAJO3RIMIRNSW3NZAA',
#                                          'SGweeGX+EMF7sUWGiJEwRt2gIytVuXY1iOBjOMa3',
#                                          sandbox)
#             amt_services.connect_to_turk()

#             if not o_approved:
#                 try:
#                     amt_services.mtc.approve_assignment(ass_id)
#                     conn.execute(text('UPDATE worker SET o_approved = :o_approved WHERE id = :worker_id'),
#                                  o_approved=True, worker_id=player.worker_id)
#                 except Exception as e:
#                     print e
#                     return False

#             bonus = MTurkConnection.get_price_as_price(reward)
#             amt_services.mtc.grant_bonus(player.worker_id, ass_id,
#                                          bonus, "Completed dialogue with id " + str(dialogue_id))
#             conn.execute(text("UPDATE dialogue SET oracle_paid = :oracle_paid "
#                               "WHERE dialogue_id = :id"),
#                          oracle_paid=True, id=dialogue_id)
#             conn.execute(text("UPDATE money SET money = money + :money"),
#                          money=reward+max(reward*0.2, 0.01))
#             return True
#     return False

# def pay_questioner(conn, player, reward):
#     res = conn.execute(text("SELECT dialogue_id FROM dialogue WHERE "
#                             "questioner_paid = :questioner_paid AND mode = :mode,"
#                             "AND status = :status AND"
#                             " questioner_session_id IN "
#                             "(SELECT id FROM session WHERE worker_id = :worker_id)"),
#                        questioner_paid=False, status='success',
#                        mode='normal', worker_id=player.worker_id)
#     if res.rowcount > 0:
#         dialogue_id = res.first()[0]
#         r = conn.execute(text("SELECT q_ass_id, q_approved FROM worker WHERE id = :worker_id"),
#                          worker_id=player.worker_id)

#         if r.rowcount > 0:
#             ass_id, q_approved = r.first()

#             sandbox = False
#             amt_services = MTurkServices('AKIAJO3RIMIRNSW3NZAA',
#                                          'SGweeGX+EMF7sUWGiJEwRt2gIytVuXY1iOBjOMa3',
#                                          sandbox)
#             amt_services.connect_to_turk()

#             if not q_approved:
#                 try:
#                     amt_services.mtc.approve_assignment(ass_id)
#                     conn.execute(text('UPDATE worker SET q_approved = :q_approved WHERE id = :worker_id'),
#                                  q_approved=True, worker_id=player.worker_id)
#                 except Exception as e:
#                     print e
#                     return False

#             bonus = MTurkConnection.get_price_as_price(reward)
#             amt_services.mtc.grant_bonus(player.worker_id, ass_id,
#                                          bonus, "Completed dialogue with id " + str(dialogue_id))
#             conn.execute(text("UPDATE dialogue SET questioner_paid = :questioner_paid "
#                               "WHERE dialogue_id = :id"),
#                          questioner_paid=True, id=dialogue_id)
#             conn.execute(text("UPDATE money SET money = money + :money"),
#                          money=reward+max(reward*0.2, 0.01))
#             return True
#     return False


def get_oracle_reward(conn, assignment_id):
    stats = get_assignment_stats(conn, assignment_id,
                                 questioner=False)
    fails = stats['failure']
    if fails == 0:
        return 0.10
    if fails == 1:
        return 0.07
    if fails == 2:
        return 0.04
    return 0.0


def get_questioner_reward(conn, assignment_id):
    stats = get_assignment_stats(conn, assignment_id,
                                 questioner=True)
    fails = stats['failure']
    if fails == 0:
        return 0.15
    if fails == 1:
        return 0.10
    if fails == 2:
        return 0.05
    return 0.0