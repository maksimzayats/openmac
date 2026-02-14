from diwire import Injected, Scope, resolver_context
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from achrome.core.apple_events.apple_events import ChromeAppleEvents
from achrome.ioc.container import get_container

app = FastAPI()


@app.get("/", include_in_schema=False)
def read_root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/v1/tabs/")
@resolver_context.inject(scope=Scope.REQUEST)
def list_tabs_route(
    chrome_api: Injected[ChromeAppleEvents],
):
    t = chrome_api.list_tabs()
    print(f"{t = }")


@app.get("/v1/tabs/{tab_id}/html")
@resolver_context.inject(scope=Scope.REQUEST)
def get_tab_html_route(tab_id: int):
    pass


@app.get("/v1/tabs/{tab_id}/snapshot")
@resolver_context.inject(scope=Scope.REQUEST)
def get_tab_snapshot_route(tab_id: int):
    pass


if __name__ == "__main__":
    import uvicorn

    _ = get_container()
    uvicorn.run(app, host="localhost", port=8022)
