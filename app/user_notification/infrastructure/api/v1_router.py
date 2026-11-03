from fastapi import APIRouter

API_VERSION_PREFIX = '/v1'

router = APIRouter(prefix=API_VERSION_PREFIX)
