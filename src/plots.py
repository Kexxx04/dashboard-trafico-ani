import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.catalogs import METRIC_LABELS


def empty_figure(title: str, message: str = "No hay datos para mostrar"):
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=16),
    )
    fig.update_layout(
        template="plotly_dark",
        title=title,
        title_x=0,
        height=400,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def estilo_fig(fig, xaxis_title="", yaxis_title="Valor", height=430):
    fig.update_layout(
        template="plotly_dark",
        title_x=0,
        height=height,
        margin=dict(l=20, r=20, t=60, b=20),
        legend_title_text="",
    )
    fig.update_xaxes(title=xaxis_title)
    fig.update_yaxes(title=yaxis_title)
    return fig


def _dynamic_title(total_items: int, top_n: int, singular: str, plural: str, top_label: str):
    if total_items <= 1:
        return singular
    if total_items <= top_n:
        return f"{plural} ({total_items})"
    return f"{top_label} {top_n}"


def plot_trafico_anual(df: pd.DataFrame):
    if "anio" not in df.columns or "cantidadtrafico" not in df.columns:
        return empty_figure("Tráfico por año")

    resumen = (
        df.dropna(subset=["anio"])
        .groupby("anio", as_index=False)["cantidadtrafico"]
        .sum()
        .sort_values("anio")
    )

    if resumen.empty:
        return empty_figure("Tráfico por año")

    fig = px.bar(
        resumen,
        x="anio",
        y="cantidadtrafico",
        text="cantidadtrafico",
        title="Tráfico total por año",
    )
    fig.update_traces(texttemplate="%{text:,.0f}")
    return estilo_fig(fig, "Año", "Cantidad de tráfico")


def plot_trafico_mensual(df: pd.DataFrame):
    if "desde" not in df.columns or "cantidadtrafico" not in df.columns:
        return empty_figure("Tendencia mensual del tráfico")

    aux = df.dropna(subset=["desde"]).copy()
    if aux.empty:
        return empty_figure("Tendencia mensual del tráfico")

    aux["periodo"] = aux["desde"].dt.to_period("M").astype(str)

    resumen = (
        aux.groupby("periodo", as_index=False)["cantidadtrafico"]
        .sum()
        .sort_values("periodo")
    )

    fig = px.line(
        resumen,
        x="periodo",
        y="cantidadtrafico",
        markers=True,
        title="Tendencia mensual del tráfico",
    )
    return estilo_fig(fig, "Periodo", "Cantidad de tráfico")


def plot_heatmap_mes_categoria(df: pd.DataFrame):
    category_col = "categoriatarifa_norm" if "categoriatarifa_norm" in df.columns else "categoriatarifa"
    required = {"mes_nombre", category_col, "cantidadtrafico"}

    if not required.issubset(df.columns):
        return empty_figure("Heatmap tráfico por mes y categoría")

    aux = df.dropna(subset=["mes_nombre", category_col]).copy()
    if aux.empty:
        return empty_figure("Heatmap tráfico por mes y categoría")

    meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ]

    tabla = (
        aux.groupby(["mes_nombre", category_col], as_index=False)["cantidadtrafico"]
        .sum()
    )

    fig = px.density_heatmap(
        tabla,
        x=category_col,
        y="mes_nombre",
        z="cantidadtrafico",
        histfunc="sum",
        category_orders={"mes_nombre": meses},
        title="Concentración de tráfico por mes y categoría",
    )
    fig.update_xaxes(tickangle=-45)
    return estilo_fig(fig, "Categoría tarifaria", "Mes", height=520)


def plot_top_peajes_trafico(df: pd.DataFrame, top_n: int = 10):
    if "peaje" not in df.columns or "cantidadtrafico" not in df.columns:
        return empty_figure("Tráfico por peaje")

    resumen_total = (
        df.groupby("peaje", as_index=False)["cantidadtrafico"]
        .sum()
        .sort_values("cantidadtrafico", ascending=False)
    )

    if resumen_total.empty:
        return empty_figure("Tráfico por peaje")

    total_peajes = len(resumen_total)
    resumen = resumen_total.head(top_n).sort_values("cantidadtrafico", ascending=True)

    titulo = _dynamic_title(
        total_peajes,
        top_n,
        "Tráfico del peaje seleccionado",
        "Tráfico de peajes seleccionados",
        "Top peajes con mayor tráfico",
    )

    fig = px.bar(
        resumen,
        x="cantidadtrafico",
        y="peaje",
        orientation="h",
        text="cantidadtrafico",
        title=titulo,
    )
    fig.update_traces(texttemplate="%{text:,.0f}")
    return estilo_fig(fig, "Cantidad de tráfico", "Peaje")


def plot_participacion_peajes(df: pd.DataFrame, top_n: int = 8):
    if "peaje" not in df.columns or "cantidadtrafico" not in df.columns:
        return empty_figure("Participación del tráfico por peaje")

    resumen_total = (
        df.groupby("peaje", as_index=False)["cantidadtrafico"]
        .sum()
        .sort_values("cantidadtrafico", ascending=False)
    )

    if resumen_total.empty:
        return empty_figure("Participación del tráfico por peaje")

    total_general = resumen_total["cantidadtrafico"].sum()
    resumen = resumen_total.head(top_n).copy()

    if len(resumen) == 1:
        return empty_figure(
            "Participación del tráfico por peaje",
            "Con un solo peaje seleccionado este gráfico no aporta comparación.",
        )

    suma_top = resumen["cantidadtrafico"].sum()
    otros = total_general - suma_top

    if otros > 0:
        fila_otros = pd.DataFrame(
            [{"peaje": "Otros", "cantidadtrafico": otros}]
        )
        resumen = pd.concat([resumen, fila_otros], ignore_index=True)

    fig = px.pie(
        resumen,
        names="peaje",
        values="cantidadtrafico",
        title="Participación del tráfico por peaje",
    )
    return estilo_fig(fig, "", "")


def plot_trafico_categoria(df: pd.DataFrame):
    category_col = "categoriatarifa_norm" if "categoriatarifa_norm" in df.columns else "categoriatarifa"

    if category_col not in df.columns or "cantidadtrafico" not in df.columns:
        return empty_figure("Tráfico por categoría tarifaria")

    resumen = (
        df.groupby(category_col, as_index=False)["cantidadtrafico"]
        .sum()
        .sort_values("cantidadtrafico", ascending=False)
    )

    if resumen.empty:
        return empty_figure("Tráfico por categoría tarifaria")

    fig = px.bar(
        resumen,
        x=category_col,
        y="cantidadtrafico",
        title="Tráfico por categoría tarifaria",
    )
    fig.update_xaxes(tickangle=-45)
    return estilo_fig(fig, "Categoría tarifaria", "Cantidad de tráfico", height=500)


def plot_tarifa_promedio_categoria(df: pd.DataFrame):
    category_col = "categoriatarifa_norm" if "categoriatarifa_norm" in df.columns else "categoriatarifa"

    if category_col not in df.columns or "valortarifa" not in df.columns:
        return empty_figure("Tarifa promedio por categoría")

    resumen = (
        df.groupby(category_col, as_index=False)["valortarifa"]
        .mean()
        .sort_values("valortarifa", ascending=False)
    )

    if resumen.empty:
        return empty_figure("Tarifa promedio por categoría")

    fig = px.bar(
        resumen,
        x=category_col,
        y="valortarifa",
        title="Tarifa promedio por categoría",
    )
    fig.update_xaxes(tickangle=-45)
    return estilo_fig(fig, "Categoría tarifaria", "Valor tarifa promedio", height=500)


def plot_evasores_peaje(df: pd.DataFrame, top_n: int = 10):
    if "peaje" not in df.columns or "cantidadevasores" not in df.columns:
        return empty_figure("Evasores por peaje")

    resumen_total = (
        df.groupby("peaje", as_index=False)["cantidadevasores"]
        .sum()
        .sort_values("cantidadevasores", ascending=False)
    )

    if resumen_total.empty:
        return empty_figure("Evasores por peaje")

    total_peajes = len(resumen_total)
    resumen = resumen_total.head(top_n).sort_values("cantidadevasores", ascending=True)

    titulo = _dynamic_title(
        total_peajes,
        top_n,
        "Evasores del peaje seleccionado",
        "Evasores en peajes seleccionados",
        "Top peajes con más evasores",
    )

    fig = px.bar(
        resumen,
        x="cantidadevasores",
        y="peaje",
        orientation="h",
        text="cantidadevasores",
        title=titulo,
    )
    fig.update_traces(texttemplate="%{text:,.0f}")
    return estilo_fig(fig, "Cantidad de evasores", "Peaje")


def plot_exentos_peaje(df: pd.DataFrame, top_n: int = 10):
    if "peaje" not in df.columns or "cantidadexentos787" not in df.columns:
        return empty_figure("Exentos por peaje")

    resumen_total = (
        df.groupby("peaje", as_index=False)["cantidadexentos787"]
        .sum()
        .sort_values("cantidadexentos787", ascending=False)
    )

    if resumen_total.empty:
        return empty_figure("Exentos por peaje")

    total_peajes = len(resumen_total)
    resumen = resumen_total.head(top_n).sort_values("cantidadexentos787", ascending=True)

    titulo = _dynamic_title(
        total_peajes,
        top_n,
        "Exentos del peaje seleccionado",
        "Exentos en peajes seleccionados",
        "Top peajes con más exentos",
    )

    fig = px.bar(
        resumen,
        x="cantidadexentos787",
        y="peaje",
        orientation="h",
        text="cantidadexentos787",
        title=titulo,
    )
    fig.update_traces(texttemplate="%{text:,.0f}")
    return estilo_fig(fig, "Cantidad de exentos", "Peaje")


def plot_tasa_evasion_peaje(df: pd.DataFrame, top_n: int = 10):
    if not {"peaje", "cantidadevasores", "cantidadtrafico"}.issubset(df.columns):
        return empty_figure("Tasa de evasión por peaje")

    resumen_total = (
        df.groupby("peaje", as_index=False)
        .agg(
            evasores=("cantidadevasores", "sum"),
            trafico=("cantidadtrafico", "sum"),
        )
    )

    resumen_total["tasa_evasion"] = (
        resumen_total["evasores"] / resumen_total["trafico"].replace(0, pd.NA)
    ) * 100

    resumen_total = resumen_total.sort_values("tasa_evasion", ascending=False)

    if resumen_total.empty:
        return empty_figure("Tasa de evasión por peaje")

    total_peajes = len(resumen_total)
    resumen = resumen_total.head(top_n).sort_values("tasa_evasion", ascending=True)

    titulo = _dynamic_title(
        total_peajes,
        top_n,
        "Tasa de evasión del peaje seleccionado",
        "Tasa de evasión en peajes seleccionados",
        "Top peajes por tasa de evasión",
    )

    fig = px.bar(
        resumen,
        x="tasa_evasion",
        y="peaje",
        orientation="h",
        title=titulo,
        text="tasa_evasion",
    )
    fig.update_traces(texttemplate="%{text:.4f}%")
    return estilo_fig(fig, "Tasa de evasión (%)", "Peaje")


def plot_tarifa_vs_trafico(df: pd.DataFrame):
    if "valortarifa" not in df.columns or "cantidadtrafico" not in df.columns:
        return empty_figure("Relación entre tarifa y tráfico")

    aux = df.dropna(subset=["valortarifa", "cantidadtrafico"]).copy()
    if aux.empty:
        return empty_figure("Relación entre tarifa y tráfico")

    color_col = None
    if "categoriatarifa_norm" in aux.columns:
        color_col = "categoriatarifa_norm"
    elif "categoriatarifa" in aux.columns:
        color_col = "categoriatarifa"

    fig = px.scatter(
        aux,
        x="valortarifa",
        y="cantidadtrafico",
        color=color_col,
        hover_data=["peaje"] if "peaje" in aux.columns else None,
        title="Relación entre valor de tarifa y tráfico",
    )
    return estilo_fig(fig, "Valor tarifa", "Cantidad de tráfico")


def plot_compare_peajes(df: pd.DataFrame, peajes: list[str], metric: str):
    if not peajes or len(peajes) < 2:
        return empty_figure("Comparación entre peajes", "Selecciona al menos 2 peajes")

    if "desde" not in df.columns or metric not in df.columns or "peaje" not in df.columns:
        return empty_figure("Comparación entre peajes")

    aux = df[df["peaje"].isin(peajes)].dropna(subset=["desde"]).copy()
    if aux.empty:
        return empty_figure("Comparación entre peajes")

    aux["periodo"] = aux["desde"].dt.to_period("M").astype(str)

    resumen = (
        aux.groupby(["periodo", "peaje"], as_index=False)[metric]
        .sum()
        .sort_values("periodo")
    )

    metric_label = METRIC_LABELS.get(metric, metric)

    fig = px.line(
        resumen,
        x="periodo",
        y=metric,
        color="peaje",
        markers=True,
        title=f"Comparación mensual de {metric_label.lower()} entre peajes",
    )
    return estilo_fig(fig, "Periodo", metric_label)