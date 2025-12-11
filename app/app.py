from util.trading_app import Trading_app
import asyncio


async def main():
    app = Trading_app()
    await app.run()


asyncio.run(main())
