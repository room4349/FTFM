from models.response import ResponseModel, ResponseStatusCode
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from env.team_list import API_KEY, CARRERNET_URL
from fastapi.openapi.utils import get_openapi
from database.conn import DBObject
from models.team_list import TeamList
from fastapi import FastAPI
import uvicorn
import routers


app = FastAPI()

def custom_openapi():
    if not app.openapi_schema:
        app.openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            terms_of_service=app.terms_of_service,
            contact=app.contact,
            license_info=app.license_info,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=app.servers,
        )
        for _, method_item in app.openapi_schema.get('paths').items():
            for _, param in method_item.items():
                responses = param.get('responses')
                if '422' in responses:
                    del responses['422']

    return app.openapi_schema


app.openapi = custom_openapi
app.include_router(routers.TeamList_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    data = exc.__dict__["_errors"][0]
    message = "데이터를 서버에 전송해 주세요." if data["type"] == "missing" else "Validation 오류가 발생하였습니다."
    print(data)
    return ResponseModel.show_json(
        status_code=422,
        message=message,
        detail=f"{data['type']} {data['loc'][0]} in {data['loc'][1]}, {data['msg']}"
    )

if __name__ == "__main__":
    status_code, data =  TeamList._check_data_exist(DBObject.instance)
    if status_code != ResponseStatusCode.CONFLICT:
        status_code, result = TeamList._init_univ(DBObject.instance, CARRERNET_URL, API_KEY)
        if status_code != ResponseStatusCode.SUCCESS:
            print(result.text)
            exit(0)
    
    status_code, data = TeamList._check_image_exist(DBObject.instance)
    
    uvicorn.run("main:app", reload=True, host = "localhost", port = 8000)
