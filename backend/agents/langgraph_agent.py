from typing import Annotated


from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing_extensions import TypedDict
import os
import json
import asyncio
from enum import Enum
from uuid import UUID

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic_ai import RunContext
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import Optional, Dict
from fastapi import WebSocket
import psycopg2

from backend.agents.openai_chat_completion import deephermes_free
from backend.vector_search import PineconeSearch
from backend.models import User, Meeting, PresentationURL, Session, Summary
from backend.database.base import get_db


from PIL import Image, ImageDraw, ImageFont
import os
from tempfile import NamedTemporaryFile
from fastapi.responses import FileResponse

#######################
from dotenv import load_dotenv

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
#########################

PINE_API_KEY = os.getenv("PINE_API_KEY")
PINE_INDEX_NAME = os.getenv("PINE_INDEX_NAME")

#########################
PRICING_PAGE_URL = os.getenv("PRICING_PAGE_URL", "https://smooth.ai/pricing")

GROWTH_PLAN_DEMO = os.getenv(
    "GROWTH_PLAN_DEMO", "https://app.heygen.com/share/f512ed4186bc42c89647ad9f155c7447s"
)

##########################
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_EMAIL_PASSWORD = os.getenv("SENDER_EMAIL_PASSWORD")


db_connection = get_db()


class PPTSharingState(Enum):
    NORMAL_MODE = "normal_mode"
    PPT_MODE = "ppt_mode"


class UIMode(Enum):
    NORMAL_MODE = "normal_mode"
    ASK_FOR_MEETING = "ask_for_meeting"
    PPT_MODE = "ppt_mode"
    GOTO_PAGE_MODE = "goto_page_mode"


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]

    context: str
    prompt: str
    response: str
    sent_to_postgres: bool
    ppt_sharing_state: PPTSharingState  # Add this field
    went_to_pricing: bool  # Track if the user visited the pricing page
    ui_mode: UIMode  # Track the current UI mode
    ppt_url: Optional[str]  # URL for the presentation
    pricing_page_url: Optional[str]  # URL for the pricing page


pinecone_search = PineconeSearch(api_key=PINE_API_KEY, index_name=PINE_INDEX_NAME)


class LangGraphClass:
    def __init__(
        self,
        memory: MemorySaver,
        user_id: str,
        session_id: str,
        websocket_object: WebSocket,
    ):
        self.state = GraphState(
            messages=[],
            context=None,
            prompt=None,
            response=None,
            user_details=None,
            sent_to_postgres=False,
            ppt_sharing_state=PPTSharingState.NORMAL_MODE,
            ppt_url=None,
            pricing_page_url=None,
            went_to_pricing=False,
            ui_mode=UIMode.NORMAL_MODE,
        )
        self.memory = memory
        self.user_id = user_id if user_id else None
        self.session_id = session_id if session_id else None
        self.can_trigger_tool_counter = 0
        self.tools_used = []
        self.refresh_states = True

        self.websocket_object = websocket_object

    def refresh_all_states(self, state: GraphState):
        state["context"] = None
        state["ui_mode"] = UIMode.NORMAL_MODE
        state["ppt_sharing_state"] = PPTSharingState.NORMAL_MODE
        state["went_to_pricing"] = False

        state["ppt_url"] = None
        state["pricing_page_url"] = None
        state["pricing_page_url"] = None
        state["messages"] = add_messages(
            state["messages"],
            AIMessage(content="Hi there!"),
        )

        return state

    async def refresh_all_state_node(self, state: GraphState) -> GraphState:
        """Handles chatbot responses using pydantic_ai LLM."""
        if self.refresh_states:
            state = self.refresh_all_states(state)
            self.refresh_states = False

        return state

    async def chatbot_node_with_trigger_tools(self, state: GraphState) -> GraphState:
        """Handles chatbot responses using pydantic_ai LLM."""

        user_prompt = next(
            (
                msg
                for msg in reversed(state["messages"])
                if isinstance(msg, HumanMessage)
            ),
            None,
        )
        if self.refresh_states:
            state = self.refresh_all_states(state)
            self.refresh_states = False

        # if "context" in state and state["context"]:
        #     print("Using context", state["context"])
        #     context = state["context"]
        # else:

        #     print("No context found, searching for context", user_prompt)
        context = pinecone_search.search(
            query=user_prompt.content, requires_embedding=True, top_k=5
        )
        state["context"] = context
        # print("Context retrieved", context)

        use_tool = False

        if self.can_trigger_tool_counter > 3:
            use_tool = True

        tools = []

        next_tool_to_use = [tool for tool in [] if tool not in self.tools_used]
        next_tool_to_use = next_tool_to_use[0] if next_tool_to_use else None

        system_prompt = f"""

##PERSONA:
Your goal is to engage potential clients, understand their needs, and provide detailed information about the product and related offerings. You can achieve your goal in the conversation by following Conversation Flow and Tool Usage.



You can present information for the product.

List of tools | trigger
_______________________
{tools}

Already used tools:
{self.tools_used}

Tool to use:
{next_tool_to_use}

For these , go to tools, but only when relevant, lead the conversation naturally towards all of the above tools. If not asked directly for any tool, try to ask and use the {next_tool_to_use} if {use_tool} is true.

Additonal_Instructions
When interacting with users:
1. Maintain a natural and fluid conversation, responding appropriately to their queries and interests.
"""

        self.can_trigger_tool_counter += 1

        # Combine the system prompt and user prompt into a single string
        History = " ".join([msg.content for msg in state["messages"][-50:-1]])
        context_text = " ".join(text["metadata"]["chunk_text"] for text in context)
        combined_prompt = (
            f"Context:{context_text}\n\n{system_prompt}\n\nHistory:{History}"
        )

        # Pass only the combined prompt as a string to the agent
        chat_response = deephermes_free(
            role="assistant", content=combined_prompt + user_prompt.content
        )

        state["messages"].append(AIMessage(role="assistant", content=chat_response))
        return state

    async def update_retrieved_context(self, state: GraphState) -> GraphState:
        """Updates the context with the retrieved data, if the new user inputs are not related to the stored context."""

        state["context"] = pinecone_search.hybrid_search(state["messages"], top_k=1)

        return state

    def get_presentation_url(self, type_url: str = "pricing") -> str:
        """
        Returns the URL of the presentation based on the type.
        """
        # get from db, using Table PresentationURL
        presentation = (
            db_connection.query(PresentationURL)
            .filter(PresentationURL.url_type == type_url)
            .first()
        )
        if presentation:
            return presentation.url
        else:
            print(f"No presentation found for type: {type_url}")
            return None

    def create_presentation_image(self, presentation_text: str) -> str:
        """
        Creates a presentation image with the given text.
        """
        # Create an image with white background
        img = Image.new("RGB", (800, 600), color=(135, 206, 235))
        d = ImageDraw.Draw(img)

        # Load default font
        font = ImageFont.load_default()

        # Add text to image
        # Get the size of the text
        # Calculate the size of the text
        text_width, text_height = d.multiline_textbbox(
            (0, 0), presentation_text, font=font
        )

        # Calculate the x and y coordinates to centre the text
        x = (img.width - text_width) / 2
        y = (img.height - text_height) / 2

        # Add the text to the image
        d.text((x, y), presentation_text, fill=(0, 0, 0), font=font)

        # Save the image temporarily
        with NamedTemporaryFile(
            delete=False, suffix=".png", dir="static/uploads"
        ) as tmp:
            img.save(tmp, format="PNG")
            image_path = tmp.name
            base_url = "http://localhost:8000"
            file_url = f"{base_url}/api/ppt/media/{os.path.basename(image_path)}"
        return file_url

    async def generic_ppt_sharing_tool(self, state: GraphState) -> GraphState:
        """
        Node to handle PPT sharing using a state-driven approach.
        Decides the presentation type based on conversation history.
        """

        # Transition to PPT Mode
        state["ppt_sharing_state"] = PPTSharingState.PPT_MODE

        # Use AI to determine the type of presentation text to create
        history = " ".join(
            [
                message.content
                for message in state["messages"]
                if isinstance(message, HumanMessage)
            ][-50:]
        )

        # Determine presentation type based on history
        prompt = f"Analyze the following conversation history to determine the most suitable presentation type and generate the corresponding presentation text in less than 700 characters: {history}"

        response = deephermes_free(role="assistant", content=prompt)
        presentation_text = response.data

        # Create and save the presentation image
        presentation_image_path = self.create_presentation_image(presentation_text)

        # Update the state with the presentation image URL and message
        state["ppt_url"] = presentation_image_path
        state["ui_mode"] = UIMode.PPT_MODE
        state["messages"] = add_messages(
            state["messages"],
            AIMessage(
                content=f"Presentation created and available at: {presentation_image_path}"
            ),
        )
        return state

    def determine_tool(self, state: GraphState) -> str:
        """
        Determines which tool to activate based on the latest AI message content.
        """
        # print("Determining tool to activate...", state["messages"])

        # Get the latest AI message
        ai_message = (
            state["messages"][-1]
            if isinstance(state["messages"][-1], AIMessage)
            else None
        )

        if not ai_message:
            state["messages"] = add_messages(
                state["messages"],
                AIMessage(
                    content="I'm sorry, I didn't understand that. Can you repeat?"
                ),
            )
            return END  # Default to END if no valid AI message is found

        # Extract the content of the AI message
        content = ai_message.content.lower()

        if "ppt_sharing" in content:
            return "ppt_sharing"

        return END

    def build_graph(self) -> StateGraph:
        graph_builder = StateGraph(GraphState)
        graph_builder.add_node("chatbot", self.chatbot_node_with_trigger_tools)

        tools = [self.update_retrieved_context]
        tool_node = ToolNode(tools=tools)

        graph_builder.add_edge(START, "chatbot")

        graph_builder.add_node("tools", tool_node)

        graph_builder.add_node("ppt_sharing", self.generic_ppt_sharing_tool)
        graph_builder.add_edge("tools", "ppt_sharing")

        graph_builder.add_conditional_edges(
            "chatbot",
            self.determine_tool,  # Use the unified condition node
            {
                "ppt_sharing": "ppt_sharing",
                END: END,
            },
        )

        graph_builder.add_edge("chatbot", END)

        graph = graph_builder.compile(checkpointer=self.memory)

        return graph
