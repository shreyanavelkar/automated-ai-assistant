from uuid import UUID, uuid4

import uvicorn
from autogen_core import DefaultTopicId
from autogen_ext.models.openai import OpenAIChatCompletionClient
from fastapi import FastAPI, HTTPException, Depends
from fastapi.openapi.models import Response
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.frontends.implementations import CookieParameters, SessionCookie

from automated_ai_assistant.agent.utils import load_api_key
from automated_ai_assistant.model.data_types import EndUserMessage, SessionData, ChatRequest
from automated_ai_assistant.oltp_tracing import logger
from automated_ai_assistant.session_verifier import BasicVerifier
from automated_ai_assistant.utils.runtime_utils import initialize_agent_runtime

app = FastAPI()


@app.get("/")
def check_health():
    return "Alive"


cookie_params = CookieParameters()

cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",
    cookie_params=cookie_params,
)

backend = InMemoryBackend[UUID, SessionData]()

verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)


@app.post("/create_session/{name}")
async def create_session(name: str, response: Response):
    session = uuid4()
    data = SessionData(username=name)

    await backend.create(session, data)
    cookie.attach_to_response(response, session)

    return f"created session for {name}"


@app.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(session_data: SessionData = Depends(verifier)):
    return session_data


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        api_key = load_api_key()
        model_client = OpenAIChatCompletionClient(
            api_key=api_key,
            model="gpt-4",
            temperature=0.2
        )
        runtime = await initialize_agent_runtime(model_client=model_client)

        response = await runtime.publish_message(
            message=EndUserMessage(content=request.message, source="user"),
            topic_id=DefaultTopicId(type="chat_agent")
        )
        await runtime.stop_when_idle()

        return response

    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        return "Failed to handle message."


@app.post("/delete_session")
async def del_session(response: Response, session_id: UUID = Depends(cookie)):
    await backend.delete(session_id)
    cookie.delete_from_response(response)
    return "deleted session"


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
