from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import create_engine
import uvicorn

from router import router
from db_init import create_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = create_engine("postgresql+psycopg2://postgres:admin@localhost/steamstats")
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)


if __name__ == '__main__':
    create_db()
    uvicorn.run(app, host='0.0.0.0', port=8000)