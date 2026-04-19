import pandas as pd


def _fmt_int(value) -> str:
    if pd.isna(value):
        return "N/D"
    return f"{int(round(value)):,}".replace(",", ".")


def _fmt_pct(value) -> str:
    if pd.isna(value):
        return "N/D"
    return f"{value:.2f}%"


def safe_mode(df: pd.DataFrame, column: str, default="N/D"):
    if column in df.columns and not df[column].dropna().empty:
        return df[column].mode().iloc[0]
    return default


def build_executive_insights(df: pd.DataFrame) -> list[str]:
    insights = []

    if "cantidadtrafico" in df.columns and not df.empty:
        total_trafico = df["cantidadtrafico"].sum()
        insights.append(f"El tráfico total del período filtrado es de {_fmt_int(total_trafico)} vehículos.")

    if {"peaje", "cantidadtrafico"}.issubset(df.columns) and not df.empty:
        top_peaje = (
            df.groupby("peaje", as_index=False)["cantidadtrafico"]
            .sum()
            .sort_values("cantidadtrafico", ascending=False)
            .head(1)
        )
        if not top_peaje.empty:
            insights.append(
                f"El peaje con mayor tráfico es {top_peaje.iloc[0]['peaje']} con {_fmt_int(top_peaje.iloc[0]['cantidadtrafico'])} vehículos."
            )

    if {"categoriatarifa", "cantidadtrafico"}.issubset(df.columns) and not df.empty:
        top_cat = (
            df.groupby("categoriatarifa", as_index=False)["cantidadtrafico"]
            .sum()
            .sort_values("cantidadtrafico", ascending=False)
            .head(1)
        )
        if not top_cat.empty:
            insights.append(
                f"La categoría tarifaria dominante es {top_cat.iloc[0]['categoriatarifa']} con {_fmt_int(top_cat.iloc[0]['cantidadtrafico'])} vehículos."
            )

    if {"peaje", "tasa_evasion"}.issubset(df.columns) and not df["tasa_evasion"].dropna().empty:
        worst_evasion = (
            df.groupby("peaje", as_index=False)["tasa_evasion"]
            .mean()
            .sort_values("tasa_evasion", ascending=False)
            .head(1)
        )
        if not worst_evasion.empty:
            insights.append(
                f"La mayor tasa promedio de evasión aparece en {worst_evasion.iloc[0]['peaje']} con {_fmt_pct(worst_evasion.iloc[0]['tasa_evasion'])}."
            )

    if {"desde", "cantidadtrafico"}.issubset(df.columns) and not df["desde"].dropna().empty:
        aux = df.dropna(subset=["desde"]).copy()
        aux["periodo"] = aux["desde"].dt.to_period("M").astype(str)
        top_month = (
            aux.groupby("periodo", as_index=False)["cantidadtrafico"]
            .sum()
            .sort_values("cantidadtrafico", ascending=False)
            .head(1)
        )
        if not top_month.empty:
            insights.append(
                f"El mes con mayor tráfico en el conjunto filtrado es {top_month.iloc[0]['periodo']} con {_fmt_int(top_month.iloc[0]['cantidadtrafico'])} vehículos."
            )

    return insights


def build_section_insights(df: pd.DataFrame) -> dict:
    insights = {
        "temporal": [],
        "peajes": [],
        "categorias": [],
        "riesgo": [],
    }

    if {"anio", "cantidadtrafico"}.issubset(df.columns) and not df["anio"].dropna().empty:
        resumen = (
            df.groupby("anio", as_index=False)["cantidadtrafico"]
            .sum()
            .sort_values("anio")
        )
        if len(resumen) >= 2:
            first_year = resumen.iloc[0]
            last_year = resumen.iloc[-1]
            if first_year["cantidadtrafico"] > 0:
                variacion = ((last_year["cantidadtrafico"] - first_year["cantidadtrafico"]) / first_year["cantidadtrafico"]) * 100
                insights["temporal"].append(
                    f"Entre {int(first_year['anio'])} y {int(last_year['anio'])}, el tráfico cambió {_fmt_pct(variacion)}."
                )

    if {"peaje", "cantidadtrafico"}.issubset(df.columns):
        top_peajes = (
            df.groupby("peaje", as_index=False)["cantidadtrafico"]
            .sum()
            .sort_values("cantidadtrafico", ascending=False)
            .head(3)
        )
    if not top_peajes.empty:
        nombres = ", ".join(top_peajes["peaje"].tolist())
        cantidad = len(top_peajes)

        if cantidad == 1:
            insights["peajes"].append(f"El peaje con mayor flujo es: {nombres}.")
        elif cantidad == 2:
            insights["peajes"].append(f"Los dos peajes con mayor flujo son: {nombres}.")
        else:
            insights["peajes"].append(f"Los tres peajes con mayor flujo son: {nombres}.")

    if {"categoriatarifa", "valortarifa"}.issubset(df.columns):
        top_tarifa = (
            df.groupby("categoriatarifa", as_index=False)["valortarifa"]
            .mean()
            .sort_values("valortarifa", ascending=False)
            .head(1)
        )
        if not top_tarifa.empty:
            insights["categorias"].append(
                f"La categoría con mayor tarifa promedio es {top_tarifa.iloc[0]['categoriatarifa']}."
            )

    if {"cantidadevasores", "cantidadtrafico"}.issubset(df.columns):
        total_trafico = df["cantidadtrafico"].sum()
        total_evasores = df["cantidadevasores"].sum()
        if total_trafico > 0:
            tasa_global = (total_evasores / total_trafico) * 100
            insights["riesgo"].append(
                f"La tasa global de evasión del período filtrado es {_fmt_pct(tasa_global)}."
            )

    return insights