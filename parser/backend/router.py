from fastapi import APIRouter, Request

import models
import schemas
import service


router = APIRouter()


@router.get('/')
async def root():
    return 'Service up'


@router.get('/items')
async def get_items(request: Request, limit=20):
    return service.get_items(request.app.state.engine, limit)


@router.post('/items')
async def insert_items(request: Request, items: list[models.Item]):
    items = [schemas.Item(**item.model_dump()) for item in items]
    return service.insert_items(request.app.state.engine, items)


@router.delete('/items')
async def delete_item(request: Request, item_name: str):
    return service.delete_item(request.app.state.engine, item_name)