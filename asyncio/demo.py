import asyncio


# Define a coroutine
async def fetch_from_db():
    print("Fetching from the database...")
    await asyncio.sleep(2)  # Simulate an IO operation
    print("Data fetched from the database")
    return {"data": "DB_RESULT"}


async def read_file():
    print("Reading file...")
    await asyncio.sleep(1)  # Simulate an IO operation
    print("File read")
    return {"data": "FILE_CONTENT"}


async def main():
    # Schedule both coroutines to run on the event loop
    db_task = asyncio.create_task(fetch_from_db())
    file_task = asyncio.create_task(read_file())

    # Wait for both tasks to complete
    db_result, file_result = await asyncio.gather(db_task, file_task)
    print(db_result, file_result)


if __name__ == "__main__":
    # Run the event loop
    asyncio.run(main())
