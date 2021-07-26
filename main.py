import sys
sys.path.extend(["src"])
from src.main import main
import asyncio

if __name__ == '__main__':
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(main(main_loop))
