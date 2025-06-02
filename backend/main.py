import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
import json
from backend.agents.pydantic_agents import basic_communication_agent
from backend.agents.langgraph_agent import LangGraphClass
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from backend.api.ppt_upload import router as ppt_router

import platform
import os

from dotenv import load_dotenv

load_dotenv()

PG_URL = os.getenv("PG_URL")

# 1. Make sure you do this before any async code runs
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def handle_client_offer(offer_sdp: str) -> str:
    """
    Handle the client's WebRTC offer for audio capture and return the server's SDP answer.

    Args:
        offer_sdp (str): The Session Description Protocol (SDP) offer from the client.

    Returns:
        str: The SDP answer from the server.
    """
    # Create a new RTCPeerConnection
    pc = RTCPeerConnection()

    # Set the remote description with the client's offer
    await pc.setRemoteDescription(RTCSessionDescription(sdp=offer_sdp, type="offer"))

    # Create an answer to the offer
    answer = await pc.createAnswer()

    # Set the local description with the answer
    await pc.setLocalDescription(answer)

    # Return the SDP answer
    return pc.localDescription.sdp


import asyncio
import websockets
import requests

# Global variable to store WebSocket connections
connected_clients = set()

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
import asyncio
from fastapi import File, UploadFile, Form

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # e.g. ["http://localhost:3000"] if it's a single frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

connected_clients = dict()

# create a session object and save it to the database
from backend.database.base import get_db
from fastapi import Depends
from backend.models import Session, User, Website
from sqlalchemy.orm import Session as SQLAlchemySession


def create_website(
    db: SQLAlchemySession = Depends(get_db),
    site_id: int = 0,
):
    """
    Create a new website in the database.
    """
    existing_website = db.query(Website).filter(Website.site_id == site_id).first()
    if existing_website:
        return existing_website

    new_website = Website(site_id=site_id, name="My Website")
    db.add(new_website)
    db.commit()
    db.refresh(new_website)
    return new_website


def create_session(
    db: SQLAlchemySession = Depends(get_db),
    site_id: int = 0,
    user_id: int = 0,
    conversation_id: str = None,
):
    """
    Create a new session in the database.
    """
    new_session = Session(site_id=site_id, user_id=user_id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


def create_user(
    db: SQLAlchemySession = Depends(get_db),
    site_id: int = 0,
    client_id: str = None,
):
    """
    Create a new user in the database.
    """
    if client_id:
        existing_user = db.query(User).filter(User.client_id == client_id).first()
        if existing_user:
            return existing_user

        new_user = User(client_id=client_id, site_id=site_id)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user


from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from backend.models import Meeting
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # e.g. ["http://localhost:3000"] if it's a single frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import requests
from fastapi import HTTPException

CALENDLY_API_BASE_URL = "https://api.calendly.com"
CALENDLY_ACCESS_TOKEN = os.getenv("CALENDLY_TOKEN")


memory_saver = MemorySaver()
PG_URL = f"postgresql://{os.getenv('PGUSER')}:{os.getenv('PGPASSWORD')}@{os.getenv('PGHOST')}:{os.getenv('PGPORT')}/{os.getenv('PGDATABASE')}"


@router.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Accept the WebSocket connection
    await websocket.accept()
    websocket.ping_timeout = 3600

    client_id = None  # Initialize client_id to None
    conversation_id = None  # Initialize client_id to None

    async with AsyncConnectionPool(
        # Example configuration
        conninfo=PG_URL,
        max_size=20,
        min_size=1,
        # to be remove
        kwargs={"autocommit": True},
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        # NOTE: you need to call .setup() the first time you're using your checkpointer
        await checkpointer.setup()

        try:
            initial_message = await websocket.receive_text()
            data = json.loads(initial_message)

            # Extract the client_id from the initial message
            client_id = data.get("client_id")
            conversation_id = data.get("conversation_id")
            if not client_id:
                await websocket.send_text(
                    json.dumps({"error": "client_id is required"})
                )
                await websocket.close()
                return

            # Add the WebSocket connection to the connected_clients dictionary
            connected_clients[client_id] = websocket
            print(f"Client connected: {client_id}")

            # ANALYTICS
            payload = {
                "user_id": client_id,
                "project_name": "smoothai",
                "conversation_id": conversation_id,
            }
            try:
                response = requests.post(
                    f"{os.environ.get('NEXT_PUBLIC_API_URL')}/talk-time", json=payload
                )
                # response.raise_for_status()
                # Optionally, inspect the JSON result if needed
                # return response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error starting talk-time: {e}")
                # return None  # or raise an exception, depending on your needs

            # Send a welcome message to the client
            # await websocket.send_text(
            #     json.dumps({"type": "normal_chat", "message": ""})
            # )

            # await websocket.send_text(
            #     json.dumps(
            #         {
            #             "type": "normal_chat",
            #             "message": "Welcome to Smooth AI! 🚀 My name is Sophie. I'm your AI Advisor, here to help you convert more leads with AI-driven conversations. May I know your name?",
            #         }
            #     )
            # )
        except Exception as e:
            print(f"Error receiving initial message: {e}")
            await websocket.close()
            return

        # Create or fetch the user
        db = get_db()

        # create a website, one time only
        website = create_website(site_id=1, db=db)
        user = create_user(
            db=db,
            site_id=website.site_id,
            client_id=client_id,
        )

        # create session
        session = create_session(
            db=db,
            site_id=user.site_id,
            user_id=user.user_id,
            conversation_id=conversation_id,
        )
        langgraph_class = LangGraphClass(
            memory=checkpointer,
            user_id=user.user_id,
            session_id=session.session_id,
            websocket_object=websocket,
        )
        graph = langgraph_class.build_graph()

        # send first message, by saying automatic hi to graph
        first_time = True

        # Receive the initial message to get the client identifier
        try:

            # Handle communication with the client
            while True:
                if first_time:
                    from time import sleep

                    # sleep(5)
                    response = {
                        "type": "normal_mode",
                        "message": "Hey you my sweet pregnant lady. You have come to the right place!",
                        "presentation_urls": "",
                        "pricing_page_url": "",
                    }

                    # print("response from backend is ", response)
                    await websocket.send_text(json.dumps(response))
                    first_time = False

                message = await websocket.receive_text()
                # Parse the JSON message
                data = json.loads(message)

                # store meeting in database
                if "type" in data and data["type"] == "meeting_data":
                    meeting_start_time = (
                        data["meeting_start_time"]
                        if "meeting_start_time" in data
                        else None
                    )
                    meeting_end_time = (
                        data["meeting_end_time"] if "meeting_end_time" in data else None
                    )
                    date = data["date"] if "date" in data else None
                    meeting_link = (
                        data["meeting_link"] if "meeting_link" in data else None
                    )

                    # Query the Users table for the user with the provided email
                    meeting = Meeting(
                        session_id=session.session_id,
                        meeting_link=meeting_link,
                        scheduled_for=meeting_start_time,
                    )
                    db.add(meeting)
                    db.commit()

                #################
                # print("user message here is ", data["message"])

                ########## calling langgraph agent ##########
                user_input = data["message"]
                config = {"configurable": {"thread_id": data["client_id"]}}

                response = graph.astream(
                    {
                        "messages": [HumanMessage(role="user", content=user_input)],
                    },
                    config,
                    stream_mode="values",
                )

                LLM_response = None
                response_type = None
                urls = None
                async for event in response:
                    messages = event.get("messages", [])
                    ai_messages = [
                        msg for msg in messages if isinstance(msg, AIMessage)
                    ]
                    if ai_messages:
                        LLM_response = ai_messages[-1].content

                    response_type = (
                        event.get("ui_mode").value
                        if event.get("ui_mode")
                        else "normal_mode"
                    )
                    # response_type = "normal_mode"

                    # Extract ppt_url from the last event where it is available
                    presentation_urls = event.get("ppt_url", None)
                    pricing_page_url = event.get("pricing_page_url", None)

                response = {
                    "type": response_type,
                    "message": LLM_response,
                    "presentation_urls": presentation_urls,
                    "pricing_page_url": pricing_page_url,
                }

                # print("response from backend is ", response)
                await websocket.send_text(json.dumps(response))

        except Exception as e:
            print(f"Error with client {client_id}: {e}")
        finally:
            # Remove the client from the connected_clients dictionary
            if client_id in connected_clients:
                del connected_clients[client_id]
            print(f"Client disconnected: {client_id}")

            # ANALYTICS
            payload = {
                "user_id": client_id,
                "project_name": "smoothai",
                "conversation_id": conversation_id,
            }
            try:
                response = requests.post(
                    f"{os.environ.get('NEXT_PUBLIC_API_URL')}/talk-time/end",
                    json=payload,
                )
                # response.raise_for_status()
                # Optionally, inspect the JSON result if needed
                # return response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error ending talk-time: {e}")
                # return None  # or raise an exception, depending on your needs


app.include_router(router)
app.include_router(ppt_router, prefix="/api/ppt", tags=["ppt"])

# Run the app using: `uvicorn this_module_name:app --host localhost --port 8765`

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
