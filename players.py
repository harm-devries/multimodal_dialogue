class Player():
    """Player wrapper."""

    def __init__(self, sid, ip):
        self.sid = sid
        self.ip = ip
        self.assignment_id = None
        self.hit_id = None
        self.worker_id = None
        self.partner = None
        self.dialogue = None


class QualifyOracle(Player):
    """Oracle that needs to qualify."""
    namespace = '/q_oracle'
    role = 'QualifyOracle'

    def __init__(self, sid, ip):
        Player.__init__(self, sid, ip)


class Oracle(Player):
    """Oracle."""
    namespace = '/oracle'
    role = 'Oracle'

    def __init__(self, sid, ip):
        Player.__init__(self, sid, ip)


class QualifyQuestioner(Player):
    """Questioner that needs to qualify."""
    namespace = '/q_questioner'
    role = 'QualifyQuestioner'

    def __init__(self, sid, ip):
        Player.__init__(self, sid, ip)


class Questioner(Player):
    """Questioner. """
    namespace = '/questioner'
    role = 'Questioner'

    def __init__(self, sid, ip):
        Player.__init__(self, sid, ip)
