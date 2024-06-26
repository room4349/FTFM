from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any


def load_postgresql_user_info() -> Dict[str, Any]:
    """ load_postgresql_user_info() 함수는 데이터베이스를 연결하는데 필요한 정보들을
        user_info.txt 파일에서 불러오는 역할을 합니다.

    ### Raises
        - FileNotFoundError: user_info.txt 파일을 찾을 수 없거나 경로가 잘못 됐을 때 발생하는 에러입니다.
            user_info.txt 파일은 main.py 파일과 같은 경로에 있어야 합니다.
        - ValueError: user_info.txt 파일에서 정보를 찾을 수 없을 때 발생하는 에러입니다.
            정보는 user, password, host, port, db 가 필요합니다.
        - IndexError: user_info.txt 파일에서 키와 값의 개수가 맞지 않을 때 발생하는 에러입니다.
        - KeyError: user_info.txt 파일에서 필요한 정보가 부족할 때 발생하는 에러입니다.

    ### Returns
        Dict[str, Any]: user_info.txt 파일에서 불러온 정보들을 반환합니다.
    """
    try:
        f = open("user_info.txt", "r")

    except FileNotFoundError:
        raise FileNotFoundError("user_info.txt의 파일 경로가 잘못됐습니다.")

    lines = list(map(lambda x: x.replace("\n", ""), f.readlines()))
    keys, values = list(), list()

    for line in lines:
        split_line = list(map(lambda x: x.strip(), line.split("=")))
        if "" in split_line:
            raise ValueError("user_info.txt에 정보를 입력해주세요.")

        keys.append(split_line[0])
        values.append(split_line[1])

    if len(keys) != len(values):
        raise IndexError("Key와 Value의 개수를 맞춰주세요.")

    must_info = ["host", "user", "password", "port", "db"]
    for info in must_info:
        if info not in keys:
            raise KeyError(f"필수 정보는 f{', '.join(must_info)}")

    return {keys[i]: values[i] for i in range(len(keys))}


class DBObject(object):
    """ DBObject 클래스는 데이터베이스 시스템에 연결 해주는 패키지 입니다.

    """
    def __init__(self):
        user_info = load_postgresql_user_info()
        DB_URL = f'''postgresql://{user_info["user"]}:\
            {user_info["password"]}@{user_info["host"]}:{user_info["port"]}/\
            {user_info["db"]}'''
        self.engine = create_engine(DB_URL.replace(" ", ""))
        self.session = sessionmaker(bind=self.engine)()

    def __del__(self):
        self.engine.dispose()
        self.session.close()

    # DBObject 클래스를 싱글톤으로 구현
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(DBObject, cls).__new__(cls)

        return cls.instance
