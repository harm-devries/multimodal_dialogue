"""Helper functions to connect to postgres database."""
import psycopg2
import urlparse


def db_connect(database, username, password, hostname, port):
    """Connect to postgresql database."""
    try:
        conn = psycopg2.connect(database=database,
                                user=username,
                                password=password,
                                host=hostname,
                                port=port)
        return conn
    except Exception as e:
        print "Unable to connect to database:"
        print e.msg


def parse_postgresurl(db_url):
    """Parse postgresql url.

    Returns database, username, password,
    hostname and port.
    """
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(db_url)
    return url.path[1:], url.username, url.password, url.hostname, url.port
