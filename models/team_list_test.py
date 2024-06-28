from sqlalchemy import Column, TEXT, DateTime, ForeignKeyConstraint, Boolean
from models.response import ResponseStatusCode, Detail
from sqlalchemy import ARRAY, Enum, String
from typing import Tuple, TypeVar, List
from database.conn import DBObject
from datetime import datetime
from models.base import Base
import traceback
import logging

Playerlist = TypeVar("Playerlist", bound="Playerlist")

class Playerlist(Base):
    __tablename__ = "Playerlist"

    player_id: str = Column((String),primary_key=True)  # 게시물 고유 uuid
    player_Country: str =  Column(String) # 선수 모국 1개만 적어.
    player_team: str = Column((String),default=None) # 나중에 너가 API 에서 팀 받아와 지면 넣어
    player_position: str = Column((String),default=None) #선수 포지션 어딘지 너가 수작업 해 ^^
    player_image_urls: List[str] = Column(ARRAY(TEXT), nullable=True)  # 이미지 URL 리스트
    player_image_types: List[str] = Column(ARRAY(String(255)), nullable=True)  # 이미지 타입 리스트

    

    # __table_args__ = (ForeignKeyConstraint(
    #     ["a_uuid"], ["account.a_uuid"],
    #     ondelete="SET NULL", onupdate="CASCADE"
    # ),) 외래키 나중에 쓸 떄 써

    @property
    def info(self):
        return {
            'player_id': str(self.player_id),
            'player_Country': str(self.player_Country),
            'player_team': str(self.player_team),
            'player_position': str(self.player_position),
            'player_image_urls': str(self.player_image_urls),
            'player_image_types': str(self.player_image_types)
        }
    
    def __init__(self, player_id: str, player_Country: str, player_team: str, player_position: str, player_image_urls: str, player_image_types: str):
        self.player_id = player_id
        self.player_Country = player_Country
        self.player_team = player_team
        self.player_position = player_position
        self.player_image_urls = player_image_urls
        self.player_image_types = player_image_types

    @staticmethod
    def insert_player(dbo: DBObject, player_id: str, player_Country: str, player_team: str, player_position: str, player_image_urls: str, player_image_types: str)  -> Tuple[ResponseStatusCode, None | Detail]:
        try:
            Player = Playerlist(
                player_id=player_id,
                player_Country=player_Country,
                player_team=player_team,
                player_position=player_position,
                player_image_urls=player_image_urls,
                player_image_types=player_image_types,
            )
            
            dbo.session.add(Player)
            dbo.session.commit()
            
            return (ResponseStatusCode.SUCCESS, None)
        
        except Exception as e:
            dbo.session.rollback()
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(f"{e}"))


    @staticmethod
    def delete_player(dbo: DBObject, art_uuid: str, a_uuid: str) -> Tuple[ResponseStatusCode, None | Detail]:
        try:
            Playerlist = dbo.session.query(Playerlist).filter_by(art_uuid = art_uuid).first()
            if not Playerlist:
                return (ResponseStatusCode.NOT_FOUND, Detail(f"Article with id {art_uuid} not found"))

            if str(Playerlist.a_uuid) != a_uuid:
                return (ResponseStatusCode.FAIL, Detail(f"User with id {a_uuid} is not authorized to delete this article"))

            dbo.session.delete(Playerlist)
            dbo.session.commit()

            return (ResponseStatusCode.SUCCESS, None)

        except Exception as e:
            dbo.session.rollback()
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))

    @staticmethod
    def update_Playerlist(dbo: DBObject, art_uuid: str, token: str, title: str, content: str, is_anonymous: bool) -> Tuple[ResponseStatusCode, None | Detail]:
        try:
            # Token을 이용하여 사용자 확인
            response_code, result = Account._decode_token_to_uuid(token)
            if response_code != ResponseStatusCode.SUCCESS:
                return (response_code, result)
            
            a_uuid = result
            status_code, result = Playerlist._load_article_from_uuid(dbo, art_uuid)
            if status_code != ResponseStatusCode.SUCCESS:
                return (status_code, result)

            if str(result.a_uuid) != a_uuid:
                return (ResponseStatusCode.FAIL, Detail("User is not authorized to update this article"))

            # 업데이트할 게시물 찾기
            article = dbo.session.query(Article).filter(Article.art_uuid == art_uuid, Article.a_uuid == result.a_uuid).one_or_none()
            if not article:
                return (ResponseStatusCode.NOT_FOUND, Detail(f"Article with id {art_uuid} not found"))

            # 게시물 정보 업데이트
            article.title = title
            article.content = content
            article.is_anonymous = is_anonymous
            article.update_date = datetime.now()

            dbo.session.commit()

            return (ResponseStatusCode.SUCCESS, None)
        
        except Exception as e:
            dbo.session.rollback()
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))
    
    @staticmethod
    def get_article_list(dbo: DBObject, start: int = 0) -> Tuple[ResponseStatusCode, list | Detail]:
        try:
            articles = dbo.session.query(Article).all()
            articles_list = []

            for article in articles[start: min(start + 11, len(articles))]:
                if article.is_anonymous:
                    nickname = "Anonymous" #익명
                    a_uuid = "Anonymous" #익명 
                    user = dbo.session.query(Account).filter_by(a_uuid=article.a_uuid).first()
                    if user:
                        u_uuid = str(user.u_uuid)
                    else:
                        u_uuid = "Unknown"
                else:
                    user = dbo.session.query(Account).filter_by(a_uuid=article.a_uuid).first()
                    if user:
                        nickname = user.nickname
                        a_uuid = str(user.a_uuid)
                        u_uuid = str(user.u_uuid)
                    else:
                        nickname = "Unknown"
                        a_uuid = "Unknown"
                        u_uuid = "Unknown"

                articles_list.append({
                    "art_uuid": str(article.art_uuid),
                    "a_uuid": a_uuid,
                    "nickname": nickname,
                    "title": article.title,
                    "content": article.content,
                    'upload_date': article.upload_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "is_anonymous": article.is_anonymous,
                    "u_uuid": u_uuid
                })

            return (ResponseStatusCode.SUCCESS, articles_list)

        except Exception as e:
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))


