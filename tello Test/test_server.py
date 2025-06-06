#!/usr/bin/env python3
from aiohttp import web
import asyncio

async def health_handler(request):
    return web.json_response({"status": "ok"})

def create_app():
    app = web.Application()
    app.router.add_get('/health', health_handler)
    return app

async def main():
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Server started on http://0.0.0.0:8080")
    
    try:
        await asyncio.Future()  # run forever
    except KeyboardInterrupt:
        pass
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main()) 