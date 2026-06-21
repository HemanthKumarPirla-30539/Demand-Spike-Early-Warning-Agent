import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
import json

from dotenv import load_dotenv
load_dotenv()

# --- IMPORTS for sending real email ---
import requests
# --- END NEW IMPORTS ---

# --- Title for your App ---
st.set_page_config(page_title="Autonomous Agent V5", page_icon="🤖") 
st.title("🤖 Autonomous Sales Agent V5 (Demo Ready)")
st.caption("This AI agent can analyze sales and *autonomously* send email alerts.")

# --- NEW: FUNCTION TO RESET THE FORM ---
def clear_form():
    # We can't reset the file_uploader, but we can reset everything else!
    st.session_state["recipient_email"] = ""
    st.session_state["business_context"] = ""
    st.session_state["alert_slider"] = 25
    st.session_state["slump_checkbox"] = False
    st.session_state["slump_slider"] = 25
    if "auto_send_checkbox" in st.session_state:
        st.session_state["auto_send_checkbox"] = False
# --- END NEW FUNCTION (NOW CORRECTED) ---

# --- UPDATED: RESET BUTTON ---
if st.button("Reset Demo", use_container_width=True, type="secondary", on_click=clear_form):
    pass # The on_click handles all the logic
st.markdown("---")
# --- END UPDATED SECTION ---

# --- SECURE: Get API Key from Streamlit Secrets ---
try:
    API_KEY = os.getenv("GEMINI_API_KEY")
    
except FileNotFoundError:
    st.error("CRITICAL ERROR: Could not find .streamlit/secrets.toml file.")
    st.info("Please create this file and add your GEMINI_API_KEY.")
    st.stop()
except KeyError:
    st.error("CRITICAL ERROR: 'GEMINI_API_KEY' not found in secrets.toml.")
    st.info("Please add your Gemini API key to the .streamlit/secrets.toml file.")
    st.stop()

# Configure the API
try:
    genai.configure(api_key=API_KEY)
    
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    st.error(f"Error configuring API: {e}")
    st.stop()
# --- END SECURE KEY SECTION ---


# --- FUNCTION: The Email Sender ---
def send_email(recipient_email, subject, body):
    try:
        BREVO_API_KEY = os.getenv("BREVO_API_KEY")
        st.write("Brevo Key Exists:", BREVO_API_KEY is not None)
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }

        payload = {
            "sender": {
                "name": "Hemanth",
                "email": "hemanthkumaryadav260@gmail.com"
            },
            "to": [
                {
                    "email": recipient_email
                }
            ],
            "subject": subject,
            "htmlContent": f"<pre>{body}</pre>"
        }

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers=headers,
            json=payload
        )

        st.write("Status Code:", response.status_code)
        st.write("Response:", response.text)

        if response.status_code in [200, 201]:
            return True, "Email sent successfully!"
        else:
            return False, f"Brevo Error: {response.text}"

    except Exception as e:
        return False, str(e)
# --- END NEW FUNCTION ---


# --- Get User Input (File Uploader) ---
uploaded_file = st.file_uploader(
    "1. Upload your sales CSV file", 
    type=["csv"],
    key="file_uploader"
)

# --- Get Recipient Email ---
recipient_email = st.text_input(
    "2. Enter Recipient Email for Alert", 
    placeholder="e.g., ops-manager@coffeeshop.com",
    key="recipient_email"
)

# --- Get Business Context ---
business_context = st.text_input(
    "3. (Optional) Add any business context", 
    placeholder="e.g., 'Festive offer on cold drinks'",
    key="business_context"
)

# --- SPIKE THRESHOLD ---
alert_threshold = st.slider(
    "4. Set the Spike Threshold (%) 📈", 
    min_value=10, max_value=50, value=25, step=5,
    help="Warn if sales jump *above* this % of the 7-day average.",
    key="alert_slider"
)

# --- SLUMP DETECTION ---
warn_on_slump = st.checkbox(
    "5. Also warn about sales *slumps* (sudden drops)?",
    key="slump_checkbox"
)
slump_threshold = 25

if warn_on_slump:
    slump_threshold = st.slider(
        "Slump Threshold (%) 📉", 
        min_value=10, max_value=50, value=25, step=5,
        help="Warn if sales drop *below* this % of the 7-day average.",
        key="slump_slider"
    )

# --- AUTONOMOUS MODE CHECKBOX ---
st.markdown("---")
st.subheader("🚀 Take Action")

if not recipient_email:
    st.warning("Please enter a recipient email (Step 2) to enable alert actions.")
    auto_send = False
else:
    auto_send = st.checkbox(
        f"Send alert immediately to `{recipient_email}` without review",
        key="auto_send_checkbox"
    )
st.markdown("---")


if uploaded_file is not None:
    # Read the CSV file using pandas
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.lower()

        st.write("Columns Found:")
        st.write(df.columns.tolist())
        
        try:
            df['date'] = pd.to_datetime(df['date'])
        except Exception as e:
            st.warning(f"Could not parse dates. Charts may be incorrect. Error: {e}")
        
        with st.expander("Click to see Data Preview"):
            st.dataframe(df)
        
        with st.expander("Click to see All Sales Charts 📊"):
            unique_skus = df['sku'].unique()
            for sku in unique_skus:
                st.subheader(f"Sales Trend for: {sku}")
                sku_data = df[df['sku'] == sku].sort_values('date')
                st.line_chart(sku_data, x='date', y='sales')
        
        data_as_text = df.to_string()

        if st.button("Analyze Sales Velocity"):
            
            # --- Dynamically build prompt sections ---
            slump_instructions = ""
            spinner_text = f"AI is analyzing for spikes > {alert_threshold}%..."
            subject_text = f"SUBJECT: 🚨 URGENT: Demand Spike Warning (Threshold: {alert_threshold}%)"
            
            if warn_on_slump:
                slump_instructions = f"""
                - **Task 3 (Slumps):** Check for sales >{slump_threshold}% *below* the 7-day average. A "Slump" is >{slump_threshold}% sales *lower* than the 7-day moving average.
                """
                spinner_text = f"AI is analyzing for spikes (>{alert_threshold}%) and slumps (<{slump_threshold}%)..."
                subject_text = f"SUBJECT: 📈📉 Sales Velocity Alert (Spikes & Slumps Detected)"

            # --- PROMPT (asking for JSON) ---
            prompt = f"""
            You are a "Sales Velocity Analyst".
            Analyze the following sales DATA and consider the business CONTEXT.
            Respond with *ONLY* a JSON list of all spikes and slumps, wrapped in ```json ... ``` tags.
            If no issues are found, respond with an empty list: [].

            DATA:
            {data_as_text}

            CURRENT BUSINESS CONTEXT:
            {business_context}

            YOUR TASKS:
            1.  **Analyze Data:** Segregate by 'sku'.
            2.  **Task 2 (Spikes):** Check for sales >{alert_threshold}% *above* the 7-day average.
            {slump_instructions}

            JSON FORMAT FOR EACH ISSUE:
            {{
                "type": "spike" or "slump",
                "sku": "The SKU name",
                "location": "The location",
                "today_sales": "The most recent sales number",
                "avg_sales": "The calculated 7-day average",
                "change_pct": "The % increase or decrease",
                "cause": "Your suggested cause, using business context if relevant."
            }}
            """
            
            with st.spinner(spinner_text):
                try:
                    response = model.generate_content(prompt)
                    st.success("Analysis Complete!")
                    st.markdown("### 🤖 AI-Generated Visual Report")
                    
                    try:
                        json_text = response.text.strip().replace("```json", "").replace("```", "")
                        alerts = json.loads(json_text)
                        
                        email_body_text = "Hi Team,\n\nMy analysis is complete. Here are the findings:\n\n"
                        
                        if not alerts:
                            st.markdown("All SKUs are operating within normal sales velocity. No warnings to report.")
                            email_body_text += "All SKUs are operating within normal sales velocity. No warnings to report."
                        else:
                            for alert in alerts:
                                if alert['type'] == 'spike':
                                    st.markdown("---")
                                    st.markdown(f"### ⚠️ SPIKE WARNING (>{alert_threshold}%)")
                                    email_body_text += f"--- \n ⚠️ SPIKE WARNING (>{alert_threshold}%) \n"
                                else:
                                    st.markdown("---")
                                    st.markdown(f"### 📉 SLUMP WARNING (>{slump_threshold}%)")
                                    email_body_text += f"--- \n 📉 SLUMP WARNING (>{slump_threshold}%) \n"

                                # --- Display visual report in Streamlit ---
                                st.markdown(f"* **SKU:** `{alert['sku']}`")
                                st.markdown(f"* **Location:** `{alert['location']}`")
                                st.markdown(f"* **Today's Sales:** `{alert['today_sales']}`")
                                st.markdown(f"* **7-Day Average:** `{alert['avg_sales']}`")
                                st.markdown(f"* **Change:** `{alert['change_pct']}%`")
                                st.markdown(f"* **Suggested Cause:** {alert['cause']}")
                                st.markdown(f"**Data for {alert['sku']}:**")
                                sku_data = df[df['sku'] == alert['sku']].sort_values('date')
                                st.line_chart(sku_data, x='date', y='sales')
                                
                                # --- Add this alert's info to the email body string ---
                                email_body_text += f"* SKU: {alert['sku']} \n"
                                email_body_text += f"* Location: {alert['location']} \n"
                                email_body_text += f"* Today's Sales: {alert['today_sales']} \n"
                                email_body_text += f"* 7-Day Average: {alert['avg_sales']} \n"
                                email_body_text += f"* Change: {alert['change_pct']}% \n"
                                email_body_text += f"* Suggested Cause: {alert['cause']} \n\n"
                        
                        st.markdown("---")
                        email_body_text += "\n\nBest,\nSales Velocity Agent"
                        
                        # --- AUTONOMOUS LOGIC ---
                        subject_clean = subject_text.replace("SUBJECT: ", "")
                        
                        if auto_send:
                            # User wants it sent NOW.
                            st.info(f"Autonomous mode enabled. Sending alert to `{recipient_email}`...")
                            with st.spinner("Sending email ..."):
                                success, message = send_email(
                                    recipient_email, 
                                    subject_clean, 
                                    email_body_text
                                )
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                            # Errors are handled by the function
                        
                        else:
                            # User wants to review first. Show the button.
                            st.markdown(f"**Ready to send the report to:** `{recipient_email}`")
                            if st.button("Click Here to Send the Email Alert", use_container_width=True):
                                with st.spinner("Sending email..."):
                                    success, message = send_email(
                                        recipient_email, 
                                        subject_clean, 
                                        email_body_text
                                    )
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                        # --- NEW: "VIBE CODE" REVEALER ---
                        st.markdown("---")
                        with st.expander("Click here to see the *exact* prompt sent to the AI (The 'Vibe Code')"):
                            st.code(prompt, language="text")
                        # --- END NEW SECTION ---

                    except json.JSONDecodeError:
                        st.error("Error: The AI's response was not in the correct JSON format. Here is the raw text:")
                        st.text(response.text)
                    except Exception as e:
                        st.error(f"Error while processing alerts: {e}")
                        st.text(f"Raw AI response: {response.text}")

                except Exception as e:
                     st.error("Unable to connect with Gemini API. Please try again later.")
                     with st.expander("Technical Details"):
                         st.code(str(e))
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")