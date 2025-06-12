from src.db import get_thread_source_transcription_in_json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import json

load_dotenv()


def content_generator(url: str):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.5)
    transcripitons = get_thread_source_transcription_in_json(url)
    text1 = " ".join([transcription["text"] for transcription in transcripitons])

    prompt = f"""
    You are an expert writer who provides consise and accurate notes from a transcription of a youtube video.
    You will be given a transcripiton of a youtube video, using that create a title and concise point wise notes. Use simple text format, not the markdown format.
    Each point should contain maximum of 40-50 words.
    Write only the important points no fluff. Try to include exact wordings inside double quote if something informative has been said.
    The output must be in json format starting and trailing  with triple backtics.
    {{
    "title": "Title of the video",
    "notes": [
        "Point 1",
        "Point 2",
        "Point 3"
    ]
    }}
    Here is the transcription of the video:
    {text1}
    Here are the concise notes:
    """
    response = llm.invoke(prompt)
    json_response = json.loads(
        str(response.content.strip().strip("```").strip("```json"))
    )
    return json_response
