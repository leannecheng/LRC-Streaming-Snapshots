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
    for term_name in term_order:
        term_data = data["terms"][term_name]
        for dept_name, dept_data in term_data["departments"].items():
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
        c1.metric("Total Students", total_students)
        c2.metric("Total Reservations", total_reservations)
        st.markdown("---")

        # Top 8 by average Students
        top_depts_students = (
            df.groupby("Department")["Students"]
              .mean()
              .nlargest(8)
              .index
              .tolist()
        )
        df_top_students = df[df["Department"].isin(top_depts_students)]
        st.subheader("Top 8 Departments: Students per Term")
        chart1 = (
            alt.Chart(df_top_students)
               .mark_bar(point=True)
               .encode(
                   x=alt.X("Term:N", sort=term_order),
                   y="Students:Q",
                   color="Department:N",
                   tooltip=["Term","Department","Students"]
               )
               .properties(width=900, height=500)
        )
        st.altair_chart(chart1, use_container_width=True)

        # Top 8 by average Reservations
        top_depts_res = (
            df.groupby("Department")["Reservations"]
              .mean()
              .nlargest(8)
              .index
              .tolist()
        )
        df_top_res = df[df["Department"].isin(top_depts_res)]
        st.subheader("Top 8 Departments: Reservations per Term")
        chart2 = (
            alt.Chart(df_top_res)
               .mark_bar(point=True)
               .encode(
                   x=alt.X("Term:N", sort=term_order),
                   y="Reservations:Q",
                   color="Department:N",
                   tooltip=["Term","Department","Reservations"]
               )
               .properties(width=900, height=500)
        )
        st.altair_chart(chart2, use_container_width=True)

else:
    term_data = data["terms"][selected_term]

    if toggle_mode == "Department":
        st.markdown(f"## Department View — {selected_term}")
        if selected_dept == "All Departments":
            s1, s2 = st.columns(2)
            s1.metric("Total Students", term_data["total_students"])
            s2.metric("Total Reservations", term_data["total_reservations"])
            st.markdown("---")

            dept_totals = [
                {"Department": d, "Students": td["total_students"], "Reservations": td["total_reservations"]}
                for d, td in term_data["departments"].items()
            ]
            df_totals = pd.DataFrame(dept_totals).sort_values("Reservations", ascending=False)

            top8_students = df_totals.nlargest(8, "Students")
            top8_res     = df_totals.nlargest(8, "Reservations")

            col1, col2 = st.columns(2)
            with col1:
                st.write("### Students")
                st.altair_chart(
                    alt.Chart(top8_students)
                       .mark_arc()
                       .encode(theta="Students:Q", color="Department:N", tooltip=["Department","Students"])
                       .properties(width=400, height=400),
                    use_container_width=True
                )
            with col2:
                st.write("### Reservations")
                st.altair_chart(
                    alt.Chart(top8_res)
                       .mark_arc()
                       .encode(theta="Reservations:Q", color="Department:N", tooltip=["Department","Reservations"])
                       .properties(width=400, height=400),
                    use_container_width=True
                )

            st.markdown("### Department Totals Table")
            st.dataframe(df_totals, use_container_width=True)
        else:
            dept_data = term_data["departments"][selected_dept]
            d1, d2 = st.columns(2)
            d1.metric("Total Students", dept_data["total_students"])
            d2.metric("Total Reservations", dept_data["total_reservations"])
            st.markdown("---")

            df_levels = pd.DataFrame([
                {"Level": lvl, "Students": c["students"], "Reservations": c["reservations"]}
                for lvl, c in dept_data["levels"].items()
            ])

            st.markdown(f"### Level Breakdown for {selected_dept}")
            col1, col2 = st.columns(2)
            with col1:
                st.write("Students")
                st.altair_chart(
                    alt.Chart(df_levels)
                       .mark_arc()
                       .encode(theta="Students:Q", color="Level:N", tooltip=["Level","Students"])
                       .properties(width=400, height=400),
                    use_container_width=True
                )
            with col2:
                st.write("Reservations")
                st.altair_chart(
                    alt.Chart(df_levels)
                       .mark_arc()
                       .encode(theta="Reservations:Q", color="Level:N", tooltip=["Level","Reservations"])
                       .properties(width=400, height=400),
                    use_container_width=True
                )
    else:
        st.markdown(f"## Level View — {selected_term} — Level {selected_level}")
        rows = []
        for dept_name, td in term_data["departments"].items():
            lvl = td["levels"].get(selected_level)
            if lvl:
                rows.append({"Department": dept_name, "Students": lvl["students"], "Reservations": lvl["reservations"]})
        df_lv = pd.DataFrame(rows)
        total_s = df_lv["Students"].sum()
        total_r = df_lv["Reservations"].sum()
        c1, c2 = st.columns(2)
        c1.metric("Total Students", total_s)
        c2.metric("Total Reservations", total_r)
        st.markdown("---")

        top8_s = df_lv.nlargest(8, "Students")
        top8_r = df_lv.nlargest(8, "Reservations")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Students")
            st.altair_chart(
                alt.Chart(top8_s)
                   .mark_arc()
                   .encode(theta="Students:Q", color="Department:N", tooltip=["Department","Students"])
                   .properties(width=400, height=400),
                use_container_width=True
            )
        with col2:
            st.write("Reservations")
            st.altair_chart(
                alt.Chart(top8_r)
                   .mark_arc()
                   .encode(theta="Reservations:Q", color="Department:N", tooltip=["Department","Reservations"])
                   .properties(width=400, height=400),
                use_container_width=True
            )

st.markdown("""
---
###### Built by [Leanne Cheng](https://leannecheng.github.io/) with ❤️ for the [U-M Language Resource Center](https://lsa.umich.edu/lrc) ✨
""")


