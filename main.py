#使用前通过命令安装pip install fastapi uvicorn[standard]
#pip install typer
#运行命令uvicorn main:app --reload

#外部访问需要使用cpolar穿透命令为cpolar http 8080
#需要在服务器上安装curl -L https://www.cpolar.com/static/downloads/install-release-cpolar.sh | sudo bash
#cpolar authtoken xxxxxxx
#uvicorn main:app --reload
#cpolar http 8080
#之后会出现一个外部的网址，可以访问
from typing import Union

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}