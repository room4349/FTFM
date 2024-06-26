from models.response import ResponseStatusCode, Detail
from typing import Dict, Any, List, TypeVar, Tuple
# from utility.checker import is_valid_uuid_format
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine.row import Row
from database.conn import DBObject
from models.base import Base
from pathlib import Path
from PIL import Image
import requests
import json
import traceback
import requests
import logging
import rembg
import uuid
import os

TeamList = TypeVar("TeamList", bound="TeamList")


class TeamList(Base):
    """
    팀 목록을 저장하는 데이터베이스 테이블을 나타내는 클래스입니다.
    """
   
    __tablename__ = "TeamList"

    team_id = Column(String, primary_key=True)
    team_name = Column(String(100), nullable=False)
    short_name = Column(String(50))
    tla = Column(String(10))
    crest = Column(String(200))
    address = Column(Text)
    website = Column(String(200))
    founded = Column(String)
    club_colors = Column(String(100))
    venue = Column(String(200))



    def __init__(
        self,
        team_id,
        team_name,
        tla=None,
        crest=None,
        address=None,
        website=None,
        club_colors=None,
        venue=None
    ):
        self.team_id = team_id
        self.team_name = team_name
        self.tla = tla
        self.crest = crest
        self.address = address
        self.website = website
        self.club_colors = club_colors
        self.venue=venue

    @property
    def info(self):
        return {
            "team_id": self.team_id,
            "team_name": self.team_name,
            "tla":self.tla,
            "crest":  self.crest,
            "address": self.address,
            "website":  self.website,
            "club_colors":  self.club_colors,
            "venue": self.venue
        }


    @staticmethod
    def _check_data_exist(
        dbo: DBObject
    ) -> Tuple[ResponseStatusCode, None | str]:
        return {
            True: (ResponseStatusCode.SUCCESS, None),
            False: (ResponseStatusCode.CONFLICT,
                    Detail("Data Conflicted in University._check_data_exist"))
        }[dbo.session.query(TeamList).all() == []]

    @staticmethod
    def _crawl_univ_info(
        URL: str,
        API_KEY: str
    ) -> Tuple[ResponseStatusCode, List[Dict[str, Any]] | str]:
        try:
            params = {'limit': 5000}

            response = requests.get(URL,API_KEY,params=params)

            if response.status_code == 200:
                data = response.json()
                return (ResponseStatusCode.SUCCESS,
                        list(map(lambda x: {"team_id": x["id"],
                                            "team_name": x["schoolGubun"],
                                            "short_name": x["adres"],
                                            "tla": x["link"],
                                            "crest": x["estType"],
                                            "address": x["totalCount"],
                                            "website": x["website"],
                                            "founded": x["founded"],
                                            "club_colors": x["club_colors"],
                                            "venue": x["venue"]
                                            },
                                data["dataSearch"]["content"])))

            else:
                return (ResponseStatusCode.FAIL,
                        Detail("""URL Not Responded in \
                            University._crawl_univ_info"""))

        except requests.exceptions.ConnectionError:
            return (ResponseStatusCode.NOT_FOUND,
                    Detail("URL Not Found in University._crawl_univ_info"))

        except Exception as e:
            logging.error(f"""{e}: {''.join(traceback.format_exception(None,
                        e, e.__traceback__))}""")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, str(e))

    @staticmethod
    def _insert_univ_info(
        dbo: DBObject,
        univ_info: List[Dict[str, Any]]
    ) -> Tuple[ResponseStatusCode, str | None]:
        try:
            for u in univ_info:
                univ = TeamList(
                    univ_name=u["univ_name"],
                    est_type=u["est_type"],
                    link=u["link"],
                    address=u["address"],
                    univ_gubun=u["univ_gubun"]
                )
                dbo.session.add(univ)

            return (ResponseStatusCode.SUCCESS, None)

        except IntegrityError:
            return (ResponseStatusCode.CONFLICT,
                    Detail("""Data Already Exist in
                        University._insert_univ_info"""))

        except Exception as e:
            logging.error(f"""{e}: {''.join(traceback.format_exception(None,
                        e, e.__traceback__))}""")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))

        finally:
            dbo.session.commit()

    @staticmethod
    def _init_univ(
        dbo: DBObject,
        URL: str,
        API_KEY: str
    ) -> Tuple[ResponseStatusCode, str | None]:
        try:
            result, data = TeamList._check_data_exist(dbo)
            if result != ResponseStatusCode.SUCCESS:
                return (result, data)

            result, data = TeamList._crawl_univ_info(URL, API_KEY)
            if result != ResponseStatusCode.SUCCESS:
                return (result, data)

            if int(data[0]["total"]) != len(data):
                return (ResponseStatusCode.DATA_REQUIRED,
                        Detail("""Total University Count Not Equals in
                            University._init_univ"""))

            else:
                result, detail = TeamList._insert_univ_info(dbo, data)
                if isinstance(detail, Detail):
                    raise Exception(detail.message)

                return (ResponseStatusCode.SUCCESS, None)

        except Exception as e:
            logging.error(f"""{e}: {''.join(traceback.format_exception(None,
                        e, e.__traceback__))}""")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))