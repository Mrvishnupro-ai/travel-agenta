import streamlit as st
import os
from dotenv import load_dotenv
from portia import (
    Config,
    DefaultToolRegistry,
    LLMProvider,
    LogLevel,
    Portia,
    StorageClass,
    ActionClarification,
    PlanRunState,
)
from portia.cli import CLIExecutionHooks
from portia.open_source_tools.browser_tool import BrowserTool, BrowserInfrastructureOption
from portia import open_source_tool_registry

st.set_page_config(
    layout="wide",
    page_title="Travel Agenta"
)
 
if 'api_keys_submitted' not in st.session_state:
    st.session_state.api_keys_submitted = False

# API Key Input Sidebar
with st.sidebar:
    st.title("API KEYS")
    st.write("Please enter your API keys to proceed.")
    
    portia_api_key = st.text_input("PORTIA API KEY*", type="password")
    gemini_api_key = st.text_input("GEMINI API KEY*", type="password")
    tavily_api_key = st.text_input("TAVILY API KEY*", type="password")

    if st.button("Submit"):
        if portia_api_key and gemini_api_key:
            st.session_state.portia_api_key = portia_api_key
            st.session_state.gemini_api_key = gemini_api_key
            st.session_state.tavily_api_key = tavily_api_key
            st.session_state.api_keys_submitted = True
            st.success("API Keys submitted successfully!")
            st.rerun()
        else:
            st.error("Please provide both Portia and Gemini API keys.")

# Main Application
if st.session_state.api_keys_submitted:
    st.title("🌍TRAVEL AGENTA")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.header("Plan Your Trip")

        form_col1, form_col2 = st.columns(2)
        
        with form_col1:
            origin = st.text_input("FROM", "New York")
            start_date = st.text_input("START DATE", "15 Oct 2025")
            duration = st.text_input("DURATION", "7 days")

        with form_col2:
            destination = st.text_input("TO", "Paris")
            return_date = st.text_input("RETURN DATE", "22 Oct 2025")
            budget = st.text_input("BUDGET", "Approx $2000")

        st.markdown("---")

        trip_type = st.radio("TRIP TYPE", ["Solo", "Family", "Friends", "Business"], horizontal=True)
        accommodation = st.radio("ACCOMMODATION", ["Budget", "Luxury", "Flexible"], horizontal=True)
        food_preferences = st.radio("FOOD PREFERENCES", ["Veg", "Non Veg", "Flexible"], horizontal=True)

        st.markdown("---")

        activities = st.text_input("ACTIVITIES", "Museums, historic sites, local cuisine tours")
        emails_input = st.text_input("EMAILS", "veerarohit789@gmail.com")
        custom_instructions = st.text_area("CUSTOM INSTRUCTIONS", "Focus on cultural experiences and avoid tourist traps. Include at least one day trip outside the main city.")

        if st.button("GENERATE A PLAN", use_container_width=True):
            required_fields = {
                "Origin": origin,
                "Destination": destination,
                "Start Date": start_date,
                "Return Date": return_date,
                "Duration": duration,
                "Budget": budget,
                "Emails": emails_input
            }

            os.environ["PORTIA_API_KEY"] = st.session_state.portia_api_key
            os.environ["GEMINI_API_KEY"] = st.session_state.gemini_api_key
            os.environ["TAVILY_API_KEY"] = st.session_state.tavily_api_key

            missing = [field for field, value in required_fields.items() if not value.strip()]

            if missing:
                st.error(f"⚠ Please fill all required fields: {', '.join(missing)}")
                st.stop()

            emails = [email.strip() for email in emails_input.split(',')]
            
            load_dotenv()

            task = f"""
            Make a Travel Plan with the following details:
            - Origin: {origin} - Destination: {destination} - Start Date: {start_date} - Return Date: {return_date}
            - Duration: {duration} - Trip Type: {trip_type} - Budget: {budget} - Accommodation Preference: {accommodation}
            - Activities & Interests: {activities} - Dining Preferences: {food_preferences} - Custom Instructions: {custom_instructions}
            - Expected Final Output: A detailed day-by-day itinerary, travel options, and recommendations.
            - Once the plan is generated, email a comprehensive report to the following addresses: {", ".join(emails)}.
            - Add this events in calender.
            - Send calender invitation to this emails {emails} 
            """

            try:
                my_config = Config.from_default(
                    llm_provider=LLMProvider.GOOGLE, storage_class=StorageClass.CLOUD,
                    storage_dir="./production_states", default_log_level=LogLevel.DEBUG,
                    default_log_sink="./agent_audit.log", json_log_serialize=True,
                )

                portia = Portia(
                    config=my_config,
                    tools=DefaultToolRegistry(my_config) + open_source_tool_registry + [
                        BrowserTool(infrastructure_option=BrowserInfrastructureOption.REMOTE)
                    ],
                    execution_hooks=CLIExecutionHooks(),
                )
                
                with col2:
                    plan_steps_container = st.container()
                    final_output_container = st.container()

                    with plan_steps_container:
                        st.header("PLAN STEPS")
                        with st.spinner('Agent is generating the plan...'):
                            plan = portia.plan(task)
                            st.text_area("Generated Plan Steps", plan.pretty_print(), height=300, key="plan_steps_output") # <-- ADDED KEY
                            st.session_state.plan_output = plan.pretty_print()

                    with final_output_container:
                        st.header("FINAL OUTPUT")
                        with st.spinner('Agent is executing the plan and mailing the report...'):
                            plan_run = portia.run_plan(plan, end_user="Streamlit User")
                            
                            final_summary = (
                                f"Plan successfully executed!\n\nA detailed travel itinerary for your {trip_type} trip "
                                f"from {origin} to {destination} has been generated and sent to: {emails_input}."
                            )
                            st.text_area("Execution Summary", final_summary, height=150, key="final_output_summary") # <-- ADDED KEY
                            st.session_state.final_output = final_summary

            except Exception as e:
                st.error(f"An error occurred: {e}")


else:
    st.info("⬅ Please enter your API keys in the sidebar to start planning your trip.")