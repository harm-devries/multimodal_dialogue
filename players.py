class Player():
    """Player wrapper."""

    def __init__(self, sid, assignment_id, hit_id, worker_id, ip):
        self.sid = sid
        self.assignment_id = assignment_id
        self.hit_id = hit_id
        self.worker_id = worker_id
        self.ip = ip
        self.partner = None
        self.dialogue = None


class Oracle(Player):
    """Oracle."""
    namespace = '/oracle'
    role = 'Oracle'

    def __init__(self, sid, assignment_id, hit_id, worker_id, ip):
        Player.__init__(self, sid, assignment_id, hit_id, worker_id, ip)


class Questioner1(Player):
    """Questioner of level1."""
    namespace = '/questioner1'
    role = 'Questioner1'

    def __init__(self, sid, assignment_id, hit_id, worker_id, ip):
        Player.__init__(self, sid, assignment_id, hit_id, worker_id, ip)


class Questioner2(Player):
    """Questioner of level2. """
    namespace = '/questioner2'
    role = 'Questioner2'

    def __init__(self, sid, assignment_id, hit_id, worker_id, ip):
        Player.__init__(self, sid, assignment_id, hit_id, worker_id, ip)
