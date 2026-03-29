from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm # For multimodel support
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts
import asyncio
from dotenv import load_dotenv
from greeting_agent import greeting_agent, farewell_agent
from litellm import query
from google.adk.tools.tool_context import ToolContext
load_dotenv()

# Use one of the model constants defined earlier
MODEL_GEMINI_2_0_FLASH = "gemini-3-flash-preview"
root_agent = None
runner_root = None # Initialize runner


def get_weather_stateful(city: str, tool_context: ToolContext) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city (e.g., "New York", "London", "Tokyo").

    Returns:
        dict: A dictionary containing the weather information.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """
    print(f"--- Tool: get_weather_stateful called for city: {city} ---") # Log tool execution
    city_normalized = city.lower().replace(" ", "") # Basic normalization

    preferred_unit = tool_context.state.get("user_preference_temperature_unit", "Celsius") # Default to Celsius
    # Mock weather data
    mock_weather_db = {
        "newyork": {"temp_c": 25, "condition": "sunny"},
        "london": {"temp_c": 15, "condition": "cloudy"},
        "tokyo": {"temp_c": 18, "condition": "light rain"},
    }

    if city_normalized in mock_weather_db:
        data = mock_weather_db[city_normalized]
        temp_c = data["temp_c"]
        condition = data["condition"]

        # format temperateure based on user preference in session state

        if preferred_unit == 'Fahrenheit':
            temp_value = temp_c * 9/5 + 32
            temp_unit = '°F'
        else:
            temp_value = temp_c
            temp_unit = '°C'
        report = f"The weather in {city} is {condition} with a temperature of {temp_value:.0f}{temp_unit}."
        result = {"status": "success", "report": report}
        tool_context.state["last_city_checked_stateful"] = city
        return result
    else:
        error_msg = f"Sorry, I don't have weather information for '{city}'."
        print(f"--- Tool: City '{city}' not found. ---")
        return {"status": "error", "error_message": error_msg}
print("✅ State-aware 'get_weather_stateful' tool defined.")



if greeting_agent and farewell_agent and 'get_weather_stateful' in globals():
    # Let's use a capable Gemini model for the root agent to handle orchestration
    root_agent_model = MODEL_GEMINI_2_0_FLASH

    root_agent_stateful = Agent(
        name="weather_agent_v4_stateful", # Give it a new version name
        model=root_agent_model,
        description="The main coordinator agent. Handles weather requests and delegates greetings/farewells to specialists.",
        instruction="You are the main Weather Agent. Your job is to provide weather using 'get_weather_stateful'. "
                    "The tool will format the temperature based on user preference stored in state. "
                    "Delegate simple greetings to 'greeting_agent' and farewells to 'farewell_agent'. "
                    "Handle only weather requests, greetings, and farewells.",
        tools=[get_weather_stateful], # Root agent still needs the weather tool for its core task
        # Key change: Link the sub-agents here!
        sub_agents=[greeting_agent, farewell_agent],
        output_key="last_weather_report",
    )
    print(f"✅ Root Agent '{root_agent_stateful.name}' created using model '{root_agent_model}' with sub-agents: {[sa.name for sa in root_agent_stateful.sub_agents]}")

else:
    print("❌ Cannot create root agent because one or more sub-agents failed to initialize or 'get_weather' tool is missing.")
    if not greeting_agent: print(" - Greeting Agent is missing.")
    if not farewell_agent: print(" - Farewell Agent is missing.")
    if 'get_weather' not in globals(): print(" - get_weather function is missing.")

root_agent = root_agent_stateful
session_service = InMemorySessionService()
APP_NAME = "weather_tutorial_app"
USER_ID = "user_1"
SESSION_ID = "session_001_agent_team"


print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")

async def init_session(app_name: str, user_id: str, session_id: str):

    """Initializes a session for the agent."""
    session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )
    print(f"Session initialized: App='{app_name}', User='{user_id}', Session='{session_id}'")
    return session

async def call_agent_async(query: str, runner, user_id, session_id):
    """Calls the agent with a user query and prints the response."""
    print(f"Calling agent with query: '{query}'")
      # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=query)])
    final_response_text = "Agent did not produce a final response." # Default

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = f"Agent escalated: {event.error_message or 'No error message provided.'}" 
            break
    print(f"Final response from agent: '{final_response_text}'")

root_agent_var_name = 'root_agent' 

if 'weather_agent_v4_stateful' in globals(): # Check if user used this name instead
    root_agent_var_name = 'weather_agent_v4_stateful'
elif 'root_agent' not in globals():
    print("⚠️ Root agent ('root_agent' or 'weather_agent_v4_stateful') not found. Cannot define run_team_conversation.")
    # Assign a dummy value to prevent NameError later if the code block runs anyway
    root_agent = None # Or set a flag to prevent execution


if root_agent_var_name in globals() and globals()[root_agent_var_name]:
    # Define the main async function for the conversation logic.
    # The 'await' keywords INSIDE this function are necessary for async operations.
    async def run_stateful_conversation():
        print("\n--- Testing Agent Team Delegation ---")
        session_service = InMemorySessionService()
        APP_NAME = "weather_tutorial_agent_team"
        USER_ID = "user_1_agent_team"
        SESSION_ID = "session_001_agent_team"
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )
        print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")

        actual_root_agent = globals()[root_agent_var_name]
        runner_root_stateful = Runner( # Or use InMemoryRunner
            agent=actual_root_agent,
            app_name=APP_NAME,
            session_service=session_service
        )
        print(f"Runner created for agent '{actual_root_agent.name}'.")

        # --- Interactions using await (correct within async def) ---
        await call_agent_async(query = "What's the weather in London?",
                               runner=runner_root_stateful,
                               user_id=USER_ID,
                               session_id=SESSION_ID)
        try:
            # Access the internal storage directly - THIS IS SPECIFIC TO InMemorySessionService for testing
            # NOTE: In production with persistent services (Database, VertexAI), you would
            # typically update state via agent actions or specific service APIs if available,
            # not by direct manipulation of internal storage.
            stored_session = session_service.sessions[APP_NAME][USER_ID][SESSION_ID]
            stored_session.state["user_preference_temperature_unit"] = "Fahrenheit"
            # Optional: You might want to update the timestamp as well if any logic depends on it
            # import time
            # stored_session.last_update_time = time.time()
            print(f"--- Stored session state updated. Current 'user_preference_temperature_unit': {stored_session.state.get('user_preference_temperature_unit', 'Not Set')} ---") # Added .get for safety
        except KeyError:
            print(f"--- Error: Could not retrieve session '{SESSION_ID}' from internal storage for user '{USER_ID}' in app '{APP_NAME}' to update state. Check IDs and if session was created. ---")
        except Exception as e:
             print(f"--- Error updating internal session state: {e} ---")
        print("\n--- Turn 2: Requesting weather in New York (expect Fahrenheit) ---")
        await call_agent_async(query= "Tell me the weather in New York.",
                               runner=runner_root_stateful,
                               user_id=USER_ID,
                               session_id=SESSION_ID
                              )
        print("\n--- Turn 3: Sending a greeting ---")
        await call_agent_async(query= "Hi!",
                               runner=runner_root_stateful,
                               user_id=USER_ID,
                               session_id=SESSION_ID
                              )


async def main():
    session = await init_session(APP_NAME,USER_ID,SESSION_ID)

    runner = Runner(
        agent=root_agent,
        session_service=session_service,
        app_name=APP_NAME,
    )
    await call_agent_async("What's the weather like in New York?", runner, USER_ID, SESSION_ID)
    await call_agent_async("How about Paris?", runner, USER_ID, SESSION_ID)
    await call_agent_async("Can you tell me the weather in Tokyo?", runner, USER_ID, SESSION_ID)

    print(f"Runner created for agent '{runner.agent.name}'.")







if __name__ == "__main__": # Ensures this runs only when script is executed directly
    print("Executing using 'asyncio.run()' (for standard Python scripts)...")
    try:
        # This creates an event loop, runs your async function, and closes the loop.
        asyncio.run(run_stateful_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")