from fastapi import FastAPI
from database import engine
import models
from routers import router

# Создание таблиц
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Simple Forum API")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)