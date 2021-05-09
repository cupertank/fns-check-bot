from typing import Optional

from pypika import PostgreSQLQuery, Table


class Dao:
    """
    Provides interface for interacting with the database
    """

    def __init__(self, db):
        self.__localDict = {}
        self.__isLocal = db is None  # for non-heroku builds
        if self.__isLocal:
            return

        self.db = db
        self.cursor = db.cursor()
        self.users = Table("users")

    def set_refresh_token(self, uid: int, refresh_token: str) -> None:
        if self.__isLocal:
            if uid not in self.__localDict:
                self.__localDict[uid] = [None, None]
            self.__localDict[uid][0] = refresh_token
            return

        sql = PostgreSQLQuery.into(self.users).insert(uid, refresh_token, None) \
            .on_conflict(self.users.uid).do_update(self.users.refresh_token, refresh_token)
        self.cursor.execute(str(sql))
        self.db.commit()

    def get_refresh_token(self, uid: int) -> Optional[str]:
        if self.__isLocal:
            if uid in self.__localDict:
                return self.__localDict[uid][0]
            else:
                return None

        sql = PostgreSQLQuery.from_(self.users).select("refresh_token").where(self.users.uid == uid)
        self.cursor.execute(str(sql))
        res = self.cursor.fetchone()
        if res is None:
            return None
        return res[0]

    def set_session_id(self, uid: int, session_id: str) -> None:
        if self.__isLocal:
            if "uid" not in self.__localDict:
                self.__localDict[uid] = [None, None]
            self.__localDict[uid][1] = session_id
            return

        sql = PostgreSQLQuery.into(self.users).insert(uid, None, session_id) \
            .on_conflict(self.users.uid).do_update(self.users.session_id, session_id)
        self.cursor.execute(str(sql))
        self.db.commit()

    def get_session_id(self, uid: int) -> Optional[str]:
        if self.__isLocal:
            if uid in self.__localDict:
                return self.__localDict[uid][1]
            else:
                return None

        sql = PostgreSQLQuery.from_(self.users).select("session_id").where(self.users.uid == uid)
        self.cursor.execute(str(sql))
        res = self.cursor.fetchone()
        if res is None:
            return None
        return res[0]
