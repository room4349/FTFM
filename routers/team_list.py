from models.response import ResponseStatusCode, ResponseModel, Detail
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from database.conn import DBObject
from team_list import TeamList
import os


TeamList_router = APIRouter(
    prefix="/TeamList",
    tags=["TeamList"]
)


@TeamList_router.get("/", responses={
    200: {
        "description": "u_uuid에 삽입되어 있는 값은, 실제 존재하지 않는 값입니다.",
        "content": {
            "application/json": {
                "example": {
                    "status_code": 200, "message": "데이터를 불러오는데 성공하였습니다.", "univ_list": [
                        {
                            "u_uuid": "066ce1a1-4153-4b3e-9a3a-04b92a877fc1",
                            "univ_name": "서울대학교(서울특별시)"
                        },
                        {
                            "u_uuid": "ff934e6f-294b-472a-8e64-6e1c3b012a1b",
                            "univ_name": "고려대학교(서울특별시)"
                        },
                        {
                            "u_uuid": "4013a665-b7c5-45a5-9bb4-c31576820151",
                            "univ_name": "연세대학교(서울특별시)"
                        },
                        {
                            "u_uuid": "f50f071e-06e1-43f5-aae3-dfb8c23fb063",
                            "univ_name": "배재대학교(대전광역시)"
                        },
                        {
                            "u_uuid": "290b7568-1800-4e07-a628-3f74061de2df",
                            "univ_name": "우송대학교(대전광역시)"
                        },
                        {
                            "u_uuid": "9ab8c8f9-98f6-4681-92bf-411982a7651d",
                            "univ_name": "목원대학교(대전광역시)"
                        }
                    ]
                }
            }
        }
    },
    404: {
        "description": "데이터베이스에 데이터가 존재하지 않을 때 발생합니다.",
        "content": {
            "application/json": {
                "example": {"status_code": 404, "message": "데이터를 불러오는데 실패하였습니다", "detail": "Data doesn't exist"}
            }
        }
    },
    500: {
        "description": "예상하지 못한 서버 에러가 발생하였을 때 발생합니다.",
        "content": {
            "application/json": {
                "example": {"status_code": 500, "message": "서버 내부 에러가 발생하였습니다.", "detail": "Error occured"}
            }
        }
    }
}, 
name="대학교 이름 조회",
description = "데이터베이스 내부에 존재하는 모든 대학교의 이름, uuid를 조회합니다.")
async def get_all_univ_list():
    message_dict = {
        ResponseStatusCode.SUCCESS: "데이터를 불러오는데 성공하였습니다.",
        ResponseStatusCode.NOT_FOUND: "데이터를 불러오는데 실패하였습니다.",
        ResponseStatusCode.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }

    status_code, result = TeamList.get_univ_name_list(DBObject.instance)
    if isinstance(result, Detail):
        return ResponseModel.show_json(status_code=status_code.value, message = message_dict[status_code], detail = result.text)
        
    return ResponseModel.show_json(status_code = status_code.value, message = message_dict[status_code], univ_list = result)
