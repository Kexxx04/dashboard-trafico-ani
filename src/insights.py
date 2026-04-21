import pandas as pd


def _fmt_int(value) -> str:
    if pd.isna(value):
        return "N/D"
    return f"{int(round(value)):,}".replace(",", ".")


def _fmt_pct(value) -> str:
    if pd.isna(value):
        return "N/D"
    if abs(value) < 0.01:
        return f"{value:.4f}%"
    return f"{value:.2f}%"


def safe_mode(df: pd.DataFrame, column: str, default="N/D"):
    if column in df.columns and not df[column].dropna().empty:
        return df[column].mode().iloc[0]
    return default


def build_executive_insights(df: pd.DataFrame) -> list[str]:
    insights = []

    if "cantidadtrafico" in df.columns and not df.empty:
        total_trafico = df["cantidadtrafico"].sum()
        insights.append(
            f"El tráfico total del período filtrado es de {_fmt_int(total_trafico)} vehículos."
        )

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

    if {"anio", "cantidadtrafico"}.issubset(df.columns) and not df["anio"].dropna().empty:
        top_year = (
            df.groupby("anio", as_index=False)["cantidadtrafico"]
            .sum()
            .sort_values("cantidadtrafico", ascending=False)
            .head(1)
        )
        if not top_year.empty:
            insights.append(
                f"El año con mayor tráfico es {int(top_year.iloc[0]['anio'])} con {_fmt_int(top_year.iloc[0]['cantidadtrafico'])} vehículos."
            )

    if {"peaje", "cantidadtrafico"}.issubset(df.columns):
        part = (
            df.groupby("peaje", as_index=False)["cantidadtrafico"]
            .sum()
            .sort_values("cantidadtrafico", ascending=False)
        )
        if len(part) >= 2:
            total = part["cantidadtrafico"].sum()
            primero = part.iloc[0]
            porcentaje = (primero["cantidadtrafico"] / total) * 100 if total > 0 else pd.NA
            insights.append(
                f"{primero['peaje']} concentra {_fmt_pct(porcentaje)} del tráfico del conjunto filtrado."
            )

    return insights


def build_section_insights(df: pd.DataFrame) -> dict:
    insights = {
        "temporal": [],
        "peajes": [],
        "categorias": [],
        "riesgo": [],
    }

    # TEMPORAL
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
                variacion = (
                    (last_year["cantidadtrafico"] - first_year["cantidadtrafico"])
                    / first_year["cantidadtrafico"]
                ) * 100
                insights["temporal"].append(
                    f"Entre {int(first_year['anio'])} y {int(last_year['anio'])}, el tráfico cambió {_fmt_pct(variacion)}."
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
            insights["temporal"].append(
                f"El mes con mayor tráfico del período filtrado es {top_month.iloc[0]['periodo']} con {_fmt_int(top_month.iloc[0]['cantidadtrafico'])} vehículos."
            )

    # PEAJES
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

        if len(top_peajes) >= 1:
            total = df["cantidadtrafico"].sum()
            principal = top_peajes.iloc[0]
            porcentaje = (principal["cantidadtrafico"] / total) * 100 if total > 0 else pd.NA
            insights["peajes"].append(
                f"{principal['peaje']} representa {_fmt_pct(porcentaje)} del tráfico del conjunto filtrado."
            )

    # CATEGORIAS
    if {"categoriatarifa_norm", "cantidadtrafico"}.issubset(df.columns):
        top_categoria = (
            df.groupby("categoriatarifa_norm", as_index=False)["cantidadtrafico"]
            .sum()
            .sort_values("cantidadtrafico", ascending=False)
            .head(1)
        )
        if not top_categoria.empty:
            insights["categorias"].append(
                f"La categoría con mayor tráfico es {top_categoria.iloc[0]['categoriatarifa_norm']} con {_fmt_int(top_categoria.iloc[0]['cantidadtrafico'])} vehículos."
            )

    if {"categoriatarifa_norm", "valortarifa"}.issubset(df.columns):
        top_tarifa = (
            df.groupby("categoriatarifa_norm", as_index=False)["valortarifa"]
            .mean()
            .sort_values("valortarifa", ascending=False)
            .head(1)
        )
        if not top_tarifa.empty:
            insights["categorias"].append(
                f"La categoría con mayor tarifa promedio es {top_tarifa.iloc[0]['categoriatarifa_norm']}."
            )

    # RIESGO
    if {"cantidadevasores", "cantidadtrafico"}.issubset(df.columns):
        total_trafico = df["cantidadtrafico"].sum()
        total_evasores = df["cantidadevasores"].sum()
        if total_trafico > 0:
            tasa_global = (total_evasores / total_trafico) * 100
            insights["riesgo"].append(
                f"La tasa global de evasión del período filtrado es {_fmt_pct(tasa_global)}."
            )

    if {"peaje", "cantidadevasores", "cantidadtrafico"}.issubset(df.columns):
        peor = (
            df.groupby("peaje", as_index=False)
            .agg(
                evasores=("cantidadevasores", "sum"),
                trafico=("cantidadtrafico", "sum"),
            )
        )
        peor["tasa_evasion"] = (
            peor["evasores"] / peor["trafico"].replace(0, pd.NA)
        ) * 100
        peor = peor.sort_values("tasa_evasion", ascending=False).head(1)

        if not peor.empty:
            insights["riesgo"].append(
                f"La mayor tasa de evasión se observa en {peor.iloc[0]['peaje']} con {_fmt_pct(peor.iloc[0]['tasa_evasion'])}."
            )

    return insights


def build_peaje_summary_table(df: pd.DataFrame, top_n: int = 10, mostrar_todos: bool = False) -> pd.DataFrame:
    required = {"peaje", "cantidadtrafico", "cantidadevasores", "cantidadexentos787", "valortarifa"}
    if not required.issubset(df.columns):
        return pd.DataFrame()

    aux = df.copy()
    aux["tasa_evasion_fila"] = (
        aux["cantidadevasores"] / aux["cantidadtrafico"].replace(0, pd.NA)
    ) * 100

    resumen = (
        aux.groupby("peaje", as_index=False)
        .agg(
            trafico_total=("cantidadtrafico", "sum"),
            evasores=("cantidadevasores", "sum"),
            exentos=("cantidadexentos787", "sum"),
            tarifa_promedio=("valortarifa", "mean"),
            tasa_promedio_evasion=("tasa_evasion_fila", "mean"),
        )
        .sort_values("trafico_total", ascending=False)
    )

    resumen["tasa_evasion"] = (
        resumen["evasores"] / resumen["trafico_total"].replace(0, pd.NA)
    ) * 100

    if not mostrar_todos:
        resumen = resumen.head(top_n)

    return resumen