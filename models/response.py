from fastapi.responses import JSONResponse, FileResponse
from enum import Enum


class ResponseStatusCode(Enum):
    SUCCESS = 200  # 성공
    FAIL = 401  # 실패
    FORBIDDEN = 403  # 접근 권한 없음
    NOT_FOUND = 404  # 경로 또는 자료를 찾을 수 없음 (보통 경로)
    TIME_OUT = 408  # 세션 만료됨
    CONFLICT = 409  # 데이터 충돌
    ENTITY_ERROR = 422  # 입력 데이터 타입이 잘못됨
    INTERNAL_SERVER_ERROR = 500  # 서버 내부 에러


class Detail:
    text: str | None

    def __init__(self, text: str):
        self.text = text


class ResponseModel:
    status_code: int

    @staticmethod
    def show_json(status_code: int, **kwargs):
        show_dict = {"status_code": status_code}
        for key in kwargs.keys():
            if kwargs[key]:
                show_dict[key] = kwargs[key]

        return JSONResponse(show_dict, status_code=status_code)

    @staticmethod
    def show_image(image_path: str):
        return FileResponse(path=image_path, media_type="image/png")
