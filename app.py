import streamlit as st
import pandas as pd

from src.extract import load_data, sync_data, get_sync_info
from src.transform import prepare_data
from src.plots import (
    plot_trafico_anual,
    plot_trafico_mensual,
    plot_heatmap_mes_categoria,
    plot_top_peajes_trafico,
    plot_participacion_peajes,
    plot_trafico_categoria,
    plot_tarifa_promedio_categoria,
    plot_evasores_peaje,
    plot_exentos_peaje,
    plot_tasa_evasion_peaje,
    plot_tarifa_vs_trafico,
    plot_compare_peajes,
)
from src.insights import (
    build_executive_insights,
    build_section_insights,
    build_peaje_summary_table,
    safe_mode,
)
from src.catalogs import CATEGORY_MEANINGS


FILTER_KEYS = [
    "flt_top_n",
    "flt_years",
    "flt_peajes",
    "flt_categories",
    "flt_dates",
    "flt_compare_peajes",
    "flt_compare_metric",
]


def configurar_pagina():
    st.set_page_config(
        page_title="Dashboard Tráfico Vehicular ANI",
        layout="wide",
    )


def mostrar_encabezado():
    st.title("Dashboard de Tráfico Vehicular ANI")
    st.caption("Análisis interactivo del tráfico vehicular, evasión y exenciones en peajes")


def sincronizar_datos():
    try:
        sync_result = sync_data(force=False)

        if sync_result.get("updated"):
            st.success(
                f"Datos actualizados automáticamente. Registros descargados: {sync_result.get('rows', 'N/D')}"
            )

        if st.button("Forzar actualización ahora"):
            manual_result = sync_data(force=True)
            if manual_result.get("updated"):
                st.success(
                    f"Se actualizó el CSV local. Registros descargados: {manual_result.get('rows', 'N/D')}"
                )
            else:
                st.info("La fuente no tenía cambios.")

        sync_info = get_sync_info()
        if sync_info:
            st.caption(
                f"Última revisión: {sync_info.get('last_check', 'N/D')} | "
                f"Última actualización local: {sync_info.get('last_update', 'N/D')} | "
                f"Registros: {sync_info.get('rows', 'N/D')}"
            )
    except Exception as e:
        st.error("No fue posible conectarse a la fuente de datos.")
        st.code(str(e))


@st.cache_data(show_spinner=False)
def cargar_y_preparar_datos_cached():
    df = load_data(auto_sync=False)
    df = prepare_data(df)
    return df


def limpiar_filtros():
    for key in FILTER_KEYS:
        st.session_state.pop(key, None)


def aplicar_filtros(df: pd.DataFrame):
    st.sidebar.header("Filtros")
    st.sidebar.caption("Usa estos filtros para refinar el análisis del dashboard.")

    if st.sidebar.button("Restablecer filtros", use_container_width=True):
        limpiar_filtros()
        st.rerun()

    top_n = st.sidebar.slider("Top N para rankings", 5, 20, 10, key="flt_top_n")

    if "anio" in df.columns and not df["anio"].dropna().empty:
        anios = sorted([int(a) for a in df["anio"].dropna().unique()])
        anios_sel = st.sidebar.multiselect("Años", anios, default=anios, key="flt_years")
        if anios_sel:
            df = df[df["anio"].isin(anios_sel)]

    if "peaje" in df.columns and not df["peaje"].dropna().empty:
        peajes = sorted(df["peaje"].dropna().unique())
        peajes_sel = st.sidebar.multiselect("Peajes", peajes, key="flt_peajes")
        if peajes_sel:
            df = df[df["peaje"].isin(peajes_sel)]

    categoria_col = "categoriatarifa_norm" if "categoriatarifa_norm" in df.columns else "categoriatarifa"
    if categoria_col in df.columns and not df[categoria_col].dropna().empty:
        categorias = sorted(df[categoria_col].dropna().unique())
        categorias_sel = st.sidebar.multiselect(
            "Categorías tarifarias",
            categorias,
            key="flt_categories",
        )
        if categorias_sel:
            df = df[df[categoria_col].isin(categorias_sel)]

    if "desde" in df.columns and not df["desde"].dropna().empty:
        fecha_min = df["desde"].min().date()
        fecha_max = df["desde"].max().date()

        rango = st.sidebar.date_input(
            "Rango de fechas",
            value=(fecha_min, fecha_max),
            min_value=fecha_min,
            max_value=fecha_max,
            key="flt_dates",
        )
        if isinstance(rango, tuple) and len(rango) == 2:
            inicio, fin = rango
            df = df[(df["desde"].dt.date >= inicio) & (df["desde"].dt.date <= fin)]

    compare_candidates = []
    if "peaje" in df.columns and not df["peaje"].dropna().empty:
        compare_candidates = st.sidebar.multiselect(
            "Comparar peajes",
            sorted(df["peaje"].dropna().unique()),
            max_selections=3,
            key="flt_compare_peajes",
        )

    compare_metric = st.sidebar.selectbox(
        "Métrica para comparar",
        ["cantidadtrafico", "cantidadevasores", "cantidadexentos787"],
        key="flt_compare_metric",
    )

    return df, top_n, compare_candidates, compare_metric


def mostrar_panel_fuente(df: pd.DataFrame):
    with st.expander("Resumen técnico de la fuente", expanded=False):
        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Registros", f"{len(df):,}".replace(",", "."))
        c2.metric("Peajes únicos", df["peaje"].nunique() if "peaje" in df.columns else 0)

        if "desde" in df.columns and not df["desde"].dropna().empty:
            c3.metric("Fecha mínima", str(df["desde"].min().date()))
            c4.metric("Fecha máxima", str(df["desde"].max().date()))
        else:
            c3.metric("Fecha mínima", "N/D")
            c4.metric("Fecha máxima", "N/D")


def mostrar_como_usar():
    with st.expander("Cómo usar el dashboard", expanded=False):
        st.markdown(
            """
            - Usa la barra lateral para filtrar por año, peaje, categoría y rango de fechas.
            - El comparador permite analizar hasta 3 peajes en una misma métrica.
            - En la sección de datos puedes descargar el subconjunto filtrado en CSV.
            - Si cambian los datos en la fuente, puedes usar **Forzar actualización ahora**.
            """
        )


def mostrar_resumen_categorias():
    with st.expander("Resumen de categorías tarifarias", expanded=False):
        for code, meaning in CATEGORY_MEANINGS.items():
            st.markdown(f"**{code}** — {meaning}")
        st.caption(
            "Nota: algunas categorías especiales del dataset pueden depender de la fuente "
            "o del peaje y no siempre pertenecen al catálogo base."
        )


def mostrar_kpis(df: pd.DataFrame):
    total_trafico = int(df["cantidadtrafico"].sum()) if "cantidadtrafico" in df.columns else 0
    total_evasores = int(df["cantidadevasores"].sum()) if "cantidadevasores" in df.columns else 0
    total_exentos = int(df["cantidadexentos787"].sum()) if "cantidadexentos787" in df.columns else 0

    tasa_global = "N/D"
    if total_trafico > 0:
        tasa_global = f"{(total_evasores / total_trafico) * 100:.2f}%"

    tarifa_prom = "N/D"
    if "valortarifa" in df.columns and not df["valortarifa"].dropna().empty:
        tarifa_prom = f"{df['valortarifa'].mean():,.0f}".replace(",", ".")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Tráfico total", f"{total_trafico:,}".replace(",", "."))
    col2.metric("Evasores", f"{total_evasores:,}".replace(",", "."))
    col3.metric("Exentos", f"{total_exentos:,}".replace(",", "."))
    col4.metric("Tarifa promedio", tarifa_prom)
    col5.metric("Peaje dominante", safe_mode(df, "peaje"))
    col6.metric("Tasa global de evasión", tasa_global)


def mostrar_insights_resumen(df: pd.DataFrame):
    st.subheader("Hallazgos clave")
    for text in build_executive_insights(df)[:4]:
        st.info(text)


def render_plot(fig, key_name: str):
    st.plotly_chart(fig, use_container_width=True, key=key_name)


def mostrar_tabla_ejecutiva(df: pd.DataFrame, top_n: int, mostrar_todos: bool = False):
    tabla = build_peaje_summary_table(df, top_n=top_n, mostrar_todos=mostrar_todos)
    if tabla.empty:
        return

    tabla = tabla.rename(
        columns={
            "peaje": "Peaje",
            "trafico_total": "Tráfico total",
            "evasores": "Evasores",
            "exentos": "Exentos",
            "tasa_evasion": "Tasa de evasión (%)",
            "tasa_promedio_evasion": "Tasa promedio de evasión (%)",
            "tarifa_promedio": "Tarifa promedio",
        }
    )

    tabla["Tráfico total"] = tabla["Tráfico total"].map(
        lambda x: f"{int(x):,}".replace(",", ".") if pd.notna(x) else "N/D"
    )
    tabla["Evasores"] = tabla["Evasores"].map(
        lambda x: f"{int(x):,}".replace(",", ".") if pd.notna(x) else "N/D"
    )
    tabla["Exentos"] = tabla["Exentos"].map(
        lambda x: f"{int(x):,}".replace(",", ".") if pd.notna(x) else "N/D"
    )
    tabla["Tasa de evasión (%)"] = tabla["Tasa de evasión (%)"].map(
        lambda x: f"{x:.4f}" if pd.notna(x) else "N/D"
    )
    tabla["Tasa promedio de evasión (%)"] = tabla["Tasa promedio de evasión (%)"].map(
        lambda x: f"{x:.4f}" if pd.notna(x) else "N/D"
    )
    tabla["Tarifa promedio"] = tabla["Tarifa promedio"].map(
        lambda x: f"{x:,.2f}".replace(",", ".") if pd.notna(x) else "N/D"
    )

    titulo = "Resumen ejecutivo por peaje"
    if mostrar_todos:
        titulo += " (todos los peajes)"
    else:
        titulo += f" (top {top_n})"

    st.caption(titulo)
    st.dataframe(
        tabla,
        use_container_width=True,
        key="tabla_resumen_ejecutivo",
    )


def mostrar_tabs(df: pd.DataFrame, top_n: int, compare_candidates: list[str], compare_metric: str):
    section_insights = build_section_insights(df)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "1. Resumen ejecutivo",
            "2. Evolución temporal",
            "3. Concentración por peajes",
            "4. Categorías y tarifas",
            "5. Riesgo operativo",
            "6. Comparador",
            "7. Datos",
        ]
    )

    with tab1:
        st.subheader("¿Qué está pasando en términos generales?")
        mostrar_insights_resumen(df)

        c1, c2 = st.columns(2)
        with c1:
            render_plot(plot_trafico_anual(df), "tab1_trafico_anual")
        with c2:
             render_plot(
                 plot_participacion_peajes(df, top_n=min(top_n, 8)),
                 "tab1_participacion_peajes",
             )

        mostrar_todos_peajes = st.checkbox(
         "Mostrar todos los peajes en la tabla ejecutiva",
         value=False,
         key="chk_mostrar_todos_peajes",
        )

        mostrar_tabla_ejecutiva(
            df,
            top_n=top_n,
            mostrar_todos=mostrar_todos_peajes,
        ) 
        
    with tab2:
        st.subheader("¿Cómo evoluciona el tráfico en el tiempo?")
        for text in section_insights["temporal"]:
            st.info(text)

        c1, c2 = st.columns(2)
        with c1:
            render_plot(plot_trafico_anual(df), "tab2_trafico_anual")
        with c2:
            render_plot(plot_trafico_mensual(df), "tab2_trafico_mensual")

        render_plot(plot_heatmap_mes_categoria(df), "tab2_heatmap_mes_categoria")

    with tab3:
        st.subheader("¿Qué peajes concentran más tráfico?")
        for text in section_insights["peajes"]:
            st.info(text)

        c1, c2 = st.columns(2)
        with c1:
            render_plot(plot_top_peajes_trafico(df, top_n=top_n), "tab3_top_peajes_trafico")
        with c2:
            render_plot(
                plot_participacion_peajes(df, top_n=min(top_n, 8)),
                "tab3_participacion_peajes",
            )

        if {"peaje", "cantidadtrafico"}.issubset(df.columns):
            resumen = (
                df.groupby("peaje", as_index=False)["cantidadtrafico"]
                .sum()
                .sort_values("cantidadtrafico", ascending=False)
                .head(top_n)
            )
            resumen.columns = ["Peaje", "Cantidad de tráfico"]

            cantidad_peajes_tabla = len(resumen)
            if cantidad_peajes_tabla == 1:
                st.caption("Resumen del peaje seleccionado")
            elif cantidad_peajes_tabla <= top_n:
                st.caption(f"Resumen de los {cantidad_peajes_tabla} peajes seleccionados")
            else:
                st.caption(f"Resumen de los top {cantidad_peajes_tabla} peajes por tráfico")

            st.dataframe(resumen, use_container_width=True, key="tabla_top_peajes")

    with tab4:
        st.subheader("¿Qué categorías tarifarias mueven más volumen y qué tarifa tienen?")
        for text in section_insights["categorias"]:
            st.info(text)

        c1, c2 = st.columns(2)
        with c1:
            render_plot(plot_trafico_categoria(df), "tab4_trafico_categoria")
        with c2:
            render_plot(
                plot_tarifa_promedio_categoria(df),
                "tab4_tarifa_promedio_categoria",
            )

        render_plot(plot_tarifa_vs_trafico(df), "tab4_tarifa_vs_trafico")

    with tab5:
        st.subheader("¿Dónde están los mayores riesgos operativos?")
        for text in section_insights["riesgo"]:
            st.info(text)

        c1, c2 = st.columns(2)
        with c1:
            render_plot(plot_evasores_peaje(df, top_n=top_n), "tab5_evasores_peaje")
        with c2:
            render_plot(plot_exentos_peaje(df, top_n=top_n), "tab5_exentos_peaje")

        render_plot(plot_tasa_evasion_peaje(df, top_n=top_n), "tab5_tasa_evasion_peaje")

    with tab6:
        st.subheader("Comparación entre peajes seleccionados")
        st.info("Selecciona al menos 2 peajes en la barra lateral para comparar la métrica elegida.")
        render_plot(
            plot_compare_peajes(df, compare_candidates, compare_metric),
            "tab6_comparador_peajes",
        )

    with tab7:
        st.subheader("Datos filtrados")
        st.dataframe(df.head(300), use_container_width=True, key="tabla_datos_filtrados")

        csv_descarga = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Descargar datos filtrados en CSV",
            data=csv_descarga,
            file_name="trafico_ani_filtrado.csv",
            mime="text/csv",
            key="download_csv_filtrado",
        )


def main():
    configurar_pagina()
    mostrar_encabezado()
    sincronizar_datos()

    try:
        df = cargar_y_preparar_datos_cached()
    except Exception as e:
        st.error("No fue posible cargar o transformar los datos.")
        st.code(str(e))
        return

    df, top_n, compare_candidates, compare_metric = aplicar_filtros(df)

    if df.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    mostrar_panel_fuente(df)
    mostrar_como_usar()
    mostrar_kpis(df)
    mostrar_resumen_categorias()
    st.divider()
    mostrar_tabs(df, top_n, compare_candidates, compare_metric)


if __name__ == "__main__":
    main()