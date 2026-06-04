import os
import uuid
import plotly.express as px
import pandas as pd

def generate_chart(df: pd.DataFrame, chart_type: str, chart_folder: str, summary_payload: dict) -> str | None:
    os.makedirs(chart_folder, exist_ok=True)

    if df.empty or chart_type in {"none", "table", None}:
        return None

    x_col = summary_payload.get("x_axis")
    y_col = summary_payload.get("y_axis")

    # Fallback protections if standard identifiers are absent
    if not x_col or x_col not in df.columns:
        x_col = df.columns[0] if len(df.columns) > 0 else None
    if not y_col or y_col not in df.columns:
        y_col = df.columns[1] if len(df.columns) > 1 else None

    if not x_col:
        return None

    try:
        if chart_type == "bar" and y_col:
            fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} across {x_col}")
        elif chart_type == "line" and y_col:
            fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} trended over {x_col}")
        elif chart_type == "pie" and y_col:
            fig = px.pie(df, names=x_col, values=y_col, title=f"{y_col} split by {x_col}")
        elif chart_type == "scatter" and y_col:
            fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} metrics mapping vs {x_col}")
        else:
            return None

        # Sleek dark-theme overlay presets for professional look
        fig.update_layout(
            paper_bgcolor='rgba(30,41,59,1)',
            plot_bgcolor='rgba(30,41,59,1)',
            font_color='#f8fafc',
            title_font_color='#f8fafc'
        )

        file_name = f"{uuid.uuid4().hex}.html"
        file_path = os.path.join(chart_folder, file_name)
        fig.write_html(file_path)

        return file_name
    except Exception:
        return None