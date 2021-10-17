import logging
from functools import partial

import uvicorn
from greppo import GreppoApp
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount
from starlette.routing import Route
from starlette.routing import WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from user_script_utils import script_task

templates = Jinja2Templates(directory="templates")


async def api_endpoint(user_script: str, request: Request):
    input_updates = {}
    try:
        input_updates = await request.json()
        logging.debug("Got input update: ", input_updates)
    except Exception:
        logging.error("Unable to parse request body: ", await request.body())

    payload = await script_task(script_name=user_script, input_updates=input_updates)

    return JSONResponse(payload)


class GreppoServer(object):
    def __init__(self, gr_app: GreppoApp, user_script: str):
        self.gr_app = gr_app
        self.user_script = user_script

    def run(self, host="127.0.0.1", port=8000):
        routes = [
            Route(
                "/api", partial(api_endpoint, self.user_script), methods=["GET", "POST"]
            ),
            WebSocketRoute("/ws", websocket_endpoint),
            Mount("/", app=StaticFiles(directory="static", html=True), name="static"),
        ]

        middleware = [
            Middleware(
                CORSMiddleware,
                allow_origins=[
                    "http://localhost:8080",
                    "http://127.0.0.1:8080",
                    "http://localhost:8000",
                    "http://127.0.0.1:8000",
                ],
                allow_methods=["GET", "POST"],
            )
        ]

        app = Starlette(debug=True, routes=routes, middleware=middleware)
        uvicorn.run(app, host=host, port=port)

    def close(self):
        pass


async def websocket_endpoint(websocket):
    await websocket.accept()
    await websocket.send_text("Hello, websocket!")
    await websocket.close()
