from django.conf import settings
from django.db import connection
import os

def is_reserved(word, conn):
  """Determine if word is in Postgres's list of reserved keywords"""
  c = conn.cursor()
  c.execute('select catcode from pg_get_keywords() WHERE word=%s;', [word])
  row = c.fetchone()
  if row is None: return False
  if row[0] == 'R': return True
  return False
  
def insert_migration_data(appname):
  return lambda apps, schema_editor: _insert_migration_data(apps, schema_editor, appname)

def _insert_migration_data(apps, schema_editor, appname):
  path = os.path.abspath(os.path.join(str(settings.APPS_DIR), "../migration_data/" + appname + "/"))
  if os.path.isdir(path):
    for fname in filter(lambda x: x.endswith(".csv"), os.listdir(path)):
      fpath = os.path.join(path, fname)
      f = open(fpath, 'r')
      columns = []
      for x in f.readline().rstrip().split(','):
        if is_reserved(x, connection): columns.append('"' + x + '"')
        else: columns.append(x)
  
      table = fname[:fname.index('.')]
      with connection.cursor() as cur:
        cur.copy_expert("COPY " + table + "(" + ",".join(columns) + ") FROM STDIN WITH CSV HEADER", open(fpath, 'r'));
  
      with connection.cursor() as cur:
        cur.execute("SELECT setval(pg_get_serial_sequence('" + table + "', 'id'), coalesce(max(id),0) + 1, false) FROM " + table + ";")
  
      f.close()
