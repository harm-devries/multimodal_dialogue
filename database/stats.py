import os
import psycopg2

conn = psycopg2.connect('postgres://ojhcjubujbtgoz:qUx5vi7yR2j8KvjOsWd8LhN-RE@ec2-54-163-254-197.compute-1.amazonaws.com:5432/dd1rgn94b1f6e9')
cur = conn.cursor()

cur.execute("SELECT count(*) FROM dialogue WHERE status = 'success' AND questioner_session_id IN "
			"(SELECT id FROM session WHERE assignment_id IN "
			"(SELECT assignment_id FROM assignment WHERE completed = TRUE))")
print cur.fetchone()[0]

cur.execute("SELECT count(*) FROM dialogue WHERE mode = 'normal' AND status = 'success' AND questioner_session_id IN "
			"(SELECT id FROM session WHERE assignment_id IN "
			"(SELECT assignment_id FROM assignment WHERE completed = TRUE))")
print cur.fetchone()[0]

cur.execute("SELECT count(*) FROM worker WHERE oracle_status = 'qualified'")
print cur.fetchone()[0]

cur.execute("SELECT count(*) FROM worker WHERE oracle_status = 'blocked'")
print cur.fetchone()[0]

cur.execute("SELECT count(*) FROM worker WHERE questioner_status = 'qualified'")
print cur.fetchone()[0]

cur.execute("SELECT count(*) FROM worker WHERE questioner_status = 'blocked'")
print cur.fetchone()[0]