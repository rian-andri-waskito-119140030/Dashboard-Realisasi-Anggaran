import streamlit as pd_st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Konfigurasi Halaman Website (Wide Mode)
pd_st.set_page_config(page_title="Dashboard Realisasi Anggaran", layout="wide")

# ==========================================
# 1. KONFIGURASI KATEGORI & WARNA
# ==========================================
CATEGORIES_MAPPING = {
    "Program Penunjang Urusan Pemerintahan Daerah Kab/Kota": [
        "program penunjang urusan pemerintahan daerah kabupaten/kota"
    ],
    "Informasi Publik": [
        "relasi media",
        "monitoring informasi kebijakan, opini, dan aspirasi publik",
        "pelayanan informasi publik",
        "diseminasi informasi"
    ],
    "Komunikasi Publik": [
        "kemitraan komunikasi dengan komunitas informasi masyarakat",
        "pengelolaan media komunikasi publik",
        "penyusunan konten",
        "penguatan kapasitas sumber daya manusia komunikasi publik"
    ],
    "Program Pengelolaan Aplikasi Informatika": [
        "program pengelolaan aplikasi informatika"
    ],
    "Urusan Pemerintahan Bidang Statistik": [
        "urusan pemerintahan bidang statistik"
    ],
    "Urusan Pemerintahan Bidang Persandian": [
        "urusan pemerintahan bidang persandian"
    ]
}

CATEGORY_COLORS = {
    "Program Penunjang Urusan Pemerintahan Daerah Kab/Kota": "#1A73E8", 
    "Informasi Publik": "#188038",                                      
    "Komunikasi Publik": "#F9AB00",                                     
    "Program Pengelolaan Aplikasi Informatika": "#00ACC1",              
    "Urusan Pemerintahan Bidang Statistik": "#D93025",                  
    "Urusan Pemerintahan Bidang Persandian": "#9334E6"                  
}

# Warna tetap untuk RAK vs Realisasi (sesuai permintaan)
RAK_COLOR = "#1A73E8"        # Biru
REALISASI_COLOR = "#D93025"  # Merah

MONTHS_FILE = ["januari", "februari", "maret", "april", "mei", "juni", "juli"]
MONTHS_FULL = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli"]
MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul"]

# ==========================================
# 2. FUNGSI PENGOLAHAN DATA
# ==========================================
def clean_number(val):
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    val_str = str(val).replace('.', '').replace(',', '.') 
    try:
        return float(val_str)
    except ValueError:
        return 0.0

@pd_st.cache_data
def load_data():
    file_rak = "RAK_Belanja_2.16.2.20.2.21.01.0000 - Dinas Komunikasi dan Informatika (2).xlsx"
    
    # 1. Load RAK
    rak_result = {cat: {m: 0.0 for m in MONTHS_FILE} for cat in CATEGORIES_MAPPING}
    if os.path.exists(file_rak):
        df_rak = pd.read_excel(file_rak, header=2) 
        df_rak['Uraian'] = df_rak['Uraian'].astype(str).str.strip().str.lower()
        for cat_name, keywords in CATEGORIES_MAPPING.items():
            rows = df_rak[df_rak['Uraian'].isin(keywords)]
            for m in MONTHS_FILE:
                col_name = m.capitalize()
                if col_name in rows.columns:
                    rak_result[cat_name][m] = rows[col_name].apply(clean_number).sum()
                    
    # 2. Load LRA
    lra_result = {cat: {m: 0.0 for m in MONTHS_FILE} for cat in CATEGORIES_MAPPING}
    for m in MONTHS_FILE:
        file_lra = f"lra_{m}.xlsx" 
        if os.path.exists(file_lra):
            df_lra = pd.read_excel(file_lra, skiprows=4)
            df_lra['Uraian'] = df_lra['Unnamed: 4'].astype(str).str.strip().str.lower()
            for cat_name, keywords in CATEGORIES_MAPPING.items():
                rows = df_lra[df_lra['Uraian'].isin(keywords)]
                op = rows['Unnamed: 6'].apply(clean_number).sum()
                mod = rows['Unnamed: 8'].apply(clean_number).sum()
                lra_result[cat_name][m] = op + mod
                
    # 3. Bentuk Dataframe Panjang + Kolom Format Teks Akuntansi untuk Hover
    records = []
    for cat in CATEGORIES_MAPPING.keys():
        for i, m_file in enumerate(MONTHS_FILE):
            m_name = MONTHS_FULL[i]
            rak_val = rak_result[cat][m_file]
            lra_val = lra_result[cat][m_file]
            
            # Format string akuntansi Indonesia (titik sebagai pemisah ribuan)
            rak_str = f"Rp {rak_val:,.0f}".replace(",", ".") if rak_val > 0 else "Rp 0"
            lra_str = f"Rp {lra_val:,.0f}".replace(",", ".") if lra_val > 0 else "Rp 0"
            
            records.append({
                "Bidang": cat,
                "Bulan": m_name,
                "Bulan_Short": MONTHS_SHORT[i],
                "RAK (Rencana)": rak_val,
                "Realisasi (Aktual)": lra_val,
                "RAK_Str": rak_str,
                "Realisasi_Str": lra_str
            })
            
    return pd.DataFrame(records)

df_all = load_data()

# ==========================================
# 3. TAMPILAN DASHBOARD STREAMLIT (LIGHT MODE)
# ==========================================
pd_st.title("📊 Dashboard Interaktif Rencana & Realisasi Anggaran")
pd_st.markdown("Dinas Komunikasi dan Informatika — Pemantauan Kinerja Penyerapan Anggaran")

# Sidebar Filter Pilihan Bidang
pd_st.sidebar.header("Pengaturan Tampilan")
selected_categories = pd_st.sidebar.multiselect(
    "Pilih Bidang:",
    options=list(CATEGORIES_MAPPING.keys()),
    default=list(CATEGORIES_MAPPING.keys())
)

df_filtered = df_all[df_all["Bidang"].isin(selected_categories)]

# ------------------------------------------
# 4. GRAFIK UTAMA — SATU GRAFIK BATANG TEGAK (DILEBUR, TIDAK DIPISAH PER BIDANG)
# ------------------------------------------
pd_st.subheader("📈 Perbandingan RAK vs Realisasi per Bulan & Bidang (Satu Grafik Batang)")

# Label pendek di dalam batang (contoh: 350 Jt / 1,55 M) agar tidak terlalu panjang
def format_short(v):
    if v <= 0:
        return ""
    if v >= 1_000_000_000:
        return f"{v/1_000_000_000:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".") + " M"
    if v >= 1_000_000:
        return f"{v/1_000_000:,.0f}".replace(",", ".") + " Jt"
    return f"{v:,.0f}".replace(",", ".")

n_cats_main = len(selected_categories)

if n_cats_main > 0:
    # Urutkan data: Bulan (grup terluar) -> Bidang (di dalam tiap bulan)
    bulan_order = {m: i for i, m in enumerate(MONTHS_FULL)}
    bidang_order = {b: i for i, b in enumerate(selected_categories)}
    df_plot = df_filtered.copy()
    df_plot["bulan_idx"] = df_plot["Bulan"].map(bulan_order)
    df_plot["bidang_idx"] = df_plot["Bidang"].map(bidang_order)
    df_plot = df_plot.sort_values(["bulan_idx", "bidang_idx"])

    bulan_list = df_plot["Bulan"].tolist()
    bidang_list = df_plot["Bidang"].tolist()
    rak_vals = df_plot["RAK (Rencana)"].tolist()
    lra_vals = df_plot["Realisasi (Aktual)"].tolist()
    rak_strs = df_plot["RAK_Str"].tolist()
    lra_strs = df_plot["Realisasi_Str"].tolist()
    rak_short = [format_short(v) for v in rak_vals]
    lra_short = [format_short(v) for v in lra_vals]

    fig_main = go.Figure()

    # Sumbu-x dua tingkat: [Bulan, Bidang] -> Bidang tampil sebagai label per batang,
    # Bulan tampil sebagai pengelompok yang membawahi semua bidang pada bulan itu.
    fig_main.add_trace(go.Bar(
        x=[bulan_list, bidang_list],
        y=rak_vals,
        name="RAK (Rencana)",
        marker_color=RAK_COLOR,
        text=rak_short,
        textposition="inside",
        textangle=-90,
        textfont=dict(size=8, color="white"),
        insidetextanchor="middle",
        customdata=rak_strs,
        hovertemplate="<b>RAK (Rencana)</b><br>%{customdata}<extra></extra>"
    ))

    fig_main.add_trace(go.Bar(
        x=[bulan_list, bidang_list],
        y=lra_vals,
        name="Realisasi (Aktual)",
        marker_color=REALISASI_COLOR,
        text=lra_short,
        textposition="inside",
        textangle=-90,
        textfont=dict(size=8, color="white"),
        insidetextanchor="middle",
        customdata=lra_strs,
        hovertemplate="<b>Realisasi (Aktual)</b><br>%{customdata}<extra></extra>"
    ))

    fig_main.update_layout(
        barmode="group",
        template="plotly_white",
        hovermode="closest",
        height=650,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=40, r=40, t=70, b=130)
    )

    fig_main.update_yaxes(
        tickprefix="Rp ",
        tickformat=",.0f",
        separatethousands=True
    )
    fig_main.update_xaxes(tickfont=dict(size=9), automargin=True)

    pd_st.plotly_chart(fig_main, use_container_width=True)
else:
    pd_st.warning("Silakan pilih minimal satu bidang di sidebar.")

# ------------------------------------------
# 5. GRAFIK DETAIL PER BIDANG — GRAFIK BATANG (GRID 3x2)
# ------------------------------------------
pd_st.subheader("🔍 Perbandingan RAK vs Realisasi per Bidang (Grafik Batang)")
pd_st.markdown("🔵 **RAK (Rencana)** | 🔴 **Realisasi (Aktual)**")

n_cats = len(selected_categories)
if n_cats > 0:
    rows = (n_cats + 1) // 2
    fig = make_subplots(
        rows=rows, cols=2, 
        subplot_titles=selected_categories,
        vertical_spacing=0.15,
        horizontal_spacing=0.08
    )
    
    for idx, cat in enumerate(selected_categories):
        r = (idx // 2) + 1
        c = (idx % 2) + 1
        
        df_cat = df_all[df_all["Bidang"] == cat]
        x_vals = df_cat["Bulan"].tolist()
        rak_vals = df_cat["RAK (Rencana)"].tolist()
        lra_vals = df_cat["Realisasi (Aktual)"].tolist()
        rak_strs = df_cat["RAK_Str"].tolist()
        lra_strs = df_cat["Realisasi_Str"].tolist()
        
        rak_short = [format_short(v) for v in rak_vals]
        lra_short = [format_short(v) for v in lra_vals]

        # 1. Batang RAK (Biru)
        fig.add_trace(
            go.Bar(
                x=x_vals, y=rak_vals,
                name='RAK (Rencana)',
                marker_color=RAK_COLOR,
                legendgroup='rak',
                showlegend=(idx == 0),
                customdata=rak_strs,
                hovertemplate="RAK: %{customdata}<extra></extra>",
                text=rak_short,
                textposition="inside",
                textangle=-90,
                textfont=dict(size=8, color="white"),
                insidetextanchor="middle"
            ),
            row=r, col=c
        )
        
        # 2. Batang Realisasi (Merah)
        fig.add_trace(
            go.Bar(
                x=x_vals, y=lra_vals,
                name='Realisasi (Aktual)',
                marker_color=REALISASI_COLOR,
                legendgroup='lra',
                showlegend=(idx == 0),
                customdata=lra_strs,
                hovertemplate="Realisasi: %{customdata}<extra></extra>",
                text=lra_short,
                textposition="inside",
                textangle=-90,
                textfont=dict(size=8, color="white"),
                insidetextanchor="middle"
            ),
            row=r, col=c
        )

    fig.update_layout(
        barmode="group",
        height=350 * rows,
        template="plotly_white",
        hovermode="closest",
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Format sumbu Y subplots agar menggunakan pemisah ribuan
    fig.update_yaxes(tickprefix="Rp ", tickformat=",.0f", separatethousands=True)

    pd_st.plotly_chart(fig, use_container_width=True)
else:
    pd_st.warning("Silakan pilih minimal satu bidang di sidebar.")

# ------------------------------------------
# 6. TABEL RANGKUMAN (FORMAT AKUNTANSI)
# ------------------------------------------
with pd_st.expander("📁 Lihat Data Tabel Rangkuman (Format Per Bulan: RAK vs Realisasi)"):
    df_filtered = df_all[df_all["Bidang"].isin(selected_categories)]
    if not df_filtered.empty:
        df_pivot = df_filtered.pivot(index="Bidang", columns="Bulan", values=["RAK (Rencana)", "Realisasi (Aktual)"])
        
        new_columns = []
        for m in MONTHS_FULL:
            new_columns.append(("RAK (Rencana)", m))
            new_columns.append(("Realisasi (Aktual)", m))
            
        df_pivot = df_pivot[new_columns]
        
        def format_accounting(val):
            if pd.isna(val) or val == 0:
                return "-"
            return f"{val:,.0f}".replace(",", ".")
            
        df_display = df_pivot.map(format_accounting)
        pd_st.dataframe(df_display, use_container_width=True)
    else:
        pd_st.warning("Belum ada bidang yang dipilih.")
