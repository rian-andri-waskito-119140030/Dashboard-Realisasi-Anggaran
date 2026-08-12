import streamlit as pd_st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Konfigurasi Halaman Website (Wide Mode)
pd_st.set_page_config(page_title="Dashboard Realisasi Anggaran", layout="wide")

# CSS Tambahan untuk Responsif Tabel di HP
pd_st.markdown("""
    <style>
    [data-testid="stDataFrame"] {
        width: 100%;
        overflow-x: auto;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 1. KONFIGURASI 6 KATEGORI UTAMA & WARNA
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

MONTHS_FILE = ["januari", "februari", "maret", "april", "mei", "juni", "juli"]
MONTHS_FULL = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli"]
MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul"]

# ==========================================
# 2. FUNGSI PENGOLAHAN DATA
# ==========================================
def clean_number(val):
    try:
        if pd.isna(val) or val is None or val == "" or str(val).strip() == "-": 
            return 0.0
        if isinstance(val, (int, float)): 
            return float(val)
            
        val_str = str(val).strip().replace('Rp', '').replace(' ', '')
        val_str = val_str.replace('.', '').replace(',', '.') 
        return float(val_str)
    except Exception:
        return 0.0

# Fungsi untuk menyingkat angka di dalam batang grafik agar rapi
def format_short_label(val):
    if val == 0:
        return ""
    elif val >= 1_000_000_000:
        return f"{val / 1_000_000_000:.1f} M".replace('.', ',')
    elif val >= 1_000_000:
        return f"{val / 1_000_000:,.0f} Jt".replace(',', '.')
    else:
        return f"{val:,.0f}".replace(',', '.')

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
                    rak_result[cat_name][m] = rows[col_name].apply(clean_number).astype(float).sum()
                    
    # 2. Load LRA
    lra_result = {cat: {m: 0.0 for m in MONTHS_FILE} for cat in CATEGORIES_MAPPING}
    for m in MONTHS_FILE:
        file_lra = f"lra_{m}.xlsx" 
        if os.path.exists(file_lra):
            df_lra = pd.read_excel(file_lra, skiprows=4)
            df_lra['Uraian'] = df_lra['Unnamed: 4'].astype(str).str.strip().str.lower()
            for cat_name, keywords in CATEGORIES_MAPPING.items():
                rows = df_lra[df_lra['Uraian'].isin(keywords)]
                
                op = rows['Unnamed: 6'].apply(clean_number).astype(float).sum()
                mod = rows['Unnamed: 8'].apply(clean_number).astype(float).sum()
                
                lra_result[cat_name][m] = float(op) + float(mod)
                
    # 3. Bentuk Dataframe Panjang
    records = []
    for cat in CATEGORIES_MAPPING.keys():
        for i, m_file in enumerate(MONTHS_FILE):
            m_name = MONTHS_FULL[i]
            rak_val = float(rak_result[cat][m_file])
            lra_val = float(lra_result[cat][m_file])
            
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
# 3. TAMPILAN DASHBOARD STREAMLIT
# ==========================================
pd_st.title("📊 Dashboard Realisasi Anggaran")
pd_st.markdown("Dinas Komunikasi dan Informatika")

# Sidebar Filter Pilihan Bidang & Bulan
pd_st.sidebar.header("Filter Data")
selected_categories = pd_st.sidebar.multiselect(
    "Pilih Bidang:",
    options=list(CATEGORIES_MAPPING.keys()),
    default=list(CATEGORIES_MAPPING.keys())
)

selected_months = pd_st.sidebar.multiselect(
    "Pilih Bulan:",
    options=MONTHS_FULL,
    default=MONTHS_FULL
)

df_filtered = df_all[(df_all["Bidang"].isin(selected_categories)) & (df_all["Bulan"].isin(selected_months))]

# ------------------------------------------
# 4A. GRAFIK UTAMA 1 (TOTAL PER BULAN)
# ------------------------------------------
pd_st.subheader("📈 Total Keseluruhan per Bulan (RAK vs Realisasi)")

if not df_filtered.empty:
    df_agg_bulan = df_filtered.groupby("Bulan", sort=False)[["RAK (Rencana)", "Realisasi (Aktual)"]].sum().reset_index()
    
    fig_bulan = go.Figure()
    
    fig_bulan.add_trace(go.Bar(
        x=df_agg_bulan["Bulan"],
        y=df_agg_bulan["RAK (Rencana)"],
        name="Total RAK (Biru)",
        marker_color="#1A73E8",
        text=[format_short_label(v) for v in df_agg_bulan["RAK (Rencana)"]],
        textposition="auto",
        hovertemplate="Bulan: %{x}<br>Total RAK: Rp %{y:,.0f}<extra></extra>".replace(",", ".")
    ))
    
    fig_bulan.add_trace(go.Bar(
        x=df_agg_bulan["Bulan"],
        y=df_agg_bulan["Realisasi (Aktual)"],
        name="Total Realisasi (Merah)",
        marker_color="#D93025",
        text=[format_short_label(v) for v in df_agg_bulan["Realisasi (Aktual)"]],
        textposition="auto",
        hovertemplate="Bulan: %{x}<br>Total Realisasi: Rp %{y:,.0f}<extra></extra>".replace(",", ".")
    ))

    fig_bulan.update_layout(
        barmode='group',
        template="plotly_white",
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, font=dict(size=11)),
        margin=dict(l=10, r=10, t=20, b=80),
        autosize=True
    )

    fig_bulan.update_yaxes(tickprefix="Rp ", tickformat=",.0f", separatethousands=True)
    pd_st.plotly_chart(fig_bulan, use_container_width=True)

# ------------------------------------------
# 4B. GRAFIK UTAMA 2 (TOTAL PER BIDANG - MENGETAHUI YANG RENDAH)
# ------------------------------------------
pd_st.subheader("📉 Akumulasi Total per Bidang (RAK vs Realisasi)")
pd_st.markdown("Menyoroti bidang mana yang realisasinya paling tertinggal.")

if not df_filtered.empty:
    df_agg_bidang = df_filtered.groupby("Bidang", sort=False)[["RAK (Rencana)", "Realisasi (Aktual)"]].sum().reset_index()
    
    fig_bidang = go.Figure()
    
    fig_bidang.add_trace(go.Bar(
        x=df_agg_bidang["Bidang"],
        y=df_agg_bidang["RAK (Rencana)"],
        name="Total RAK (Biru)",
        marker_color="#1A73E8",
        text=[format_short_label(v) for v in df_agg_bidang["RAK (Rencana)"]],
        textposition="auto",
        hovertemplate="Bidang: %{x}<br>Total RAK: Rp %{y:,.0f}<extra></extra>".replace(",", ".")
    ))
    
    fig_bidang.add_trace(go.Bar(
        x=df_agg_bidang["Bidang"],
        y=df_agg_bidang["Realisasi (Aktual)"],
        name="Total Realisasi (Merah)",
        marker_color="#D93025",
        text=[format_short_label(v) for v in df_agg_bidang["Realisasi (Aktual)"]],
        textposition="auto",
        hovertemplate="Bidang: %{x}<br>Total Realisasi: Rp %{y:,.0f}<extra></extra>".replace(",", ".")
    ))

    fig_bidang.update_layout(
        barmode='group',
        template="plotly_white",
        legend=dict(orientation="h", yanchor="top", y=-0.5, xanchor="center", x=0.5, font=dict(size=11)),
        margin=dict(l=10, r=10, t=20, b=120),
        autosize=True
    )

    fig_bidang.update_yaxes(tickprefix="Rp ", tickformat=",.0f", separatethousands=True)
    pd_st.plotly_chart(fig_bidang, use_container_width=True)

# ------------------------------------------
# 5. GRAFIK DETAIL PER BIDANG (BULANAN)
# ------------------------------------------
pd_st.subheader("🔍 Detail RAK vs Realisasi per Bidang")

n_cats = len(selected_categories)
if n_cats > 0:
    df_detail = df_all[(df_all["Bidang"].isin(selected_categories)) & (df_all["Bulan"].isin(selected_months))]
    
    fig = make_subplots(
        rows=n_cats, cols=1, 
        subplot_titles=selected_categories,
        vertical_spacing=0.06
    )
    
    for idx, cat in enumerate(selected_categories, start=1):
        df_cat = df_detail[df_detail["Bidang"] == cat]
        x_vals = df_cat["Bulan"].tolist()
        rak_vals = df_cat["RAK (Rencana)"].tolist()
        lra_vals = df_cat["Realisasi (Aktual)"].tolist()
        rak_strs = df_cat["RAK_Str"].tolist()
        lra_strs = df_cat["Realisasi_Str"].tolist()
        
        # Batang RAK (Biru)
        fig.add_trace(
            go.Bar(
                x=x_vals, y=rak_vals,
                name='RAK',
                marker_color='#1A73E8', 
                text=[format_short_label(v) for v in rak_vals],
                textposition='auto',
                legendgroup='rak',
                showlegend=(idx == 1),
                customdata=rak_strs,
                hovertemplate="RAK: %{customdata}<extra></extra>"
            ),
            row=idx, col=1
        )
        
        # Batang Realisasi (Merah)
        fig.add_trace(
            go.Bar(
                x=x_vals, y=lra_vals,
                name='Realisasi',
                marker_color='#D93025', 
                text=[format_short_label(v) for v in lra_vals],
                textposition='auto',
                legendgroup='lra',
                showlegend=(idx == 1),
                customdata=lra_strs,
                hovertemplate="Realisasi: %{customdata}<extra></extra>"
            ),
            row=idx, col=1
        )

    fig.update_layout(
        barmode='group', 
        height=320 * n_cats,
        template="plotly_white",
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=40, b=20)
    )
    
    fig.update_yaxes(tickprefix="Rp ", tickformat=",.0f", separatethousands=True)
    pd_st.plotly_chart(fig, use_container_width=True)
else:
    pd_st.warning("Silakan pilih minimal satu bidang di sidebar.")

# ------------------------------------------
# 6. TABEL RANGKUMAN 
# ------------------------------------------
with pd_st.expander("📁 Lihat Tabel Rangkuman RAK vs Realisasi"):
    df_tabel = df_all[df_all["Bidang"].isin(selected_categories)]
    if not df_tabel.empty:
        df_pivot = df_tabel.pivot(index="Bidang", columns="Bulan", values=["RAK (Rencana)", "Realisasi (Aktual)"])
        
        new_columns = []
        for m in MONTHS_FULL:
            new_columns.append(("RAK (Rencana)", m))
            new_columns.append(("Realisasi (Aktual)", m))
            
        df_pivot = df_pivot[new_columns]
        
        df_pivot.columns = [f"{col[0]} - {col[1]}" for col in df_pivot.columns]
        df_pivot = df_pivot.reset_index()
        
        def format_accounting(val):
            if pd.isna(val) or val == 0:
                return "-"
            return f"{val:,.0f}".replace(",", ".")
            
        for col in df_pivot.columns:
            if col != "Bidang":
                df_pivot[col] = df_pivot[col].apply(format_accounting)
                
        pd_st.dataframe(df_pivot, use_container_width=True, hide_index=True)
    else:
        pd_st.warning("Belum ada data untuk ditampilkan di tabel.")
