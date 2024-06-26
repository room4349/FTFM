import sys
import os

from team_list_test import TeamList  # models 폴더에 있는 team_list_test 모듈에서 TeamList 클래스를 임포트합니다.
from database.conn import DBObject

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
