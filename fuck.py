import requests
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from database.conn import DBObject  # DBObject를 직접 여기서 임포트합니다.
import unicodedata  # 문자열 정규화를 위한 모듈

Base = declarative_base()

class TeamList(Base):
    """
    팀 목록을 저장하는 데이터베이스 테이블을 나타내는 클래스입니다.
    """
    __tablename__ = "TeamList"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    shortName = Column(String)
    tla = Column(String)
    crest = Column(String)
    address = Column(Text)
    website = Column(String)
    founded = Column(String)
    clubColors = Column(String)
    venue = Column(String)

    @classmethod
    def get_api_data(cls, uri, headers, params):
        """
        주어진 API 엔드포인트에서 데이터를 가져오는 정적 메서드입니다.
        """
        try:
            response = requests.get(uri, headers=headers, params=params)
            if response.status_code == 200:
                response.encoding = 'utf-8'  # 인코딩을 명시적으로 UTF-8로 설정합니다.
                api_data = response.json()
                return api_data
            else:
                print(f"API 요청 오류: {response.status_code}")
        except requests.RequestException as e:
            print(f"API 요청 중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    # API 설정
    uri = 'http://api.football-data.org/v4/teams/'
    headers = {'X-Auth-Token': 'fc80ad2a4cab4d959d168d5c67e7cb3b'}
    params = {'limit': 500}

    # API에서 데이터 가져오기
    api_data = TeamList.get_api_data(uri, headers, params)
    if api_data is None or 'teams' not in api_data:
        print("API에서 팀 데이터를 가져오는 데 실패했습니다.")
    else:
        # 팀 데이터 출력
        print("팀 데이터:")
        for team in api_data['teams']:
            print(f"ID: {team['id']}")
            print(f"Name: {team['name']}")
            print(f"Short Name: {team.get('shortName', '')}")
            print(f"TLA: {team.get('tla', '')}")
            print(f"Crest URL: {team.get('crest', '')}")
            print(f"Address: {team.get('address', '')}")
            print(f"Website: {team.get('website', '')}")
            print(f"Founded: {team.get('founded', '')}")
            print(f"Club Colors: {team.get('clubColors', '')}")
            print(f"Venue: {team.get('venue', '')}")
            print("-" * 30)
