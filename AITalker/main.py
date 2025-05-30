#使用前通过命令安装pip install "fastapi[standard]"
#pip install typer
#运行命令fastapi dev --app main:app
from typing import Union

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}