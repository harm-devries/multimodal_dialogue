class Player():
    """Player wrapper."""

    def __init__(self, sid):
        self.sid = sid
        self.partner_sid = None


class Oracle(Player):
    """Oracle."""
    namespace = '/oracle'

    def __init__(self, sid):
        Player.__init__(self, sid)


class Questioner1(Player):
    """Questioner of level1."""
    namespace = '/questioner1'

    def __init__(self, sid):
        Player.__init__(self, sid)


class Questioner2(Player):
    """Questioner of level2. """
    namespace = '/questioner2'

    def __init__(self, sid):
        Player.__init__(self, sid)
