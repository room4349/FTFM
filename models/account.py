from env.ACCOUNT import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, TOKEN_TYPE
from sqlalchemy import Column, TEXT, String, DateTime, ForeignKeyConstraint
from models.response import ResponseStatusCode, Detail
from utility.checker import is_valid_uuid_format
from sqlalchemy.dialects.postgresql import UUID
from typing import TypeVar, Tuple, Optional
from models.university import University
from database.conn import DBObject
from pydantic import BaseModel
from datetime import timedelta
from datetime import datetime
from models.base import Base
import traceback
import logging
import bcrypt
import uuid
import jwt
import os

Account = TypeVar("Account", bound="Account")


class IDPWDModel(BaseModel):
    """ 기본적인 ID, Password를 갖는 클래스, 보안을 위해 사용

    """
    user_id: str
    password: str


class SignUpModel(IDPWDModel):
    """ 유저가 회원가입을 할 때, 보안을 위해 사용되는 클래스

    """
    nickname: str
    email: str
    phone: str
    u_uuid: str
    s_id: str


class SignoutModel(IDPWDModel):
    """ 유저가 회원탈퇴를 할 때, 보안을 위해 사용되는 클래스

    """


class LoginModel(IDPWDModel):
    """ 유저가 로그인을 할 때, 보안을 위해 사용되는 클래스

    """


class ForgotPasswordModel(IDPWDModel):
    """ 유저가 비밀번호를 변경 할 떄, 보안을 위해 사용되는 클래스

    """


class TokenModel:
    access_token: str
    token_type: str

    def __init__(self, a_uuid: str):
        self.access_token = jwt.encode({
                "sub": a_uuid,
                "exp": datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            }, SECRET_KEY, algorithm=ALGORITHM)
        self.token_type = TOKEN_TYPE


class Account(Base):
    __tablename__ = "account"

    a_uuid: str = Column(UUID(as_uuid=True),
                         primary_key=True, default=uuid.uuid4())  # 계정 고유 uuid
    id: str = Column(String(15), nullable=False, unique=True)  # 계정 아이디
    nickname: str = Column(String(15), nullable=False, unique=True)  # 계정 닉네임
    password: str = Column(String(64),
                           nullable=False)  # 계정 비밀번호 (sha256 암호화 후 bcrypt 해싱)
    email: str = Column(String(50), nullable=False, unique=True)  # 계정 이메일
    phone: str = Column(String(13), nullable=False, unique=True)  # 계정 전화번호
    s_id: str = Column(TEXT)  # 학번
    profile: str = Column(TEXT, nullable=True) # 프로필 이미지
    signup_date: datetime = Column(DateTime, default=datetime.now())  # 계정 생성일
    login_date: datetime = Column(DateTime)  # 마지막 로그인 날짜
    u_uuid: str = Column(UUID(as_uuid=True), default=None)  # 학교 uuid

    __table_args__ = (ForeignKeyConstraint(
        ["u_uuid"], ["university.u_uuid"],
        ondelete="CASCADE", onupdate="CASCADE"
    ),)

    @property
    def info(self):
        return {
            "a_uuid": str(self.a_uuid),
            "id": self.id,
            "nickname": self.nickname,
            "email": self.email,
            "phone": self.phone,
            "s_id": self.s_id,
            "profile": self.profile,
            "login_date": self.login_date.strftime("%Y-%m-%d %H:%M:%S"),
            "signup_date": self.signup_date.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def __init__ (self, id: str, nickname: str, password: str, phone: str, email: str, s_id : str, u_uuid: str, a_uuid: str | None = None, login_date: datetime | None = None, signup_date: datetime | None = None):
        self.id = id
        self.nickname = nickname
        self.password = password
        self.email = email
        self.phone = phone
        self.s_id= s_id
        self.a_uuid = a_uuid
        self.login_date = login_date
        self.signup_date = signup_date
        self.u_uuid = u_uuid

    @staticmethod
    def register(dbo: DBObject, id: str, password: str, nickname: str, email: str, phone: str, u_uuid: str, s_id: str) -> Tuple[ResponseStatusCode, None | Detail]:
        try:
            if not is_valid_uuid_format(u_uuid):
                return (ResponseStatusCode.ENTITY_ERROR, Detail(f"{u_uuid} is not valid uuid format"))
            
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            status_code, result = Account.check_duplicate(dbo, id, nickname, email, phone)
            if status_code != ResponseStatusCode.SUCCESS:
                return (status_code, result)

            status_code, result = University._load_all_u_uuid(dbo)
            if status_code != ResponseStatusCode.SUCCESS:
                return (status_code, result)
            
            if u_uuid not in result:
                return (ResponseStatusCode.NOT_FOUND, Detail(f"u_uuid {u_uuid} not in University relation"))
            
            account = Account(id = id,password = hashed_password, nickname = nickname, email = email, phone = phone, u_uuid = uuid.UUID(u_uuid), s_id = s_id)
            dbo.session.add(account)
            dbo.session.commit()
            return (ResponseStatusCode.SUCCESS, None)
        
        except Exception as e:
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))
        
    def register_out(self, dbo: DBObject) -> Tuple[ResponseStatusCode, None | Detail]:
        try:
            dbo.session.query(Account).filter_by(a_uuid = self.a_uuid).delete()
            dbo.session.commit()
            return (ResponseStatusCode.SUCCESS, None)
        
        except Exception as e:
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))
            
    @staticmethod
    def login(dbo: DBObject, user_id: str, password: str) -> Tuple[ResponseStatusCode, TokenModel | Detail]: 
        try:
            status_code, result = Account._load_user_info(dbo, id = user_id)
            if status_code != ResponseStatusCode.SUCCESS:
                if status_code == ResponseStatusCode.NOT_FOUND:
                    status_code = ResponseStatusCode.FAIL
                return (status_code, result)
            
            account = result
            if account:
                if bcrypt.checkpw(password.encode("utf-8"), account.password.encode("utf-8")):
                    dbo.session.query(Account).update({"login_date": datetime.now()})
                    dbo.session.commit()
                    return (ResponseStatusCode.SUCCESS, TokenModel(str(account.a_uuid)))
                
                else:
                    return (ResponseStatusCode.FAIL, Detail("password is not corrected"))
            
            return (ResponseStatusCode.FAIL, Detail(f"{account.id} not founded in account"))            
        

        except Exception as e:
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))
    
    @staticmethod
    def forgot_password(dbo: DBObject, account_id: str, new_password: str) -> ResponseStatusCode:
        """
        Parameters:
            db_session (Session): 데이터베이스 연동을 위한 sqlalchemy Session 객체. \n
            user_id (str): 유저가 변경할 비밀번호의 아이디 \n
            session (Dict[str, Any]): 로그인을 관리하는 세션 \n
            new_password (str): 유저가 변경할 새로운 비밀번호 \n
        
        Returns:
            ResponseStatusCode.SUCCESS: 비밀번호 변경 성공. \n
            ResponseStatusCode.FAIL: 비밀번호 변경 실패. \n
            ResponseStatusCode.INTERNAL_SERVER_ERROR: 서버 내부 에러. \n
        """
        try:
            status_code, result = Account._load_user_info(dbo, id = account_id)
            if status_code != ResponseStatusCode.SUCCESS:
                if status_code == ResponseStatusCode.NOT_FOUND:
                    status_code = ResponseStatusCode.FAIL
                return (status_code, result)
            
            hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            dbo.session.query(Account).filter_by(a_uuid = Account.a_uuid).update({"password": hashed_password})
            dbo.session.commit()
            return (ResponseStatusCode.SUCCESS, None)

        except Exception as e:
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))

    @staticmethod
    def forgot_id(dbo: DBObject, email: str) -> Tuple[ResponseStatusCode, str | Detail]:
        try:
            status_code, result = Account._load_user_info(dbo, email = email)
            if status_code != ResponseStatusCode.SUCCESS:
                return (status_code, result)
            
            return (ResponseStatusCode.SUCCESS, result.id)
        
        except Exception as e:
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))
    
    @staticmethod
    def check_duplicate(dbo: DBObject, id: str | None = None, nickname: str | None = None, email: str | None = None, phone: str | None = None) -> ResponseStatusCode | str:
        query = dbo.session.query(Account)
        result = None
        detail = ""

        if id:
            result = query.filter_by(id = id).first()
            if result:
                detail = f"{id} ID already exist"
        
        if result is None and nickname:
            result = query.filter_by(nickname = nickname).first()
            if result:
                detail = f"{nickname} nickname already exist"
            
        if result is None and email:
            result = query.filter_by(email = email).first()
            if result:
                detail = f"{email} email already exist"

        if result is None and phone:
            result = query.filter_by(phone = phone).first()
            if result:
                detail = f"{phone} phone number already exist"

        return (ResponseStatusCode.SUCCESS, None) if result is None else (ResponseStatusCode.CONFLICT, Detail(detail))
    
    def update_profile_image(self, dbo: DBObject, access_token: str, profile: bytes | None = None) -> Tuple[ResponseStatusCode, None | Detail]:
        try:
            status_code, result = self._check_is_valid_token(access_token)
            if status_code != ResponseStatusCode.SUCCESS:
                return (status_code, result)
            
            if profile:
                file_name = f"{str(uuid.uuid4())}.jpg"
                with open(os.path.join("images/profile", file_name), "wb") as fp:
                    fp.write(profile)
                
                self.profile = os.path.join("images/profile", file_name)
            
            else:
                self.profile = None
                
            dbo.session.commit()
            return (ResponseStatusCode.SUCCESS, None)
            
        except Exception as e:
            dbo.session.rollback()
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))

    @staticmethod
    def _load_user_info(dbo:DBObject, a_uuid: Optional[str] = None, id: Optional[str] = None, email: Optional[str] = None) -> Tuple[ResponseStatusCode, Account | Detail]:
        try:
            result = None
            query = dbo.session.query(Account)
            if a_uuid:
                result = query.filter_by(a_uuid = a_uuid).first()
                
            elif id:
                result = query.filter_by(id = id).first()
                
            elif email:
                result = query.filter_by(email = email).first()
                
            if result:
                return (ResponseStatusCode.SUCCESS, result)
            
            return (ResponseStatusCode.NOT_FOUND, Detail("account not founded"))
            
        except Exception as e:
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))
    
    @staticmethod
    def _decode_token_to_uuid(access_token: str) -> Tuple[ResponseStatusCode, str | Detail]:
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
            a_uuid = payload.get("sub")
            if not is_valid_uuid_format(a_uuid):
                return (ResponseStatusCode.ENTITY_ERROR, Detail(f"{a_uuid} is not valid uuid format"))
            
            return (ResponseStatusCode.SUCCESS, a_uuid)
                
        except jwt.exceptions.DecodeError as e:
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.ENTITY_ERROR, Detail(str(e)))

        except Exception as e:
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))
        
    def _check_is_valid_token(self, access_token: str):
        try:
            status_code, result = Account._decode_token_to_uuid(access_token)
            if status_code != ResponseStatusCode.SUCCESS:
                return (status_code, result)
            
            if result != str(self.a_uuid):
                return (ResponseStatusCode.FAIL, Detail("uuid is not match"))
            
            return (ResponseStatusCode.SUCCESS, None)
            
        except Exception as e:
            logging.error(f"{e}: {''.join(traceback.format_exception(None, e, e.__traceback__))}")
            return (ResponseStatusCode.INTERNAL_SERVER_ERROR, Detail(str(e)))