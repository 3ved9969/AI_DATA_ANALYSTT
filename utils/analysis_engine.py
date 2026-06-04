import pandas as pd

def _safe_col(df: pd.DataFrame, col: str | None) -> str | None:
    if col and col in df.columns:
        return col
    return None

def run_analysis(df: pd.DataFrame, intent_payload: dict) -> tuple[pd.DataFrame, dict]:
    intent = intent_payload.get("intent")
    target_columns = intent_payload.get("target_columns", [])
    group_by = _safe_col(df, intent_payload.get("group_by"))
    metric = intent_payload.get("metric")
    sort_order = intent_payload.get("sort_order")
    top_n = intent_payload.get("top_n", 5)

    result = df.copy()
    summary = {
        "intent": intent,
        "rows_before": int(df.shape[0]),
        "columns": list(df.columns),
        "x_axis": None,
        "y_axis": None
    }

    if intent == "preview_data":
        result = df.head(10)
        summary["message"] = "Showing first 10 rows"
        return result, summary

    if intent == "describe_data":
        result = df.describe(include="all").fillna("")
        summary["message"] = "Dataset statistical summary"
        return result.reset_index(), summary

    if intent == "missing_values_check":
        result = df.isna().sum().reset_index()
        result.columns = ["column", "missing_count"]
        summary["message"] = "Missing values by column"
        summary["x_axis"] = "column"
        summary["y_axis"] = "missing_count"
        return result, summary

    numeric_cols = [c for c in target_columns if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
    first_numeric = numeric_cols[0] if numeric_cols else None
    first_target = _safe_col(df, target_columns[0] if target_columns else None)

    if intent == "top_n" and first_target:
        counts = df[first_target].value_counts().head(top_n).reset_index()
        counts.columns = [first_target, "count"]
        summary["top_category"] = counts.iloc[0].to_dict() if not counts.empty else {}
        summary["x_axis"] = first_target
        summary["y_axis"] = "count"
        return counts, summary

    if intent == "group_summary" and group_by:
        if first_numeric and metric in {"sum", "mean", "max", "min"}:
            val_col = f"{metric}_{first_numeric}"
            grouped = getattr(df.groupby(group_by)[first_numeric], metric)().reset_index()
            grouped.columns = [group_by, val_col]
            result = grouped
            summary["y_axis"] = val_col
        else:
            result = df.groupby(group_by).size().reset_index(name="count")
            summary["y_axis"] = "count"
            
        if sort_order in {"asc", "desc"}:
            result = result.sort_values(by=result.columns[-1], ascending=(sort_order == "asc"))
            
        summary["x_axis"] = group_by
        summary["top_rows"] = result.head(5).to_dict(orient="records")
        return result, summary

    if intent == "trend_over_time":
        for col in df.columns:
            if "date" in col.lower() or "time" in col.lower():
                if not pd.api.types.is_datetime64_any_dtype(df[col]):
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except Exception:
                        pass

        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        date_col = date_cols[0] if date_cols else None
        
        if date_col and first_numeric:
            temp = df[[date_col, first_numeric]].dropna().copy()
            temp["period"] = temp[date_col].dt.to_period("M").astype(str)
            val_col = f"{metric if metric else 'mean'}_{first_numeric}"
            
            agg_func = metric if metric in {"sum", "mean", "max", "min"} else "mean"
            result = temp.groupby("period")[first_numeric].agg(agg_func).reset_index(name=val_col)
            
            summary["x_axis"] = "period"
            summary["y_axis"] = val_col
            summary["message"] = f"Calculated baseline progression for {first_numeric}"
            return result, summary

    return result, summary