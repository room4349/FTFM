from models.response import ResponseStatusCode, Detail
from typing import Dict, Any, List, TypeVar, Tuple
from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.exc import IntegrityError
from database.conn import DBObject
from models.base import Base
import requests
import json
import traceback
import logging

TeamListType = TypeVar("TeamListType", bound="TeamList")

class TeamList(Base):
    __tablename__ = "TeamList"

    team_id = Column(Integer, primary_key=True)
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
        short_name=None,
        tla=None,
        crest=None,
        address=None,
        website=None,
        founded=None,
        club_colors=None,
        venue=None
    ):
        self.team_id = team_id
        self.team_name = team_name
        self.short_name = short_name
        self.tla = tla
        self.crest = crest
        self.address = address
        self.website = website
        self.founded = founded
        self.club_colors = club_colors
        self.venue = venue

    @property
    def info(self):
        return {
            "team_id": self.team_id,
            "team_name": self.team_name,
            "short_name": self.short_name,
            "tla": self.tla,
            "crest": self.crest,
            "address": self.address,
            "website": self.website,
            "founded": self.founded,
            "club_colors": self.club_colors,
            "venue": self.venue
        }

    @staticmethod
    def _check_data_exist(dbo: DBObject) -> Tuple[ResponseStatusCode, None | str]:
        try:
            if not dbo.session.query(TeamList).all():
                return ResponseStatusCode.SUCCESS, None
            else:
                return ResponseStatusCode.CONFLICT, Detail("Data already exists in TeamList.")
        except Exception as e:
            logging.error(f"Error checking data existence: {e}")
            return ResponseStatusCode.INTERNAL_SERVER_ERROR, str(e)

    @staticmethod
    def _crawl_team_info(URL: str, API_KEY: str) -> Tuple[ResponseStatusCode, List[Dict[str, Any]] | str]:
        try:
            params = {'limit': 5000}
            headers = {'Authorization': f'Bearer {API_KEY}'}

            response = requests.get(URL, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                teams = [
                    {
                        "team_id": x["team_id"],
                        "team_name": x["team_name"],
                        "short_name": x["short_name"],
                        "tla": x["tla"],
                        "crest": x["crest"],
                        "address": x["address"],
                        "website": x["website"],
                        "founded": x["founded"],
                        "club_colors": x["club_colors"],
                        "venue": x["venue"]
                    }
                    for x in data["dataSearch"]["content"]
                ]
                return ResponseStatusCode.SUCCESS, teams
            else:
                return ResponseStatusCode.FAIL, Detail("URL not responded in TeamList._crawl_team_info")

        except requests.exceptions.ConnectionError:
            return ResponseStatusCode.NOT_FOUND, Detail("URL not found in TeamList._crawl_team_info")

        except Exception as e:
            logging.error(f"Error crawling team info: {e}")
            return ResponseStatusCode.INTERNAL_SERVER_ERROR, str(e)

    @staticmethod
    def _insert_team_info(dbo: DBObject, team_info: List[Dict[str, Any]]) -> Tuple[ResponseStatusCode, str | None]:
        try:
            for t in team_info:
                team = TeamList(
                    team_id=t["team_id"],
                    team_name=t["team_name"],
                    short_name=t["short_name"],
                    tla=t["tla"],
                    crest=t["crest"],
                    address=t["address"],
                    website=t["website"],
                    founded=t["founded"],
                    club_colors=t["club_colors"],
                    venue=t["venue"]
                )
                dbo.session.add(team)

            dbo.session.commit()
            return ResponseStatusCode.SUCCESS, None

        except IntegrityError:
            dbo.session.rollback()
            return ResponseStatusCode.CONFLICT, Detail("Data already exists in TeamList._insert_team_info")

        except Exception as e:
            logging.error(f"Error inserting team info: {e}")
            dbo.session.rollback()
            return ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e))

    @staticmethod
    def _init_team_list(dbo: DBObject, URL: str, API_KEY: str) -> Tuple[ResponseStatusCode, str | None]:
        try:
            result, data = TeamList._check_data_exist(dbo)
            if result != ResponseStatusCode.SUCCESS:
                return result, data

            result, data = TeamList._crawl_team_info(URL, API_KEY)
            if result != ResponseStatusCode.SUCCESS:
                return result, data

            result, detail = TeamList._insert_team_info(dbo, data)
            if isinstance(detail, Detail):
                raise Exception(detail.message)

            return ResponseStatusCode.SUCCESS, None

        except Exception as e:
            logging.error(f"Error initializing team list: {e}")
            return ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e))
