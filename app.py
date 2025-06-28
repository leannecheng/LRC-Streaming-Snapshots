import streamlit as st
import json
import pandas as pd
import altair as alt

# Load JSON data
with open("cleaned_data_mega.json") as f:
    data = json.load(f)

st.set_page_config(page_title="Streaming Dashboard", layout="wide")
st.title("📺UM LRC Streaming Dashboard")

custom_term_order = [
    "SpSu 2017", "Fall 2017", "Winter 2018",
    "SpSu 2018", "Fall 2018", "Winter 2019",
    "SpSu 2019", "Fall 2019", "Winter 2020",
    "SpSu 2020", "Fall 2020", "Winter 2021",
    "SpSu 2024", "Fall 2024", "Winter 2024"
]

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Controls")
    terms = ["All Terms"] + [t for t in custom_term_order if t in data["terms"]]
    selected_term = st.selectbox("Select Term", terms)
    
    if selected_term != "All Terms":
        toggle_mode = st.radio("View By", ["Department", "Level"])
        term_data = data["terms"][selected_term]
        if toggle_mode == "Department":
            departments = sorted(term_data["departments"].keys())
            departments.insert(0, "All Departments")
            selected_dept = st.selectbox("Select Department", departments, key="dept_dropdown")
        else:
            levels = set()
            for dept_data in term_data["departments"].values():
                levels.update(dept_data["levels"].keys())
            levels = sorted(levels, key=lambda x: (x == "Unknown", x))
            selected_level = st.selectbox("Select Level", levels, key="level_dropdown")

# --- MAIN CONTENT ---
if selected_term == "All Terms":
    combined_rows = []
    for term_name in custom_term_order:
        if term_name in data["terms"]:
            term_data = data["terms"][term_name]
            for dept_name, dept_data in term_data["departments"].items():
                for level, counts in dept_data["levels"].items():
                    combined_rows.append({
                        "Term": term_name,
                        "Department": dept_name,
                        "Level": level,
                        "Students": counts["students"],
                        "Reservations": counts["reservations"]
                    })

    df = pd.DataFrame(combined_rows)

    if not df.empty:
        total_students_all = df["Students"].sum()
        total_reservations_all = df["Reservations"].sum()
        st.markdown("### All Terms Totals")
        colA, colB = st.columns(2)
        colA.metric("Total Students", total_students_all)
        colB.metric("Total Reservations", total_reservations_all)
        st.markdown("---")

        top_departments = (
            df.groupby("Department", as_index=False)["Students"]
            .mean()
            .sort_values("Students", ascending=False)
            .head(8)["Department"]
            .tolist()
        )
        df_top = df[df["Department"].isin(top_departments)]

        st.subheader("Top 8 Departments: Students per Term")
        chart_top_students = (
            alt.Chart(df_top)
            .mark_bar(point=True)
            .encode(
                x=alt.X("Term:N", sort=custom_term_order),
                y="Students:Q",
                color="Department:N",
                tooltip=["Term:N", "Department:N", "Students:Q"]
            )
            .properties(width=900, height=500)
        )
        st.altair_chart(chart_top_students, use_container_width=True)

        top_departments_res = (
            df.groupby("Department", as_index=False)["Reservations"]
            .mean()
            .sort_values("Reservations", ascending=False)
            .head(8)["Department"]
            .tolist()
        )
        df_top_res = df[df["Department"].isin(top_departments_res)]

        st.subheader("Top 8 Departments: Reservations per Term")
        chart_top_res = (
            alt.Chart(df_top_res)
            .mark_bar(point=True)
            .encode(
                x=alt.X("Term:N", sort=custom_term_order),
                y="Reservations:Q",
                color="Department:N",
                tooltip=["Term:N", "Department:N", "Reservations:Q"]
            )
            .properties(width=900, height=500)
        )
        st.altair_chart(chart_top_res, use_container_width=True)

    else:
        st.warning("No data found in All Terms view.")

else:
    if toggle_mode == "Department":
        st.markdown("## Department View")
        if selected_dept == "All Departments":
            colA, colB = st.columns(2)
            colA.metric("Total Students", term_data["total_students"])
            colB.metric("Total Reservations", term_data["total_reservations"])
            st.markdown("---")

            dept_totals = []
            for dept_name, dept_data in term_data["departments"].items():
                dept_totals.append({
                    "Department": dept_name,
                    "Students": dept_data["total_students"],
                    "Reservations": dept_data["total_reservations"]
                })
            df_totals = pd.DataFrame(dept_totals).sort_values("Reservations", ascending=False)
            top8_res = df_totals.nlargest(8, "Reservations")
            top8_students = df_totals.nlargest(8, "Students")

            st.markdown(f"### Top 8 Departments in {selected_term}")
            col1, col2 = st.columns(2)
            with col1:
                st.write("Students")
                st.altair_chart(
                    alt.Chart(top8_students)
                    .mark_arc()
                    .encode(theta="Students:Q", color=alt.Color("Department:N"), tooltip=["Department:N", "Students:Q"])
                    .properties(width=400, height=400),
                    use_container_width=True
                )
            with col2:
                st.write("Reservations")
                st.altair_chart(
                    alt.Chart(top8_res)
                    .mark_arc()
                    .encode(theta="Reservations:Q", color=alt.Color("Department:N"), tooltip=["Department:N", "Reservations:Q"])
                    .properties(width=400, height=400),
                    use_container_width=True
                )

            st.markdown("### Department Totals Table")
            st.dataframe(df_totals, use_container_width=True)

        else:
            dept_data = term_data["departments"][selected_dept]
            colA, colB = st.columns(2)
            colA.metric("Total Students", dept_data["total_students"])
            colB.metric("Total Reservations", dept_data["total_reservations"])
            st.markdown("---")

            df_levels = pd.DataFrame([
                {"Level": lvl, "Students": counts["students"], "Reservations": counts["reservations"]}
                for lvl, counts in dept_data["levels"].items()
            ])

            st.markdown(f"### Level Breakdown for {selected_dept}")
            col1, col2 = st.columns(2)
            with col1:
                st.write("Students")
                st.altair_chart(
                    alt.Chart(df_levels)
                    .mark_arc()
                    .encode(theta="Students:Q", color=alt.Color("Level:N"), tooltip=["Level:N", "Students:Q"])
                    .properties(width=400, height=400),
                    use_container_width=True
                )
            with col2:
                st.write("Reservations")
                st.altair_chart(
                    alt.Chart(df_levels)
                    .mark_arc()
                    .encode(theta="Reservations:Q", color=alt.Color("Level:N"), tooltip=["Level:N", "Reservations:Q"])
                    .properties(width=400, height=400),
                    use_container_width=True
                )

    else:  # Level mode
        combined_rows = []
        for dept_name, dept_data in term_data["departments"].items():
            lvl_data = dept_data["levels"].get(selected_level)
            if lvl_data:
                combined_rows.append({
                    "Department": dept_name,
                    "Students": lvl_data["students"],
                    "Reservations": lvl_data["reservations"]
                })
        df = pd.DataFrame(combined_rows)

        total_students = df["Students"].sum()
        total_reservations = df["Reservations"].sum()
        st.markdown(f"### Level {selected_level} Totals")
        colA, colB = st.columns(2)
        colA.metric("Total Students", total_students)
        colB.metric("Total Reservations", total_reservations)
        st.markdown("---")

        top8_res = df.nlargest(8, "Reservations")
        top8_students = df.nlargest(8, "Students")

        st.markdown(f"### Top 8 Departments - Level {selected_level} in {selected_term}")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Students")
            st.altair_chart(
                alt.Chart(top8_students)
                .mark_arc()
                .encode(theta="Students:Q", color=alt.Color("Department:N"), tooltip=["Department:N", "Students:Q"])
                .properties(width=400, height=400),
                use_container_width=True
            )
        with col2:
            st.write("Reservations")
            st.altair_chart(
                alt.Chart(top8_res)
                .mark_arc()
                .encode(theta="Reservations:Q", color=alt.Color("Department:N"), tooltip=["Department:N", "Reservations:Q"])
                .properties(width=400, height=400),
                use_container_width=True
            )

st.markdown("""
---
Built with ❤️ using Streamlit + Altair.
""")
