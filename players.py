class Player():
    """Player wrapper."""

    def __init__(self, sid, hit_id, assignment_id, worker_id, ip):
        self.sid = sid
        self.ip = ip
        self.assignment_id = assignment_id
        self.hit_id = hit_id
        self.worker_id = worker_id
        self.partner = None
        self.dialogue_id = None
        self.oracle_sid = None
        self.questioner_sid = None
        self.role = "None"
        self.namespace = "None"

    def is_oracle(self):
        return self.role.find("Oracle") > -1

    def is_questioner(self):
        return self.role.find("Questioner") > -1

    def is_qualified(self):
        return not self.namespace.startswith("/q_")


class QualifyOracle(Player):
    """Oracle that needs to qualify."""

    def __init__(self, sid, hit_id, assignment_id, worker_id, ip):
        Player.__init__(self, sid, hit_id, assignment_id, worker_id, ip)
        self.namespace = '/q_oracle'
        self.role = 'QualifyOracle'


class Oracle(Player):
    """Oracle."""

    def __init__(self, sid, hit_id, assignment_id, worker_id, ip):
        Player.__init__(self, sid, hit_id, assignment_id, worker_id, ip)
        self.namespace = '/oracle'
        self.role = 'Oracle'


class QualifyQuestioner(Player):
    """Questioner that needs to qualify."""


    def __init__(self, sid, hit_id, assignment_id, worker_id, ip):
        Player.__init__(self, sid, hit_id, assignment_id, worker_id, ip)
        self.namespace = '/q_questioner'
        self.role = 'QualifyQuestioner'

class Questioner(Player):
    """Questioner. """


    def __init__(self, sid, hit_id, assignment_id, worker_id, ip):
        Player.__init__(self, sid, hit_id, assignment_id, worker_id, ip)
        self.namespace = '/questioner'
        self.role = 'Questioner'