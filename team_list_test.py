import requests
import json
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from database.conn import DBObject
import unicodedata
import chardet

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
    founded = Column(Integer)
    clubColors = Column(String)
    venue = Column(String)

    @classmethod
    def normalize_string(cls, s):
        """
        문자열을 NFC(Normalization Form C)로 정규화합니다.
        """
        if s:
            return unicodedata.normalize('NFC', s)
        else:
            return None

    @classmethod
    def get_api_data(cls, uri, headers, params, output_file='team_data.json'):
        """
        주어진 API 엔드포인트에서 데이터를 가져오는 정적 메서드입니다.
        """
        try:
            response = requests.get(uri, headers=headers, params=params)
            response.raise_for_status()

            # 인코딩 감지하여 디코딩하기
            encoding = chardet.detect(response.content)['encoding']
            api_data = response.content.decode(encoding)

            if response.status_code == 200:
                response.encoding = 'utf-8'  # 인코딩을 UTF-8로 설정합니다.
                api_data = response.json()
                print("API에서 팀 데이터를 성공적으로 가져왔습니다.")  # 성공 메시지 출력

                # API에서 가져온 데이터 출력
                print("API에서 가져온 팀 데이터:")
                for team in api_data['teams']:
                    print(team)

                # JSON 파일로 저장
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(api_data, f, ensure_ascii=False, indent=4)
                print(f"데이터를 JSON 파일({output_file})로 성공적으로 저장했습니다.")

                return api_data
            else:
                print(f"API 요청 오류: {response.status_code}")
        except requests.RequestException as e:
            print(f"API 요청 중 오류 발생: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON 디코딩 오류 발생: {e}")
        except Exception as e:
            print(f"기타 오류 발생: {e}")
        return None

    @classmethod
    def team_list_get(cls, dbo: DBObject):
        # API 설정
        uri = 'http://api.football-data.org/v4/teams/'
        headers = {'X-Auth-Token': 'fc80ad2a4cab4d959d168d5c67e7cb3b'}
        params = {'limit': 5000}

        # API에서 데이터 가져오기
        api_data = cls.get_api_data(uri, headers, params)
        if api_data is None or 'teams' not in api_data:
            print("API에서 팀 데이터를 가져오는 데 실패했습니다.")
            return False  # 실패 시 False를 반환합니다.

        try:
            # 데이터베이스에 저장
            for team_json in api_data['teams']:
                # 팀 데이터를 TeamList 객체로 매핑하여 데이터베이스에 저장
                team_data = TeamList(
                    id=team_json['id'],
                    name=cls.normalize_string(team_json['name']),  # 이름 정규화
                    shortName=cls.normalize_string(team_json.get('shortName', '')),
                    tla=team_json.get('tla', ''),
                    crest=team_json.get('crest', ''),
                    address=team_json.get('address', ''),
                    website=team_json.get('website', ''),
                    founded=team_json.get('founded') if team_json.get('founded') is not None else None,
                    clubColors=team_json.get('clubColors', ''),
                    venue=team_json.get('venue', '')
                )
                dbo.session.add(team_data)  # 이미 존재하는 경우 업데이트, 없는 경우 삽입합니다.
            dbo.session.commit()
            print("데이터를 데이터베이스에 성공적으로 삽입했습니다.")
            return True  # 성공 시 True를 반환합니다.
        except Exception as e:
            dbo.session.rollback()
            print(f"데이터 삽입 중 오류 발생: {e}")
            return False  # 실패 시 False를 반환합니다.

def main():
    # 데이터베이스 객체 생성
    dbo = DBObject()

    # 팀 목록 저장 메서드 호출
    Team_list_save_status = TeamList.team_list_get(dbo)
    
    if Team_list_save_status:
        print("팀 목록 저장에 성공했습니다.")
    else:
        print("팀 목록 저장에 실패했습니다.")

if __name__ == "__main__":
    main()
