import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

try:
    from src.analyzer.gap import analyse_gap, ROLE_KEYWORDS
    from src.analyzer.resume import extract_resume_text
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False


st.set_page_config(
    page_title="Job Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path("data/processed")


@st.cache_data(ttl=3600)
def load_data():
    clustered = DATA_DIR / "jobs_clustered.parquet"
    forecasts = DATA_DIR / "forecasts.parquet"
    skills_file = DATA_DIR / "jobs_with_skills.parquet"

    if clustered.exists():
        df = pd.read_parquet(clustered)
    elif skills_file.exists():
        df = pd.read_parquet(skills_file)
    else:
        st.error("No processed data found. Run `python pipeline.py --all` first.")
        st.stop()

    fc = pd.read_parquet(forecasts) if forecasts.exists() else pd.DataFrame()
    return df, fc


df, forecasts = load_data()


@st.cache_resource
def _load_nlp():
    try:
        import spacy
        from src.nlp.extractor import build_matcher, load_skills_vocabulary
        nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
        skills = load_skills_vocabulary()
        matcher = build_matcher(skills, nlp)
        skill_lookup = {s.lower(): s for s in skills}
        return nlp, matcher, skill_lookup
    except OSError:
        return None, None, None


nlp_obj, matcher_obj, skill_lookup_obj = _load_nlp()

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("Job Market Intelligence")
st.sidebar.caption(f"{len(df):,} job postings analysed")

if "date" in df.columns:
    date_range = df["date"].dropna()
    if not date_range.empty:
        st.sidebar.info(
            f"**Date range**\n{date_range.min().strftime('%b %d %Y')} → "
            f"{date_range.max().strftime('%b %d %Y')}"
        )

# ── Tab layout ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Skill Heatmap", "Role Clusters", "Skill Trends", "Resume Analyzer"])


# ── Tab 1: Overview ───────────────────────────────────────────────────────────
with tab1:
    st.header("Market Overview")

    all_skills = df["skills"].explode() if "skills" in df.columns else pd.Series(dtype=str)
    unique_skills = all_skills.dropna().nunique()
    n_clusters = df["cluster"].nunique() if "cluster" in df.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Jobs", f"{len(df):,}")
    c2.metric("Unique Skills", f"{unique_skills:,}")
    c3.metric("Role Clusters", f"{n_clusters:,}")
    c4.metric("Data Sources", df["source"].nunique() if "source" in df.columns else "—")

    st.divider()

    # Top 30 skills bar chart
    if not all_skills.empty:
        skill_counts = all_skills.value_counts().head(30).reset_index()
        skill_counts.columns = ["skill", "count"]
        fig = px.bar(
            skill_counts,
            x="count",
            y="skill",
            orientation="h",
            title="Top 30 Skills by Job Mention Count",
            color="count",
            color_continuous_scale="Blues",
            labels={"count": "Job Postings", "skill": ""},
        )
        fig.update_layout(height=700, showlegend=False, coloraxis_showscale=False,
                          yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width='stretch')

    # Jobs over time
    if "week" in df.columns:
        st.subheader("Job Postings Over Time")
        weekly = df.groupby("week").size().reset_index(name="count")
        weekly["week"] = pd.to_datetime(weekly["week"])
        fig2 = px.area(weekly, x="week", y="count", title="Weekly Job Postings",
                       labels={"week": "Week", "count": "Postings"})
        fig2.update_layout(height=300)
        st.plotly_chart(fig2, width='stretch')


# ── Tab 2: Skill Heatmap ──────────────────────────────────────────────────────
with tab2:
    st.header("Skills by Role Cluster")

    if "cluster_name" not in df.columns or "skills" not in df.columns:
        st.info("Run the full pipeline (including clustering) to see this view.")
    else:
        top_skills = df["skills"].explode().value_counts().head(25).index.tolist()
        clusters = [c for c in df["cluster_name"].unique() if c != "Uncategorized"]

        selected_clusters = st.multiselect(
            "Filter clusters", clusters, default=clusters[:min(10, len(clusters))]
        )

        heat_df = df[df["cluster_name"].isin(selected_clusters)].copy()
        heat_df = heat_df.explode("skills")
        heat_df = heat_df[heat_df["skills"].isin(top_skills)]

        pivot = (
            heat_df.groupby(["cluster_name", "skills"])
            .size()
            .reset_index(name="count")
            .pivot(index="cluster_name", columns="skills", values="count")
            .fillna(0)
        )

        if not pivot.empty:
            fig = px.imshow(
                pivot,
                title="Skill Frequency per Role Cluster",
                color_continuous_scale="YlOrRd",
                aspect="auto",
                labels={"color": "Job count"},
            )
            fig.update_layout(height=max(400, len(pivot) * 35))
            st.plotly_chart(fig, width='stretch')


# ── Tab 3: Role Clusters ──────────────────────────────────────────────────────
with tab3:
    st.header("Role Clusters (UMAP + HDBSCAN)")

    if "umap_x" not in df.columns:
        st.info("Run `python pipeline.py --cluster` to generate UMAP embeddings.")
    else:
        plot_df = df[df["cluster"] != -1].copy() if "cluster" in df.columns else df.copy()

        fig = px.scatter(
            plot_df.sample(min(5000, len(plot_df)), random_state=42),
            x="umap_x",
            y="umap_y",
            color="cluster_name",
            hover_data=["title", "company", "location"],
            title="Job Role Clusters (2D UMAP Projection)",
            labels={"umap_x": "UMAP-1", "umap_y": "UMAP-2", "cluster_name": "Cluster"},
            opacity=0.6,
        )
        fig.update_traces(marker_size=4)
        fig.update_layout(height=600, legend=dict(itemsizing="constant"))
        st.plotly_chart(fig, width='stretch')

        st.subheader("Cluster Sizes")
        cluster_sizes = (
            df[df["cluster"] != -1]["cluster_name"].value_counts().reset_index()
            if "cluster" in df.columns
            else df["cluster_name"].value_counts().reset_index()
        )
        cluster_sizes.columns = ["cluster", "count"]
        fig2 = px.bar(cluster_sizes, x="cluster", y="count",
                      title="Jobs per Cluster", labels={"cluster": "", "count": "Job count"})
        fig2.update_layout(height=350, xaxis_tickangle=-30)
        st.plotly_chart(fig2, width='stretch')


# ── Tab 4: Skill Trends & Forecast ────────────────────────────────────────────
with tab4:
    st.header("Skill Demand Trends & Forecast")

    if forecasts.empty:
        st.info("Run `python pipeline.py --forecast` to generate skill forecasts.")
    else:
        available_skills = sorted(forecasts["skill"].unique().tolist())

        # Show rising / falling badges
        if "trend_slope" in forecasts.columns:
            trend_summary = (
                forecasts.groupby("skill")["trend_slope"].first().reset_index()
            )
            rising = trend_summary[trend_summary["trend_slope"] > 0.1]["skill"].tolist()
            falling = trend_summary[trend_summary["trend_slope"] < -0.1]["skill"].tolist()

            r_col, f_col = st.columns(2)
            with r_col:
                st.success(f"**Rising skills ({len(rising)})**\n\n" + ", ".join(rising[:15]))
            with f_col:
                st.error(f"**Declining skills ({len(falling)})**\n\n" + ", ".join(falling[:15]))
            st.divider()

        default_skills = available_skills[:min(5, len(available_skills))]
        selected = st.multiselect("Select skills to plot", available_skills, default=default_skills)

        if selected:
            plot_data = forecasts[forecasts["skill"].isin(selected)]
            today = pd.Timestamp.now(tz="UTC").normalize().tz_localize(None)

            fig = go.Figure()
            colors = px.colors.qualitative.Plotly

            for i, skill in enumerate(selected):
                sd = plot_data[plot_data["skill"] == skill].sort_values("ds")
                color = colors[i % len(colors)]

                # Historical actuals
                hist = sd[sd["ds"] <= today].dropna(subset=["y"])
                if not hist.empty:
                    fig.add_trace(go.Scatter(
                        x=hist["ds"], y=hist["y"],
                        mode="lines+markers",
                        name=f"{skill} (actual)",
                        line=dict(color=color, width=2),
                        marker=dict(size=4),
                    ))

                # Forecast
                fcast = sd[sd["ds"] > today]
                if not fcast.empty:
                    fig.add_trace(go.Scatter(
                        x=fcast["ds"], y=fcast["yhat"],
                        mode="lines",
                        name=f"{skill} (forecast)",
                        line=dict(color=color, width=2, dash="dash"),
                    ))
                    # Confidence band
                    fig.add_trace(go.Scatter(
                        x=pd.concat([fcast["ds"], fcast["ds"][::-1]]),
                        y=pd.concat([fcast["yhat_upper"], fcast["yhat_lower"][::-1]]),
                        fill="toself",
                        fillcolor=color.replace(")", ", 0.15)").replace("rgb", "rgba"),
                        line=dict(color="rgba(255,255,255,0)"),
                        showlegend=False,
                        hoverinfo="skip",
                    ))

            # Vertical "today" line
            fig.add_vline(x=today, line_dash="dot", line_color="gray", annotation_text="Today")
            fig.update_layout(
                title="Weekly Skill Mentions + 26-week Forecast",
                xaxis_title="Week",
                yaxis_title="Job Postings Mentioning Skill",
                height=500,
                hovermode="x unified",
            )
            st.plotly_chart(fig, width='stretch')


# ── Tab 5: Resume Analyzer ────────────────────────────────────────────────────
with tab5:
    st.header("Resume Skill Gap Analyzer")

    if not ANALYZER_AVAILABLE:
        st.error("Analyzer dependencies missing. Run: `pip install pdfminer.six python-docx`")
    elif nlp_obj is None:
        st.error("spaCy model not found. Run: `python -m spacy download en_core_web_sm`")
    else:
        col_role, col_upload = st.columns([1, 2])
        with col_role:
            selected_role = st.selectbox("Target Role", list(ROLE_KEYWORDS.keys()))
        with col_upload:
            uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"])

        if uploaded_file is not None:
            try:
                resume_text = extract_resume_text(uploaded_file.read(), uploaded_file.name)
            except ValueError as e:
                st.error(str(e))
                resume_text = ""

            if resume_text and len(resume_text) < 50:
                st.warning(
                    "Very little text was extracted. If this is a scanned PDF, "
                    "try converting it to DOCX first."
                )

            if st.button("Analyze Resume", type="primary"):
                if not resume_text:
                    st.error("Could not extract text from this file. Try a different PDF or convert to DOCX.")
                    st.stop()
                with st.spinner("Analysing your resume..."):
                    report = analyse_gap(
                        resume_text,
                        selected_role,
                        df,
                        forecasts,
                        nlp_obj,
                        matcher_obj,
                        skill_lookup_obj,
                    )

                st.divider()

                # ── Score row ────────────────────────────────────────────
                score_col, gauge_col, pct_col = st.columns([1, 2, 1])

                with score_col:
                    st.metric("Readiness Score", f"{report.readiness_score}/100")
                    st.caption(f"Based on {report.jobs_analysed:,} {selected_role} postings")

                with gauge_col:
                    gauge = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=report.readiness_score,
                        number={"suffix": "/100"},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": "#1f77b4"},
                            "steps": [
                                {"range": [0, 40], "color": "#ffcccc"},
                                {"range": [40, 70], "color": "#fff3cc"},
                                {"range": [70, 100], "color": "#ccffcc"},
                            ],
                            "threshold": {
                                "line": {"color": "black", "width": 2},
                                "thickness": 0.75,
                                "value": report.readiness_score,
                            },
                        },
                        title={"text": "Readiness"},
                    ))
                    gauge.update_layout(height=200, margin=dict(t=30, b=0, l=20, r=20))
                    st.plotly_chart(gauge, width='stretch')

                with pct_col:
                    if report.market_percentile is not None:
                        st.metric(
                            "Market Position",
                            f"Top {100 - report.market_percentile}%",
                            help="How your score compares to other candidates in this role",
                        )
                        st.caption(
                            f"Better than {report.market_percentile}% of analysed postings"
                        )

                st.divider()

                # ── Skills present / missing ──────────────────────────────
                found_col, missing_col = st.columns(2)

                with found_col:
                    st.subheader(f"Skills Found ({len(report.skills_present)})")
                    if report.skills_present:
                        for skill in report.skills_present:
                            demand = report.skill_demand.get(skill, "Low")
                            badge = "🟢" if demand == "High" else "🟡" if demand == "Medium" else "⚪"
                            st.success(f"{badge} {skill}  — {demand} demand")
                    else:
                        st.info("No matching skills found in the top role skills.")

                with missing_col:
                    st.subheader(f"Missing Skills ({len(report.skills_missing)})")
                    if report.skills_missing:
                        for skill in report.skills_missing:
                            demand = report.skill_demand.get(skill, "Low")
                            badge = "🔴" if demand == "High" else "🟠" if demand == "Medium" else "⚪"
                            st.warning(f"{badge} {skill}  — {demand} demand")
                    else:
                        st.success("You have all top skills for this role!")

                st.divider()

                # ── Top recommended skills table ──────────────────────────
                st.subheader("Top 10 Recommended Skills")
                emerging_set = {s.lower() for s in report.emerging_skills}

                rec_rows = []
                for skill in report.role_top_skills[:10]:
                    rec_rows.append({
                        "Skill": skill,
                        "Demand": report.skill_demand.get(skill, "Low"),
                        "Have It": "✓" if skill in {s.lower() for s in report.skills_present} else "✗",
                        "Trending Up": "🚀" if skill in emerging_set else "",
                    })
                st.dataframe(
                    pd.DataFrame(rec_rows),
                    width='stretch',
                    hide_index=True,
                )

                # ── Emerging skills you already have ──────────────────────
                if report.emerging_skills:
                    st.divider()
                    st.subheader("You're Ahead of the Curve 🚀")
                    st.caption(
                        "Skills on your resume that are trending strongly upward in the market."
                    )
                    st.success("  ·  ".join(report.emerging_skills))
