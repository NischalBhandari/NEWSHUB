from google.adk.sessions import InMemorySessionService
import asyncio

async def main():

    session_service_stateful = InMemorySessionService()
    APP_NAME = "news_app"
    SESSION_ID_STATEFUL = "session_state_demo_001"
    USER_ID_STATEFUL = "user_state_demo_001"

    initial_state = {
        "user_preference_temperateure_unit": "Celsius",
    }

    session_stateful = await session_service_stateful.create_session(
        app_name="news_app",
        user_id=USER_ID_STATEFUL,
        session_id=SESSION_ID_STATEFUL,
        state=initial_state
    )
    print(f"✅ Session '{SESSION_ID_STATEFUL}' created for user '{USER_ID_STATEFUL}'.")

    # Verify the initial state was set correctly
    retrieved_session = await session_service_stateful.get_session(app_name=APP_NAME,
                                                            user_id=USER_ID_STATEFUL,
                                                            session_id=SESSION_ID_STATEFUL
                                                    )
    

asyncio.run(main())

