# Aiogram imports
from aiogram import Router

# Project imports
from .test_handlers import test_router
from .admin_handlers import admin_router
from .other_handlers import other_router, all_router

main_router = Router()
main_router.include_routers(all_router, other_router, test_router, admin_router)