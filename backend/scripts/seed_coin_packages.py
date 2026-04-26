import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import async_session_maker  # noqa: E402
from app.services.coin_packages import seed_default_coin_packages  # noqa: E402


async def main() -> None:
    async with async_session_maker() as session:
        packages = await seed_default_coin_packages(session)
        await session.commit()

    print(f"Seeded {len(packages)} active coin packages.")


if __name__ == "__main__":
    asyncio.run(main())
