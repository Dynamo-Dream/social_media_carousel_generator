import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

db_client = None
db_name = os.getenv("MONGO_DB_NAME")
db_async_client = None


def get_db():
    try:
        global db_client
        if db_client is None:
            db_client = MongoClient(os.getenv("MONGO_DB_URI"))
        return db_client[db_name]
    except Exception as database_error:
        raise ValueError(
            status_code=400,
            detail="Error When Connecting to Databse",
        ) from database_error


def get_thread_source_transcription_in_json(url: str):
    try:
        db = get_db()
        thread_source_collection = db["thread_source_datas"]
        # print(url)
        thread_source_doc = thread_source_collection.find_one({"source_url": url})
        # print(thread_source_doc)
        if not thread_source_doc:
            raise ValueError(f"Document with id {url} not found")

        if (
            thread_source_doc["youtube_metadata"] is None
            or thread_source_doc["youtube_metadata"]["transcriptions"] is None
            or len(thread_source_doc["youtube_metadata"]["transcriptions"]) == 0
        ):
            raise ValueError(f"Document with id {url} does not have transcriptions")

        json_data = thread_source_doc["youtube_metadata"]["transcriptions"][0][
            "transcription"
        ]
        for dictionary in json_data:
            del dictionary["_id"]
        return json_data

    except Exception as e:
        print(e)
        raise ValueError(
            f"Some error occured while fetching transcription for document {url}"
        )
