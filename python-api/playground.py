import asyncio
import logging

logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


async def main():
    print("playground")

if __name__ == "__main__":
    asyncio.run(main())