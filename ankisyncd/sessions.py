import logging
import os
from sqlite3 import dbapi2 as sqlite

logger = logging.getLogger("ankisyncd.sessions")


def get_session_manager(config):
    if "session_db_path" in config and config["session_db_path"]:
        logger.info("Found session_db_path in config, using SqliteSessionManager for auth")
        return SqliteSessionManager(config['session_db_path'])
    # elif "session_manager" in config and config["session_manager"]:  # load from config
    #     logger.info("Found session_manager in config, using {} for persisting sessions".format(
    #         config['session_manager'])
    #     )
    #     import importlib
    #     import inspect
    #     module_name, class_name = config['session_manager'].rsplit('.', 1)
    #     module = importlib.import_module(module_name.strip())
    #     class_ = getattr(module, class_name.strip())
    #
    #     if not SimpleSessionManager in inspect.getmro(class_):
    #         raise TypeError('''"session_manager" found in the conf file but it doesn''t
    #                         inherit from SimpleSessionManager''')
    #     return class_(config)
    else:
        raise Exception("Neither session_db_path nor session_manager set")


class SimpleSessionManager:

    def __init__(self):
        self.sessions = {}

    def load(self, hkey):
        return self.sessions.get(hkey)

    def save(self, hkey, session):
        self.sessions[hkey] = session


class SqliteSessionManager(SimpleSessionManager):

    def __init__(self, session_db_path):
        SimpleSessionManager.__init__(self)

        self.session_db_path = os.path.realpath(session_db_path)
        # self._ensure_schema_up_to_date()

    def load(self, hkey, session_factory=None):
        session = SimpleSessionManager.load(self, hkey)
        if session is not None:
            return session

        conn = self._conn()
        cursor = conn.cursor()

        cursor.execute(self.fs("SELECT skey, username, path FROM session WHERE hkey=?"), (hkey,))
        res = cursor.fetchone()

        if res is not None:
            session = self.sessions[hkey] = session_factory(res[1], res[2])
            session.skey = res[0]
            return session

    # Default to using sqlite3 syntax but overridable for sub-classes using other
    # DB API 2 driver variants
    @staticmethod
    def fs(sql):
        return sql

    def _conn(self):
        new = not os.path.exists(self.session_db_path)
        conn = sqlite.connect(self.session_db_path)
        if new:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE session (hkey VARCHAR PRIMARY KEY, skey VARCHAR, username VARCHAR, path VARCHAR)")
        return conn

    def save(self, hkey, session):
        SimpleSessionManager.save(self, hkey, session)

        conn = self._conn()
        cursor = conn.cursor()

        cursor.execute("INSERT OR REPLACE INTO session (hkey, skey, username, path) VALUES (?, ?, ?, ?)",
               (hkey, session.skey, session.name, session.path))

        conn.commit()