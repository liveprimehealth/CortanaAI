import streamlit as st
import gspread
import pandas as pd
import json
import os

if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

if "GOOGLE_CREDENTIALS_JSON" in st.secrets and not os.path.exists("credentials.json"):
    with open("credentials.json", "w") as f:
        f.write(st.secrets["GOOGLE_CREDENTIALS_JSON"])

from cortana_fixed import call_claude, BASE_SYSTEM, get_today_pillar, get_sheet_leads
st.set_page_config(page_title="Cortana AI Operator", layout="wide")
PASSWORD = "prime123"

password = st.text_input(
    "Enter Cortana Password",
    type="password"
)

if password != PASSWORD:
    st.stop()
st.title("Cortana AI Operator")
st.caption("Live Prime Health Command Center")
st.divider()
leads = get_sheet_leads()

total_leads = len(leads)
hot_leads = len([l for l in leads if str(l.get("Priority", "")).lower() == "hot"])
booked_calls = len([l for l in leads if str(l.get("Status", "")).lower() == "booked call"])
clients = len([l for l in leads if str(l.get("Status", "")).lower() == "client"])

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Leads", total_leads)
col2.metric("Hot Leads", hot_leads)
col3.metric("Booked Calls", booked_calls)
col4.metric("Clients", clients)
warm_leads = len([
    l for l in leads
    if str(l.get("Priority", "")).lower() == "warm"
])

total_revenue = 0

try:
    revenue_values = []

    for lead in leads:
        revenue = lead.get("Revenue", 0)

        try:
            revenue = float(revenue)
        except:
            revenue = 0

        revenue_values.append(revenue)

    total_revenue = sum(revenue_values)

except Exception as e:
    total_revenue = 0
closed_won = len([
    l for l in leads
    if str(l.get("Call Status", "")).lower() == "closed won"
])

close_rate = 0

if booked_calls > 0:
    close_rate = round(
        (closed_won / booked_calls) * 100,
        1
    )
st.subheader("Pipeline Overview")

p1, p2, p3, p4, p5 = st.columns(5)
p1.metric("Hot Leads", hot_leads)
p2.metric("Warm Leads", warm_leads)
p3.metric("Booked Calls", booked_calls)
p4.metric("Est. Pipeline", f"${total_revenue:,.0f}")
p5.metric("Close Rate", f"{close_rate}%")
st.header("🧠 Today's Operator Mission")

if st.button("Generate Daily Operator Mission"):
    mission_prompt = f"""
You are Cortana AI Operator for Live Prime Health.

Act as Quinn's AI sales operator and business strategist.

Use this current business data:
Leads: {leads}
Total Leads: {total_leads}
Hot Leads: {hot_leads}
Warm Leads: {warm_leads}
Booked Calls: {booked_calls}
Clients: {clients}

Create today's operator mission.

Give:
1. Top 3 money-making tasks
2. Top 3 leads to follow up with
3. Best follow-up angle
4. Content task for today
5. Revenue target
6. One non-negotiable action before the day ends

Keep it direct, tactical, and execution-focused.
"""

    mission = call_claude(
        BASE_SYSTEM,
        [{"role": "user", "content": mission_prompt}],
        max_tokens=1500
    )

    st.text_area(
        "Today's Mission:",
        value=mission,
        height=500
    )

st.header("💰 Money-Making Tasks Engine")

if st.button("Generate Money-Making Tasks"):
    money_prompt = f"""
You are Cortana AI Operator for Live Prime Health.

Your job is to identify the highest revenue-producing actions Quinn should take today.

Use this data:
Leads: {leads}
Total Leads: {total_leads}
Hot Leads: {hot_leads}
Warm Leads: {warm_leads}
Booked Calls: {booked_calls}
Clients: {clients}
Total Revenue: {total_revenue}
Close Rate: {close_rate}%

Create a money-making task list.

Give:
1. Top 5 actions ranked by revenue impact
2. Exact lead names to contact first
3. What to say to each lead
4. Which leads need follow-up today
5. Which leads are closest to closing
6. One content action likely to generate leads today
7. One admin/business action that protects revenue
8. One urgent warning if Quinn is leaving money on the table

Make it tactical, direct, and sales-focused.
"""

    money_tasks = call_claude(
        BASE_SYSTEM,
        [{"role": "user", "content": money_prompt}],
        max_tokens=2000
    )

    st.text_area(
        "Today's Money-Making Tasks:",
        value=money_tasks,
        height=650
    )
st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["Daily Content", "Money", "Reels", "Leads"])

with tab1:
    st.header("Daily Content")
    day, pillar = get_today_pillar()
    st.subheader(f"{day}: {pillar}")

    if st.button("Generate Daily Content"):
        prompt = f"""
Today is {day}.
Today's content pillar is {pillar}.

Generate 5 reels:
1. controversial
2. relatable
3. educational
4. story
5. CTA/conversion

Include hook, script, visual cues, on-screen text, and CTA.
"""
        output = call_claude(BASE_SYSTEM, [{"role": "user", "content": prompt}], max_tokens=3000)
        st.markdown(output)

with tab2:
    st.header("Money Dashboard")

    if st.button("Load Money Report"):
        leads = get_sheet_leads()

        hot = [l for l in leads if str(l.get("Status", "")).lower() == "hot"]
        followups = [l for l in leads if str(l.get("Status", "")).lower() in ["followup", "follow up", "contacted"]]
        new = [l for l in leads if str(l.get("Status", "")).lower() in ["new", ""]]

        st.subheader("Hot Leads")
        st.write(hot if hot else "None")

        st.subheader("Follow-Ups")
        st.write(followups if followups else "None")

        st.subheader("New Leads")
        st.write(new if new else "None")

        st.success("Priority: message hot leads first, follow up second, qualify new leads third.")

with tab3:
    st.header("Reels Generator")
    topic = st.text_input("Topic")

    if st.button("Generate Reels"):
        if topic:
            with open("memory/reels_system_prompt.txt", "r") as f:
                reels_prompt = f.read()

            output = call_claude(
                BASE_SYSTEM + "\n\n" + reels_prompt,
                [{"role": "user", "content": f"Write 5 viral reels about: {topic}"}],
                max_tokens=3000
            )
            st.markdown(output)
        else:
            st.warning("Enter a topic first.")

with tab4:
    st.header("Lead Database")

    columns = [
        "Name",
        "Instagram",
        "Phone",
        "Email",
        "Goal",
        "Source",
        "Status",
        "Priority",
        "Last Contact",
        "Next Follow Up",
        "Notes",
        "Lead Score",
        "Recommended Action",
        "Urgency"
    ]

    leads = get_sheet_leads()
    import pandas as pd

    if leads is None or len(leads) == 0:
        leads = pd.DataFrame(columns=columns)
    else:
        leads = pd.DataFrame(leads)

edited_df = st.data_editor(
    leads,
    use_container_width=True,
    num_rows="dynamic"
)

selected_lead = st.selectbox(
    "Select Lead For Follow-Up",
    edited_df["Name"].tolist()
)

if st.button("Generate Follow-Up"):
    lead_data = edited_df[edited_df["Name"] == selected_lead].iloc[0]

    prompt = f"""
Create a personalized follow-up DM for this lead.

Lead Info:
{lead_data.to_dict()}

Tone:
- confident
- direct
- human
- not salesy
- focused on helping
- Live Prime Health style
"""

    followup = call_claude(
        BASE_SYSTEM,
        [{"role": "user", "content": prompt}],
        max_tokens=1000
    )

    st.subheader("Generated Follow-Up DM")

    st.text_area(
        "Copy this message:",
        value=followup,
        height=180
    )
st.caption(
    "Use this DM inside Instagram, text, or email."
)

st.caption("Use this DM inside Instagram, text, or email. Adjust slightly so it sounds natural.")
if st.button("Save Leads"):

    try:
        gc = gspread.service_account(filename="credentials.json")
        sheet = gc.open("Cortana Leads").sheet1

        sheet.clear()
        sheet.append_row(columns)

        for row in edited_df.values.tolist():
            sheet.append_row(row)

        st.success("Leads saved successfully.")

    except Exception as e:
        st.error(f"Error saving leads: {e}")
if st.button("Analyze Leads"):

    try:
        gc = gspread.service_account(filename="credentials.json")
        sheet = gc.open("Cortana Leads").sheet1

        headers = sheet.row_values(1)

        score_col = headers.index("Lead Score") + 1
        urgency_col = headers.index("Urgency") + 1
        action_col = headers.index("Recommended Action") + 1

        for idx, row in edited_df.iterrows():
            row_number = idx + 2

            analysis_prompt = f"""
You are Cortana AI Operator for Live Prime Health.

Return ONLY valid JSON. No markdown. No explanation.

Analyze this lead:
{row.to_dict()}

Return exactly:
{{
  "lead_score": "1-100",
  "urgency": "LOW, MEDIUM, or HIGH",
  "recommended_action": "short next best action"
}}
"""

            analysis = call_claude(
                BASE_SYSTEM,
                [{"role": "user", "content": analysis_prompt}],
                max_tokens=500
            )

            cleaned_analysis = analysis.strip()
            start = cleaned_analysis.find("{")
            end = cleaned_analysis.rfind("}") + 1
            cleaned_analysis = cleaned_analysis[start:end]

            data = json.loads(cleaned_analysis)

            sheet.update_cell(row_number, score_col, data.get("lead_score", ""))
            sheet.update_cell(row_number, urgency_col, data.get("urgency", ""))
            sheet.update_cell(row_number, action_col, data.get("recommended_action", ""))

            st.write(f"Updated: {row.get('Name', 'Unknown Lead')}")

        st.success("AI Lead Intelligence written to Google Sheets.")

    except Exception as e:
        st.error(f"Error analyzing leads: {e}")
