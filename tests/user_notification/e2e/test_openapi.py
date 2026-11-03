from httpx import ASGITransport, AsyncClient

from app.user_notification.main import app

# Public contract: FastAPI's documentation stays at the root.
OPENAPI_PATH = '/openapi.json'


async def test_openapi_is_published_with_the_service_title() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        response = await client.get(OPENAPI_PATH)

    assert response.status_code == 200
    assert response.json()['info']['title'] == 'TurfBook Notifications Service'
