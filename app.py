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
# 4. GRAFIK UTAMA — SATU GRAFIK BATANG, TETAP DIPISAH PER BIDANG (Jan-Jul)
# ------------------------------------------
pd_st.subheader("📈 Perbandingan RAK vs Realisasi per Bidang, Januari–Juli (Satu Grafik)")

# Ubah ke format panjang (long format): RAK & Realisasi jadi satu kolom "Tipe"
df_long = df_filtered.melt(
    id_vars=["Bidang", "Bulan"],
    value_vars=["RAK (Rencana)", "Realisasi (Aktual)"],
    var_name="Tipe",
    value_name="Nilai"
)
df_long["Bulan"] = pd.Categorical(df_long["Bulan"], categories=MONTHS_FULL, ordered=True)
df_long["Nilai_Str"] = df_long["Nilai"].apply(
    lambda v: f"Rp {v:,.0f}".replace(",", ".") if v > 0 else "Rp 0"
)

n_cats_main = len(selected_categories)
facet_wrap = 3 if n_cats_main > 2 else n_cats_main if n_cats_main > 0 else 1

if n_cats_main > 0:
    fig_main = px.bar(
        df_long,
        x="Bulan",
        y="Nilai",
        color="Tipe",
        barmode="group",
        facet_col="Bidang",
        facet_col_wrap=facet_wrap,
        category_orders={"Bulan": MONTHS_FULL},
        color_discrete_map={
            "RAK (Rencana)": RAK_COLOR,
            "Realisasi (Aktual)": REALISASI_COLOR
        },
        custom_data=["Nilai_Str", "Tipe"]
    )

    # Bersihkan judul facet agar hanya menampilkan nama Bidang
    fig_main.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    fig_main.update_traces(
        hovertemplate="<b>%{customdata[1]}</b><br>Bulan: %{x}<br>Nilai: %{customdata[0]}<extra></extra>"
    )

    fig_main.update_layout(
        template="plotly_white",
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=40, r=40, t=40, b=80),
        height=350 * ((n_cats_main + facet_wrap - 1) // facet_wrap)
    )

    fig_main.update_yaxes(
        tickprefix="Rp ",
        tickformat=",.0f",
        separatethousands=True,
        matches=None
    )
    fig_main.update_xaxes(matches=None)

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
        
        # 1. Batang RAK (Biru)
        fig.add_trace(
            go.Bar(
                x=x_vals, y=rak_vals,
                name='RAK (Rencana)',
                marker_color=RAK_COLOR,
                legendgroup='rak',
                showlegend=(idx == 0),
                customdata=rak_strs,
                hovertemplate="RAK: %{customdata}<extra></extra>"
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
                hovertemplate="Realisasi: %{customdata}<extra></extra>"
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
