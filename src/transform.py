import re
import unicodedata
import pandas as pd

from src.catalogs import CATEGORY_MEANINGS, UNKNOWN_CATEGORY_MESSAGE


def _normalize_string(value: str) -> str:
    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("utf-8")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_normalize_string(col) for col in df.columns]
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates().copy()


def convert_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "desde" in df.columns:
        df["desde"] = pd.to_datetime(df["desde"], errors="coerce")
        df["anio"] = df["desde"].dt.year
        df["mes_num"] = df["desde"].dt.month
        df["dia"] = df["desde"].dt.day
        df["trimestre"] = df["desde"].dt.quarter

        meses = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre",
        }
        df["mes_nombre"] = df["mes_num"].map(meses)

    if "hasta" in df.columns:
        df["hasta"] = pd.to_datetime(df["hasta"], errors="coerce")

    return df


def normalize_text_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()

    missing_tokens = {
        "": pd.NA,
        "none": pd.NA,
        "None": pd.NA,
        "nan": pd.NA,
        "NaN": pd.NA,
        "null": pd.NA,
        "Null": pd.NA,
        "n/a": pd.NA,
        "N/A": pd.NA,
    }

    for col in columns:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.strip()
                .str.replace(r"\s+", " ", regex=True)
                .replace(missing_tokens)
                .fillna("Sin dato")
            )

    return df


def normalize_category_value(value):
    if pd.isna(value):
        return "Sin dato"

    text = str(value).strip().upper()
    text = text.replace("CATEGORÍA", "CATEGORIA")
    text = text.replace("CAT.", "CAT")
    text = " ".join(text.split())

    roman_map = {
        "1": "I",
        "2": "II",
        "3": "III",
        "4": "IV",
        "5": "V",
        "6": "VI",
        "7": "VII",
    }

    if text in roman_map:
        return roman_map[text]

    if text.startswith("CATEGORIA "):
        suffix = text.replace("CATEGORIA ", "")
        return roman_map.get(suffix, suffix)

    if text.startswith("CAT "):
        suffix = text.replace("CAT ", "")
        return roman_map.get(suffix, suffix)

    return text


def add_category_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "categoriatarifa" in df.columns:
        df["categoriatarifa_norm"] = df["categoriatarifa"].apply(normalize_category_value)
        df["categoria_significado"] = df["categoriatarifa_norm"].map(CATEGORY_MEANINGS)
        df["categoria_conocida"] = df["categoria_significado"].notna()
        df["categoria_significado"] = df["categoria_significado"].fillna(UNKNOWN_CATEGORY_MESSAGE)

    return df


def create_derived_variables(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if {"cantidadevasores", "cantidadtrafico"}.issubset(df.columns):
        df["tasa_evasion"] = (
            df["cantidadevasores"] / df["cantidadtrafico"].replace(0, pd.NA)
        ) * 100

    if {"cantidadexentos787", "cantidadtrafico"}.issubset(df.columns):
        df["tasa_exentos"] = (
            df["cantidadexentos787"] / df["cantidadtrafico"].replace(0, pd.NA)
        ) * 100

    return df


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = clean_columns(df)
    df = remove_duplicates(df)

    df = convert_numeric_columns(
        df,
        [
            "idpeaje",
            "valortarifa",
            "cantidadtrafico",
            "cantidadevasores",
            "cantidadexentos787",
        ],
    )

    df = parse_dates(df)

    df = normalize_text_columns(
        df,
        ["peaje", "categoriatarifa"]
    )

    df = create_derived_variables(df)
    df = add_category_labels(df)

    return df