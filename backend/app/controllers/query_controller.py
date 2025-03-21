from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from app.models.schema.query_schema import QueryRequest

from app.usecases.query_usecase import QueryUseCase

class QueryController:
    def __init__(self, query_usecase: QueryUseCase = Depends(QueryUseCase)):
        self.query_usecase = query_usecase

    async def query(
        self,
        request: QueryRequest
    ):
        response = await self.query_usecase.process_query(request)
        
        return JSONResponse(
            content={
                "data": response,
                "statuscode": 200,
                "detail": "Query processed successfully",
                "error": ""
            },
            status_code=status.HTTP_200_OK
        )
    
    async def stream_query(self, request: QueryRequest):
        return await self.query_usecase.process_query_streaming(request)