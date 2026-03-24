import streamlit as st
import pandas as pd
import altair as alt
import requests

# ───────────────────────────────────────────────
# CONFIGURATION
PUBLIC_JSON_URL = "https://drive.google.com/uc?export=download&id=1-oPMoY0D_vaF0vhxPVKizDLnNIFulcYa"
# ───────────────────────────────────────────────

st.set_page_config(page_title="Streaming Dashboard", layout="wide")
st.title("📺 U-M LRC Streaming Dashboard")

# Fetch the JSON from Drive
try:
    resp = requests.get(PUBLIC_JSON_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()
except Exception:
    st.error("⚠️ Could not load dashboard data. Please check the data source or your network connection.")
    st.stop()

# Use the JSON's intrinsic order
term_order = list(data["terms"].keys())

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Controls")
    terms = ["All Terms"] + term_order
    selected_term = st.selectbox("Select Term", terms)

    if selected_term != "All Terms":
        toggle_mode = st.radio("View By", ["Department", "Level"])
        term_data = data["terms"][selected_term]
        if toggle_mode == "Department":
            departments = ["All Departments"] + list(term_data["departments"].keys())
            selected_dept = st.selectbox("Select Department", departments, key="dept_dropdown")
        else:
            levels = sorted({ lvl for d in term_data["departments"].values() for lvl in d["levels"] })
            selected_level = st.selectbox("Select Level", levels, key="level_dropdown")

# --- MAIN CONTENT ---
if selected_term == "All Terms":
    rows = []
    trend_rows = []
    for term_name in term_order:
        t_data = data["terms"][term_name]
        
        # Collect data for trend chart (Licensing over time)
        if "percent_licensed" in t_data:
            trend_rows.append({
                "Term": term_name,
                "Percent Licensed": t_data["percent_licensed"]
            })

        for dept_name, dept_data in t_data["departments"].items():
            for level, counts in dept_data["levels"].items():
                rows.append({
                    "Term": term_name,
                    "Department": dept_name,
                    "Level": level,
                    "Students": counts["students"],
                    "Reservations": counts["reservations"]
                })

    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("No data available for All Terms.")
    else:
        total_students = df["Students"].sum()
        total_reservations = df["Reservations"].sum()
        st.markdown("### All Terms Totals")
        c1, c2 = st.columns(2)
        c1.metric("Total Students", f"{total_students:,}")
        c2.metric("Total Reservations", f"{total_reservations:,}")
        
        # --- NEW: Licensing Trend Chart ---
        if trend_rows:
            st.markdown("---")
            st.subheader("📈 Licensing Coverage Trend")
            df_trend = pd.DataFrame(trend_rows)
            trend_chart = (
                alt.Chart(df_trend)
                .mark_line(point=True, color="#ff4b4b")
                .encode(
                    x=alt.X("Term:N", sort=term_order),
                    y=alt.Y("Percent Licensed:Q", scale=alt.Scale(domain=[0, 100])),
                    tooltip=["Term", "Percent Licensed"]
                )
                .properties(width=900, height=300)
            )
            st.altair_chart(trend_chart, use_container_width=True)

        st.markdown("---")

        # Top 8 by average Students
        top_depts_students = df.groupby("Department")["Students"].mean().nlargest(8).index.tolist()
        df_top_students = df[df["Department"].isin(top_depts_students)]
        st.subheader("Top 8 Departments: Students per Term")
        chart1 = (
            alt.Chart(df_top_students)
            .mark_bar()
            .encode(
                x=alt.X("Term:N", sort=term_order),
                y="Students:Q",
                color="Department:N",
                tooltip=["Term","Department","Students"]
            )
            .properties(width=900, height=400)
        )
        st.altair_chart(chart1, use_container_width=True)

else:
    term_data = data["terms"][selected_term]

    # Check for Option A: Only show Licensing/Location if keys exist
    has_new_metrics = "percent_licensed" in term_data and "locations" in term_data

    if toggle_mode == "Department":
        st.markdown(f"## Department View — {selected_term}")
        
        if selected_dept == "All Departments":
            # Top Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Students", f"{term_data['total_students']:,}")
            m2.metric("Total Reservations", f"{term_data['total_reservations']:,}")
            if has_new_metrics:
                m3.metric("Overall Licensed %", f"{term_data['percent_licensed']}%")
            
            st.markdown("---")

            # New Visuals Row (Option A)
            if has_new_metrics:
                col_lic, col_loc = st.columns(2)
                with col_lic:
                    st.write("### Licensing Status")
                    lic_df = pd.DataFrame([
                        {"Status": "Licensed", "Value": term_data["percent_licensed"]},
                        {"Status": "Unlicensed", "Value": 100 - term_data["percent_licensed"]}
                    ])
                    st.altair_chart(alt.Chart(lic_df).mark_arc(innerRadius=50).encode(
                        theta="Value:Q", color=alt.Color("Status:N", scale=alt.Scale(range=['#4CAF50', '#757575'])),
                        tooltip=["Status", "Value"]
                    ), use_container_width=True)

                with col_loc:
                    st.write("### Reservations by Location")
                    loc_df = pd.DataFrame([{"Location": k, "Percent": v} for k, v in term_data["locations"].items()])
                    st.altair_chart(alt.Chart(loc_df).mark_arc().encode(
                        theta="Percent:Q", color="Location:N", tooltip=["Location", "Percent"]
                    ), use_container_width=True)
                st.markdown("---")

            # Standard Dept Charts
            dept_totals = [
                {"Department": d, "Students": td["total_students"], 
                 "Reservations": td["total_reservations"], 
                 "Licensed %": td.get("percent_licensed", "N/A")}
                for d, td in term_data["departments"].items()
            ]
            df_totals = pd.DataFrame(dept_totals).sort_values("Reservations", ascending=False)

            c1, c2 = st.columns(2)
            with c1:
                st.write("### Students by Dept")
                st.altair_chart(alt.Chart(df_totals.nlargest(8, "Students")).mark_arc().encode(
                    theta="Students:Q", color="Department:N"
                ), use_container_width=True)
            with c2:
                st.write("### Reservations by Dept")
                st.altair_chart(alt.Chart(df_totals.nlargest(8, "Reservations")).mark_arc().encode(
                    theta="Reservations:Q", color="Department:N"
                ), use_container_width=True)

            st.markdown("### Department Totals Table")
            st.dataframe(df_totals, use_container_width=True)
        
        else:
            # Single Department Selection
            dept_data = term_data["departments"][selected_dept]
            d1, d2, d3 = st.columns(3)
            d1.metric("Total Students", f"{dept_data['total_students']:,}")
            d2.metric("Total Reservations", f"{dept_data['total_reservations']:,}")
            if "percent_licensed" in dept_data:
                d3.metric("Licensed %", f"{dept_data['percent_licensed']}%")

            df_levels = pd.DataFrame([
                {"Level": lvl, "Students": c["students"], "Reservations": c["reservations"]}
                for lvl, c in dept_data["levels"].items()
            ])
            st.markdown(f"### Level Breakdown for {selected_dept}")
            st.altair_chart(alt.Chart(df_levels).mark_bar().encode(
                x="Level:N", y="Reservations:Q", color="Level:N", tooltip=["Level","Reservations"]
            ), use_container_width=True)

    else:
        # Level View Logic
        st.markdown(f"## Level View — {selected_term} — Level {selected_level}")
        rows = []
        for dept_name, td in term_data["departments"].items():
            lvl = td["levels"].get(selected_level)
            if lvl:
                rows.append({"Department": dept_name, "Students": lvl["students"], "Reservations": lvl["reservations"]})
        df_lv = pd.DataFrame(rows)
        st.altair_chart(alt.Chart(df_lv).mark_bar().encode(
            x=alt.X("Department:N", sort='-y'), y="Reservations:Q", color="Department:N"
        ), use_container_width=True)

st.markdown("""
---
###### Built by [Leanne Cheng](https://leannecheng.github.io/) with ❤️ for the [U-M Language Resource Center](https://lsa.umich.edu/lrc) ✨
""")