from pypika import PostgreSQLQuery, Table

from .exceptions import FNSUserDoesNotExistException


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
            self.__localDict[uid] = refresh_token
            return

        sql = PostgreSQLQuery.into(self.users).insert(uid, refresh_token)\
            .on_conflict(self.users.uid).do_update(self.users.refresh_token, refresh_token)
        self.cursor.execute(str(sql))
        self.db.commit()

    def get_refresh_token(self, uid: int) -> str:
        if self.__isLocal:
            if uid in self.__localDict:
                return self.__localDict[uid]
            else:
                raise FNSUserDoesNotExistException(f'{uid} is not present in the database')

        sql = PostgreSQLQuery.from_(self.users).select("refresh_token").where(self.users.uid == uid)
        self.cursor.execute(str(sql))
        res = self.cursor.fetchone()
        if res is None:
            raise FNSUserDoesNotExistException(f'{uid} is not present in the database')
        return res[0]
