import modal
import logging


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
app = modal.App(
    "speech-coach",
    image=modal.Image.debian_slim(),
    secrets=[],
)


from modal import asgi_app
import fastapi
from fastapi import Request


web_app = fastapi.FastAPI()


@app.function(keep_warm=1, timeout=60 * 60)
@asgi_app()
def wrapper():
    return web_app


@web_app.post("/memory")
async def generate(
    request: Request,
    uid: str,
):
    print(request, uid)
    return {"message": "Hi"}
