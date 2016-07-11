class Player():
    """Player wrapper."""

    def __init__(self, sid, hit_id, assignment_id, worker_id, ip):
        self.sid = sid
        self.ip = ip
        self.assignment_id = assignment_id
        self.hit_id = hit_id
        self.worker_id = worker_id
        self.partner = None
        self.dialogue = None


class QualifyOracle(Player):
    """Oracle that needs to qualify."""
    namespace = '/q_oracle'
    role = 'QualifyOracle'

    def __init__(self, sid, hit_id, assignment_id, worker_id, ip):
        Player.__init__(self, sid, hit_id, assignment_id, worker_id, ip)


class Oracle(Player):
    """Oracle."""
    namespace = '/oracle'
    role = 'Oracle'

    def __init__(self, sid, hit_id, assignment_id, worker_id, ip):
        Player.__init__(self, sid, hit_id, assignment_id, worker_id, ip)


class QualifyQuestioner(Player):
    """Questioner that needs to qualify."""
    namespace = '/q_questioner'
    role = 'QualifyQuestioner'

    def __init__(self, sid, hit_id, assignment_id, worker_id, ip):
        Player.__init__(self, sid, hit_id, assignment_id, worker_id, ip)


class Questioner(Player):
    """Questioner. """
    namespace = '/questioner'
    role = 'Questioner'

    def __init__(self, sid, hit_id, assignment_id, worker_id, ip):
        Player.__init__(self, sid, hit_id, assignment_id, worker_id, ip)
