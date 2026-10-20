import pytest_asyncio
import httpx

from red_blue_field.api import create_app
from red_blue_field.config import Settings


@pytest_asyncio.fixture
async def app(tmp_path):
    value = create_app(Settings(data_dir=tmp_path, control_token='test-control-token-' + 'x' * 24))
    yield value
    await value.state.lab.close()


@pytest_asyncio.fixture
async def client(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test', headers={'X-Control-Token': app.state.lab.settings.control_token}) as value:
        yield value
