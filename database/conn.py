from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any
import logging

def load_postgresql_user_info() -> Dict[str, Any]:
    """ user_info.txt 파일에서 데이터베이스 연결에 필요한 정보를 불러옵니다.

    Raises:
        - FileNotFoundError: user_info.txt 파일을 찾을 수 없거나 경로가 잘못 됐을 때 발생하는 에러입니다.
        - ValueError: user_info.txt 파일에서 정보를 찾을 수 없을 때 발생하는 에러입니다.
        - IndexError: user_info.txt 파일에서 키와 값의 개수가 맞지 않을 때 발생하는 에러입니다.
        - KeyError: user_info.txt 파일에서 필요한 정보가 부족할 때 발생하는 에러입니다.

    Returns:
        Dict[str, Any]: user_info.txt 파일에서 불러온 정보들을 반환합니다.
    """
    try:
        with open("user_info.txt", "r") as f:
            lines = [line.strip() for line in f]

        keys, values = [], []
        for line in lines:
            split_line = list(map(lambda x: x.strip(), line.split("=")))
            if "" in split_line or len(split_line) != 2:
                raise ValueError("user_info.txt에 올바른 정보를 입력해주세요.")

            keys.append(split_line[0])
            values.append(split_line[1])

        if len(keys) != len(values):
            raise IndexError("Key와 Value의 개수를 맞춰주세요.")

        must_info = ["host", "user", "password", "port", "db"]
        for info in must_info:
            if info not in keys:
                raise KeyError(f"필수 정보는 {', '.join(must_info)} 입니다.")

        return {keys[i]: values[i] for i in range(len(keys))}

    except FileNotFoundError:
        logging.error("user_info.txt 파일을 찾을 수 없습니다.")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise

class DBObject(object):
    """ DBObject 클래스는 데이터베이스 시스템에 연결을 관리합니다. """
    def __init__(self):
        try:
            user_info = load_postgresql_user_info()
            DB_URL = f"postgresql://{user_info['user']}:{user_info['password']}@{user_info['host']}:{user_info['port']}/{user_info['db']}"
            self.engine = create_engine(DB_URL)
            self.session = sessionmaker(bind=self.engine)()
        except Exception as e:
            logging.error(f"Failed to initialize DBObject: {e}")
            raise

    def __del__(self):
        try:
            self.session.close()
            self.engine.dispose()
        except Exception as e:
            logging.error(f"Failed to clean up DBObject: {e}")

    # DBObject 클래스를 싱글톤으로 구현
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(DBObject, cls).__new__(cls)
        return cls.instance
