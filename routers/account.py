from models.response import ResponseStatusCode, ResponseModel, Detail
from models.account import SignUpModel, ForgotPasswordModel
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from database.conn import DBObject
from models.account import Account
import os


account_router = APIRouter(
    prefix="/account",
    tags=["account"]
)

@account_router.put("/register", 
    responses={
        200: {
            "description":"회원가입에 성공하여 account 테이블에 데이터가 등록되었을 때 발생합니다.",
            "content": {
                "application/json": {
                    "example": {"status_code": 200,"message": "회원가입에 성공하였습니다!"}
                }
            }
        },
        401: {
            "description":"회원가입에 실패하여 account 테이블에 데이터가 등록이 안되었을 때 발생합니다.",
            "content": {
                "application/json": {
                    "example": {"status_code": 401, "message": "회원가입에 실패하였습니다.", "detail": "regitser is failed."}
                }
            }
        },
        404: {
            "description":"입력받은 u_uuid가 university 테이블에 데이터가 등록이 안되어있을때 발생합니다.",
            "content": {
                "application/json": {
                    "example": {"status_code": 404, "message": "등록되지 않은 대학교입니다.", "detail": "u_uuid wow_awesome_uuid not found in University relation."}
                }
            }
        },
        409: {
            "description":"이미 account테이블에 데이터가 등록되어 있을 때 발생합니다.",
            "content": {
                "application/json": {
                    "example": {"status_code": 409,"message": "이미 등록된 계정 또는 이메일 입니다.","detail": "F_bomber is already exist."}
                }
            }
        },
        422: {
            "description": "데이터 타입 잘못.",
            "content": {
                "application/json":{
                    "example": {"status_code": 422, "message": "데이터 타입 오류가 발생하였습니다.", "detail": "data type error"}
                }
            } 
        },
        500: {
            "description":"이미 account테이블에 데이터가 등록되어 있을 때 발생합니다.",
            "content": {
                "application/json": {
                    "example": {"status_code": 500, "message": "서버 내부 에러가 발생하였습니다.", "detail": "Error occured."}
                }
            }
        }
    },
    name = "회원 가입"
)
async def register(model: SignUpModel):
    response_dict = {
        ResponseStatusCode.SUCCESS: "회원가입에 성공하였습니다.",
        ResponseStatusCode.FAIL: "회원가입에 실패하였습니다.",
        ResponseStatusCode.NOT_FOUND: "등록되지 않은 대학교입니다.",
        ResponseStatusCode.CONFLICT: "이미 등록된 계정 또는 이메일 입니다.",
        ResponseStatusCode.ENTITY_ERROR: "유효하지 않은 uuid 포맷입니다.",
        ResponseStatusCode.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }
    
    status_code, detail = Account.register(DBObject.instance, model.user_id, model.password, model.nickname, model.email, model.phone, model.u_uuid, model.s_id)

    if status_code != ResponseStatusCode.SUCCESS:
        return ResponseModel.show_json(status_code = status_code.value, message = response_dict[status_code], detail = detail.text)
    
    return ResponseModel.show_json(status_code = status_code.value, message = response_dict[status_code])

@account_router.post("/login",
responses={
    200: {
        "description": "로그인 요청이 성공적으로 수행 됐을때 발생한다.",
        "content": {
            "application/json": {
                "example": {"status_code": 200, "message": "로그인에 성공하였습니다.", "token": "access_token here"}
            }
        }
    },
    401: {
        "description": "로그인 요청이 실패 됐을때 발생한다.",
        "content": {
            "application/json": {
                "example": {"status_code": 401,"message": "아이디 또는 비밀번호가 일치하지 않습니다.","detail": "login is false"}
            }
        }
    },
    422:{
        "description": "로그인 요청을 할때 데이터 타입을 잘못 적었을때 발생한다.",
        "content": {
            "application/json": {
                "example": {"status_code": 422, "message": "데이터 타입이 정확하지 않습니다.","detail": "data type error"}
            }
        }
    },
    500:{
        "description": "서버 내부에서 에러가 났을때 발생한다.",
        "content": {
            "application/json": {
                "example": {"status_code": 500, "message": "서버 내부 에러","detail": "Error occured."}
            }
        }
    },
},
name = "로그인"
)
async def login(model: OAuth2PasswordRequestForm = Depends()):
    response_dict = {
        ResponseStatusCode.SUCCESS: "로그인에 성공하였습니다.",
        ResponseStatusCode.FAIL: "아이디 또는 비밀번호가 일치하지 않습니다.",
        ResponseStatusCode.ENTITY_ERROR: "데이터 형식이 잘못되었습니다.",
        ResponseStatusCode.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }
    
    status_code, detail = Account.login(DBObject.instance, model.username, model.password)
    
    if isinstance(detail, Detail):
        return ResponseModel.show_json(status_code.value, message = response_dict[status_code], detail = detail.text)
        
    return ResponseModel.show_json(status_code.value, message = response_dict[status_code], token = detail.access_token)


@account_router.delete("/signout", 
    responses={
        200: {
            "content": {
                "description": "회원탈퇴 요청이 성공적으로 수행되었을 때 발생합니다.",
                "application/json": {
                    "example": {"status_code": 200,"message": "회원탈퇴에 성공하였습니다."}
                }
            }
        },
        401: {
            "description": "회원탈퇴 요청이 실패했을 때 발생 합니다.",
            "content": {
                "application/json": {
                    "example": {"status_code": 401,"message": "회원탈퇴에 실패하였습니다.", "detail" : "Failed to register_out"}
                }
            }
        },
        408: {
            "description": "세션이 만료 됐을때 뜨는 에러.",
            "content": {
                "application/json": {
                    "example": {"status_code": 408, "message": "세션 만료됨.", "detail": "Session Expiration"}
                }
            }
        }
    },
    name = "회원탈퇴"
)
async def register_out(id: str, password: str):
    response_dict = {
        ResponseStatusCode.SUCCESS: "회원탈퇴에 성공하였습니다.",
        ResponseStatusCode.FAIL: "회원탈퇴에 실패하였습니다.",
        ResponseStatusCode.TIME_OUT: "세션이 만료되었습니다.",
        ResponseStatusCode.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }

    result = (ResponseStatusCode.FAIL, "User Not founded")
    status_code, result = Account._load_user_info(DBObject.instance, id = id)
    if status_code != ResponseStatusCode.SUCCESS:
        return ResponseModel.show_json(status_code.value, message = response_dict[status_code], detail = detail.text)
    
    user = result
    if Account.login(DBObject.instance, id, password)[0] == ResponseStatusCode.SUCCESS:
        result = user.register_out(DBObject.instance)

    status_code, detail = result
    return ResponseModel.show_json(status_code.value, message = response_dict[status_code], detail = detail)

@account_router.post("/forgot/id", responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"status_code": 200, "message": "아이디를 성공적으로 찾았습니다!", "user_id": "union_user"}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"status_code": 401, "message": "아이디를 불러오는데 실패하였습니다.", "detail": "ID not found"}
                }
            }
        },
        
        500: {
            "content": {
                "application/json": {
                    "example": {"status_code": 500, "message": "서버 내부 에러", "detail": "error occured"}
                }
            }
        }
    },
    name = "아이디 찾기")
async def forgot_id(email: str):
    response_dict = {
        ResponseStatusCode.SUCCESS: "아이디를 성공적으로 찾았습니다!",
        ResponseStatusCode.FAIL: "아이디를 불러오는데 실패하였습니다.",
        ResponseStatusCode.INTERNAL_SERVER_ERROR: "서버 내부에러가 발생하였습니다."
    }
    
    status_code, result = Account.forgot_id(DBObject.instance, email)
    if status_code != ResponseStatusCode.SUCCESS:
        return ResponseModel.show_json(status_code.value, message = response_dict[status_code], detail = result.text)
    
    return ResponseModel.show_json(status_code.value, message = response_dict[status_code], user_id = result)

@account_router.post("/forgot/password",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"status_code": 200, "message": "성공적으로 정보를 변경하였습니다."}
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "example": {"status_code": 401, "message": "정보 변경에 실패하였습니다.", "detail": "ID not found"}
                }
            }
        },
        500: {
            "content": {
                "application/json": {
                    "example": {"status_code": 500, "message": "서버 내부 에러", "detail": "error occured"}
                }
            }
        }
    },
    name = "비밀번호 변경")
async def forgot_password(model: ForgotPasswordModel):
    response_dict = {
        ResponseStatusCode.SUCCESS: "성공적으로 정보를 변경하였습니다.",              
        ResponseStatusCode.FAIL: "정보 변경에 실패하였습니다.",
        ResponseStatusCode.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }
    
    status_code, result = Account.forgot_password(DBObject.instance, model.user_id, model.password)
    if status_code != ResponseStatusCode.SUCCESS:
        return ResponseModel.show_json(status_code.value, message = response_dict[status_code], detail = result.text)
    
    return ResponseModel.show_json(status_code.value, message = response_dict[status_code])

@account_router.post("/duplicate/{parameter}", responses={
        200: {
            "description":"데이터가 사용가능할 때 발생합니다.",
            "content": {
                "application/json": {
                    "example": {"status_code": 200, "message": "사용 가능한 정보입니다!"}
                }
            }
        },
        409: {
            "description":"데이터가 중복될 때 발생합니다.",
            "content": {
                "application/json": {
                    "example": {"status_code": 409, "message": "이미 사용중인 정보입니다.", "detail": "example_id id already exist"}
                }
            }
        },
        422: {
            "description": "Path Parameter가 잘못 전달되었을 때 발생합니다.",
            "content": {
                "application/json":{
                    "example": {"status_code": 422, "message": "엔티티 전달이 잘못되었습니다.", "detail": "Path Parameter Key값은 id, nickname, phone, email 입니다."}
                }
            } 
        },
        500: {
            "description":"코드 에러가 있을 때 발생합니다.",
            "content": {
                "application/json": {
                    "example": {"status_code": 500, "message": "서버 내부 에러가 발생하였습니다.", "detail": "Error occured."}
                }
            }
        }
    },
    name = "정보 중복 체크"
)
async def check_duplicate(parameter: str, data: str):
    data_dict = {
        "id": "아이디",
        "nickname": "닉네임",
        "phone": "핸드폰 번호",
        "email": "이메일"
    }
    
    if parameter not in data_dict.keys():
            return ResponseModel.show_json(ResponseStatusCode.ENTITY_ERROR.value, message = "엔티티 전달이 잘못되었습니다.", detail = "Path Parameter Key값은 id, nickname, phone, email 입니다.")
    
    response_dict = {
        ResponseStatusCode.SUCCESS: f"사용 가능한 {data_dict[parameter]}입니다!",
        ResponseStatusCode.CONFLICT: f"이미 사용중인 {data_dict[parameter]}입니다.",
        ResponseStatusCode.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }
    
    if parameter == "id":
        status_code, result = Account.check_duplicate(DBObject.instance, id = data)
    
    elif parameter == "nickname":
        status_code, result = Account.check_duplicate(DBObject.instance, nickname = data)
    
    elif parameter == "phone":
        status_code, result = Account.check_duplicate(DBObject.instance, phone = data)
        
    else:
        status_code, result = Account.check_duplicate(DBObject.instance, email = data)
    
    if status_code != ResponseStatusCode.SUCCESS:
        return ResponseModel.show_json(status_code.value, message = response_dict[status_code], detail = result.text)
    
    return ResponseModel.show_json(status_code.value, message = response_dict[status_code])

@account_router.get("/profile", responses={
        200: {
            "description": "프로필을 성공적으로 조회했을 때 발생합니다.",
            "content": {
                "application/json": {
                    "example": {"status_code": 200, "message": "프로필을 성공적으로 조회했습니다!", "account_info": {
                        "a_uuid": "9c2670bb-cb37-44ef-9980-f2fe99d4bb00",
                        "id": "union_id",
                        "nickname": "mynameisunion",
                        "email": "2237001@pcu.ac.kr",
                        "phone": "010-0000-0000",
                        "s_id": "2237001",
                        "login_date": "2024-06-01 00:00:00",
                        "signup_date": "2024-05-15 00:00:00"
                    }}
                }
            }
        },
        404: {
            "description": "데이터베이스에 유저 정보가 존재하지 않을 때 발생합니다.",
            "content": {
                "application/json": {
                    "example": {"status_code": 404, "message": "프로필 정보를 불러오는데 실패하였습니다.", "detail": "account not found"}
                }
            }
        },
        422: {
            "description": "전달받은 토큰값이 올바르지 않을 때 발생합니다.",
            "content": {
                "application/json":{
                    "example": {"status_code": 422, "message": "토큰 형식이 잘못되었습니다.", "detail": "Invalid header string: 'utf-8' codec can't decode byte 0x9d in position 15: invalid start byte"}
                }
            } 
        },
        500: {
            "description":"코드 에러가 있을 때 발생합니다.",
            "content": {
                "application/json": {
                    "example": {"status_code": 500, "message": "서버 내부 에러가 발생하였습니다.", "detail": "Error occured."}
                }
            }
        }
    },
    name="프로필 조회"
)
async def get_profile(access_token: str):
    response_dict = {
        ResponseStatusCode.SUCCESS: "프로필을 성공적으로 조회하였습니다.",
        ResponseStatusCode.NOT_FOUND: "프로필 정보를 불러오는데 실패하였습니다.",
        ResponseStatusCode.ENTITY_ERROR: "토큰 형식이 잘못되었습니다.",
        ResponseStatusCode.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }
    
    status_code, result = Account._decode_token_to_uuid(access_token)
    if status_code == ResponseStatusCode.SUCCESS:
        status_code, result = Account._load_user_info(DBObject.instance, a_uuid=result)
        
        return ResponseModel.show_json(status_code.value, message = response_dict[status_code], account_info = result.info)
    
    if status_code != ResponseStatusCode.SUCCESS:
        return ResponseModel.show_json(status_code.value, message = response_dict[status_code], detail = result.text)
        
@account_router.get("/profile/image")
async def get_profile_image(access_token: str):
    response_dict = {
        ResponseStatusCode.SUCCESS: "프로필을 성공적으로 조회하였습니다.",
        ResponseStatusCode.NOT_FOUND: "프로필 정보를 불러오는데 실패하였습니다.",
        ResponseStatusCode.ENTITY_ERROR: "토큰 형식이 잘못되었습니다.",
        ResponseStatusCode.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }
    
    status_code, result = Account._decode_token_to_uuid(access_token)
    if status_code == ResponseStatusCode.SUCCESS:
        status_code, result = Account._load_user_info(DBObject.instance, a_uuid = result)
        if status_code == ResponseStatusCode.SUCCESS:
            return ResponseModel.show_image(os.path.join("images/profile", "default_user.png") if not result.profile else result.profile)
    
    return ResponseModel.show_json(status_code.value, message = response_dict[status_code], detail = result.text)

@account_router.post("/profile/image/update")
async def update_profile_image(access_token: str, file: UploadFile = File(None)):
    response_dict = {
        ResponseStatusCode.SUCCESS: "프로필을 성공적으로 업데이트 하였습니다.",
        ResponseStatusCode.FAIL: "ㅁㄴㅇ",
        ResponseStatusCode.NOT_FOUND: "사용자 정보를 불러오는데 실패하였습니다.",
        ResponseStatusCode.ENTITY_ERROR: "엔티티 형식이 잘못되었습니다.",
        ResponseStatusCode.INTERNAL_SERVER_ERROR: "서버 내부 에러가 발생하였습니다."
    }
    
    status_code, result = Account._decode_token_to_uuid(access_token)
    if status_code == ResponseStatusCode.SUCCESS:
        status_code, result = Account._load_user_info(DBObject.instance, a_uuid = result)
        
        if status_code == ResponseStatusCode.SUCCESS:
            status_code, result = result.update_profile_image(DBObject.instance, access_token, file)
            
            if status_code == ResponseStatusCode.SUCCESS:
                return ResponseModel.show_json(status_code.value, message = response_dict[status_code])
            
    return ResponseModel.show_json(status_code.value, message = response_dict[status_code], detail = result.text)
    