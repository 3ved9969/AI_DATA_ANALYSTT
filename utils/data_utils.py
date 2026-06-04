import os
import pandas as pd
from werkzeug.utils import secure_filename

def allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    """
    Checks if the uploaded file has a permitted extension.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, upload_folder: str) -> str:
    """
    Saves the uploaded file safely to the workspace tracking directory.
    """
    filename = secure_filename(file.filename)
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, filename)
    file.save(path)
    return path


def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Ingests dataset files dynamically while protecting against common binary
    and multi-encoding character set traps (e.g., Unicode 0xa0 errors).
    """
    ext = os.path.splitext(file_path)[-1].lower()
    
    # Handle native Excel formats
    if ext in {".xlsx", ".xls"}:
        return pd.read_excel(file_path)
    
    # Handle CSV formats with adaptive encoding discovery fallbacks
    if ext == ".csv":
        # Ordered list of common encodings to try
        encodings = ["utf-8", "latin-1", "cp1252", "utf-16"]
        for encoding in encodings:
            try:
                return pd.read_csv(file_path, encoding=encoding, low_memory=False)
            except (UnicodeDecodeError, ValueError):
                continue
                
        # Lossy fallback if all standard map combinations fail
        return pd.read_csv(file_path, encoding="utf-8", errors="replace", low_memory=False)
        
    raise ValueError(f"Unsupported file format extension: {ext}")


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes column formats, trims whitespace, auto-detects true datatypes,
    and applies smart missing-value imputations without modifying raw inputs.
    """
    df = df.copy()
    
    # 1. Clean and normalize column names
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    df = df.drop_duplicates()

    # 2. Trim trailing/leading whitespace from text elements
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()

    # 3. Dynamic Datatype Inference Matrix (Datetimes and Numerics)
    threshold = max(3, int(0.6 * len(df)))
    
    for col in df.columns:
        if df[col].dtype == "object":
            # Strip string representations of nulls to avoid evaluation bugs
            cleaned_series = df[col].replace(["nan", "NaN", "None", "nat", "NaT"], pd.NA)
            
            # Check Datetime match
            converted_dt = pd.to_datetime(cleaned_series, errors="coerce")
            if converted_dt.notna().sum() > threshold:
                df[col] = converted_dt
                continue

            # Check Numeric match
            converted_num = pd.to_numeric(cleaned_series, errors="coerce")
            if converted_num.notna().sum() > threshold:
                df[col] = converted_num

    # 4. Bulletproof Missing Value Imputations
    for col in df.columns:
        # Avoid filling completely empty columns to prevent type collapse
        if df[col].isna().all():
            continue
            
        if pd.api.types.is_numeric_dtype(df[col]):
            # Fill numeric gaps with the median calculation
            df[col] = df[col].fillna(df[col].median())
        else:
            # Replace string artifacts with true pandas NA, then fill using the column mode
            df[col] = df[col].replace(["nan", "NaN", "None"], pd.NA)
            mode_series = df[col].dropna().mode()
            if not mode_series.empty:
                df[col] = df[col].fillna(mode_series.iloc[0])

    return df


def dataset_schema(df: pd.DataFrame) -> dict:
    """
    Generates metadata summaries describing structural dimensions and features.
    """
    return {
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "rows": int(df.shape[0]),
        "columns_count": int(df.shape[1]),
    }