import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# RESPONSIVE CONFIGURATION
# ==========================================
def get_column_config():
    """Return column ratios based on screen size"""
    return {
        "sidebar": [2, 1],
        "tab1_gap": [1.2, 1.8, 1.8],
        "tab2_benefit": [1.8, 0.8, 1.8],
        "tab3_result": [1, 1]
    }

# ==========================================
# FUNGSI PEMBANTU (Helper)
# ==========================================
def safe_parse(val):
    """Mengonversi input string (termasuk %) menjadi angka desimal untuk perhitungan."""
    if isinstance(val, str):
        clean_val = val.replace(",", "").replace("%", "").strip()
        try:
            num = float(clean_val)
            # Jika ada tanda %, bagi 100 (misal '90%' jadi 0.9)
            return num / 100 if "%" in val else num
        except:
            return 0.0
    return float(val)

# Inisialisasi session state untuk menyimpan data intervensi KPI
if "kpi_interventions" not in st.session_state:
    st.session_state.kpi_interventions = {}

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="IOH Partner Dashboard", layout="wide")

# Add responsive CSS
st.markdown("""
    <style>
    @media (max-width: 768px) {
        .stTabs [role="tablist"] button {
            font-size: 12px;
            padding: 8px 12px;
        }
        h1, h2, h3, h4 { font-size: 16px; }
        .stMetric { margin-bottom: 10px; }
    }
    @media (max-width: 480px) {
        h1 { font-size: 18px; }
        h3 { font-size: 14px; }
        .stMetric { margin-bottom: 8px; }
        .stContainer { padding: 8px; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏢 IOH Partner Decision System")
st.markdown("---")

# ==========================================
# 2. SIDEBAR (REFACTORED - COMPACT LAYOUT)
# ==========================================
with st.sidebar:
    st.header("📍 Navigasi Area")
    tipe_mitra = st.selectbox("Pilih Tipe Mitra:", ["SDP (Indosat)", "3KIOSK (Tri)"])
    if tipe_mitra == "SDP (Indosat)":
        wilayah_list = ["KEDAMEAN", "DAWARBLANDONG", "SANGKAPURA"]
    else:
        wilayah_list = ["SIDAYU", "BENJENG", "JATIREJO", "KEMLAGI", "BABAT"]
    pilih_wilayah = st.selectbox("Pilih Wilayah:", wilayah_list)
    
    st.divider()
    st.header("📅 Parameter Waktu")
    days_in_month = st.number_input("Jumlah Hari Bulan Ini", value=31)
    current_day = st.number_input("Tanggal Hari Ini", value=18)
    
    st.divider()
    st.header("⚙️ Konfigurasi KPI")
    num_kpis = st.number_input("Jumlah Variabel KPI", min_value=1, value=3)
    kpi_config = []
    
    # Custom CSS untuk compact sidebar
    sidebar_compact_css = """
    <style>
    .stNumberInput small, .stTextInput small { display: none; }
    .sidebar-kpi-section { margin-bottom: 16px; }
    .sidebar-kpi-header { 
        font-size: 13px; 
        font-weight: 700; 
        color: #1a202c;
        margin-bottom: 8px;
    }
    .sidebar-metric-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
    }
    .sidebar-metric-item {
        font-size: 11px;
    }
    .sidebar-metric-label {
        color: #4a5568;
        font-size: 10px;
        font-weight: 500;
        margin-bottom: 2px;
    }
    .sidebar-metric-value {
        color: #1a202c;
        font-size: 12px;
        font-weight: 700;
        line-height: 1.3;
    }
    .sidebar-metric-value-red {
        color: #dc2626;
        font-weight: 700;
    }
    .sidebar-metric-value-green {
        color: #16a34a;
        font-weight: 700;
    }
    </style>
    """
    st.markdown(sidebar_compact_css, unsafe_allow_html=True)
    
    for i in range(num_kpis):
        if i == 0: def_name, def_w = "Trade Supply", 40
        elif i == 1: def_name, def_w = "M2S Absolute", 40
        elif i == 2: def_name, def_w = "RGU FWA", 20
        else: def_name, def_w = f"KPI {i+1}", 0
        
        # KPI Name and Weight in one line
        col_name, col_weight = st.columns([3, 1], gap="small")
        with col_name:
            kn = st.text_input(f"KPI {i+1}", value=def_name, key=f"kn{i}", label_visibility="collapsed")
        with col_weight:
            kw = st.number_input(f"W", value=def_w, key=f"kw{i}", label_visibility="collapsed")
        
        kpi_config.append({"name": kn, "weight": kw/100})
        
        # Metric Grid - 2x2 layout
        if kn in st.session_state.kpi_interventions:
            interv = st.session_state.kpi_interventions[kn]
            gap_color = "sidebar-metric-value-red" if interv['gap'] > 0 else "sidebar-metric-value-green"
            
            with st.container(border=True):
                # Row 1: Target and Actual
                col1, col2 = st.columns(2, gap="small")
                with col1:
                    st.caption("🎯 Target")
                    st.markdown(f"<div class='sidebar-metric-value'>{interv['target']:,.0f}</div>", unsafe_allow_html=True)
                with col2:
                    st.caption("✅ Actual")
                    st.markdown(f"<div class='sidebar-metric-value'>{interv['actual']:,.0f}</div>", unsafe_allow_html=True)
                
                # Row 2: Gap and Biaya
                col3, col4 = st.columns(2, gap="small")
                with col3:
                    st.caption("⚠️ Gap")
                    st.markdown(f"<div class='sidebar-metric-value {gap_color}'>{interv['gap']:,.0f}</div>", unsafe_allow_html=True)
                with col4:
                    st.caption("💰 Biaya")
                    st.markdown(f"<div class='sidebar-metric-value'>Rp {interv['biaya']:,.0f}</div>", unsafe_allow_html=True)
        else:
            with st.container(border=True):
                st.caption("Data belum tersedia")

# ==========================================
# 3. DASHBOARD ATAS
# ==========================================
st.subheader("📝 Input Data Kinerja Utama")
st.caption("Masukkan Target & Actual untuk KPI yang akan dianalisis Biayanya.")

input_struct = {"Wilayah": [pilih_wilayah]}
for kpi in kpi_config:
    def_tgt = 250000000 if kpi['name'] == "Trade Supply" else 100
    input_struct[f"Tgt_{kpi['name']}"] = [str(def_tgt)]
    input_struct[f"Act_{kpi['name']}"] = [0]
input_struct["Compliance_RGU_Pct"] = [90]

df_input = pd.DataFrame(input_struct)
edited_df = st.data_editor(df_input, width='stretch', hide_index=True, key="main_editor")
row_data = edited_df.iloc[0]
run_rate = days_in_month / current_day if current_day > 0 else 0

# ==========================================
# 4. PANEL ANALISIS
# ==========================================
st.divider()
st.subheader("📊 Panel Analisis & Keputusan")
tab1, tab2, tab3 = st.tabs(["💰 Analisis Biaya (Cost)", "🧮 KALKULATOR BENEFIT", "⚖️ Hasil Akhir"])

# --- TAB 1 ---
total_biaya_push = 0
gap_omzet_global = 0 
achievement_ratios = []

# Custom CSS untuk Tab 1 - KPI Cards
custom_css_tab1 = """
<style>
.kpi-card {
    background-color: #ffffff;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    padding: 24px;
    margin-bottom: 24px;
    transition: box-shadow 0.3s ease;
}

.kpi-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.kpi-header {
    background: linear-gradient(135deg, #1f77b4 0%, #2b8cc4 100%);
    color: #ffffff;
    font-size: 24px;
    font-weight: 700;
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 20px;
    text-align: left;
    letter-spacing: 0.5px;
}

.kpi-label {
    font-size: 11px;
    font-weight: 700;
    color: #4a5568;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
    display: block;
}

.gap-amount-display {
    background: linear-gradient(135deg, #f5f7fa 0%, #eef2f7 100%);
    border: 2px solid #cbd5e1;
    border-radius: 8px;
    padding: 16px 12px;
    text-align: center;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 60px;
}

.gap-value-red {
    color: #dc2626;
    font-size: 18px;
    font-weight: 700;
}

.gap-value-green {
    color: #16a34a;
    font-size: 18px;
    font-weight: 700;
}

.cost-result-box {
    background: linear-gradient(135deg, #f8f9fa 0%, #e8ecf0 100%);
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    padding: 14px 10px;
    text-align: center;
    font-size: 15px;
    font-weight: 700;
    color: #1a202c;
}

.total-cost-container {
    background-color: #fef2f2;
    border-left: 5px solid #dc2626;
    border-radius: 6px;
    padding: 16px 18px;
    margin-top: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.total-cost-text {
    color: #991b1b;
    font-size: 16px;
    font-weight: 700;
}

.input-row-labels {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr;
    gap: 12px;
    margin-bottom: 12px;
}

.input-row-controls {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr;
    gap: 12px;
}

@media (max-width: 1200px) {
    .input-row-labels,
    .input-row-controls {
        grid-template-columns: 1fr 1fr;
    }
}

@media (max-width: 768px) {
    .input-row-labels,
    .input-row-controls {
        grid-template-columns: 1fr;
    }
    .kpi-header {
        font-size: 20px;
    }
}
</style>
"""

with tab1:
    st.markdown(custom_css_tab1, unsafe_allow_html=True)
    st.caption("Rincian Biaya Intervensi per KPI (Gap Analysis).")
    
    for i, kpi in enumerate(kpi_config):
        name = kpi['name']
        val_t = safe_parse(row_data[f"Tgt_{name}"])
        val_a = safe_parse(row_data[f"Act_{name}"])
        val_gap = max(0.0, val_t - val_a)
        ach_ratio = val_a / val_t if val_t > 0 else 0
        achievement_ratios.append(ach_ratio)
        if i == 0: gap_omzet_global = val_gap 
        
        # KPI Card Container
        st.markdown(f'<div class="kpi-card">', unsafe_allow_html=True)
        
        # KPI Header - Prominent Title
        st.markdown(f'<div class="kpi-header">📊 {name}</div>', unsafe_allow_html=True)
        
        # Create 4-column layout for inputs
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="small")
        
        # COLUMN 1: GAP AMOUNT
        with col1:
            st.markdown('<span class="kpi-label">Gap Amount</span>', unsafe_allow_html=True)
            color_class = "gap-value-red" if val_gap > 0 else "gap-value-green"
            st.markdown(f'<div class="gap-amount-display"><span class="{color_class}">Rp {val_gap:,.0f}</span></div>', unsafe_allow_html=True)
        
        # COLUMN 2: CATATAN (Notes)
        with col2:
            st.markdown('<span class="kpi-label">Catatan</span>', unsafe_allow_html=True)
            catatan = st.text_area("", value="-", height=60, label_visibility="collapsed", key=f"nt{i}")
        
        # COLUMN 3: SATUAN BIAYA (Unit)
        with col3:
            st.markdown('<span class="kpi-label">Satuan Biaya</span>', unsafe_allow_html=True)
            idx = 0 if i==0 else 1
            satuan = st.selectbox("", ["Rupiah (%)", "Picis (Rp)"], index=idx, key=f"st{i}", label_visibility="collapsed")
            
            # Input untuk perhitungan biaya
            if satuan == "Rupiah (%)":
                st.markdown('<span class="kpi-label" style="margin-top:12px">Persentase (%)</span>', unsafe_allow_html=True)
                pct = st.number_input(f"", value=1.0, step=0.1, key=f"cp{i}", label_visibility="collapsed")
                biaya_val = val_gap * (pct/100)
            else:
                st.markdown('<span class="kpi-label" style="margin-top:12px">Harga per Unit (Rp)</span>', unsafe_allow_html=True)
                prc = st.number_input(f"", value=5000, step=500, key=f"cr{i}", label_visibility="collapsed")
                biaya_val = val_gap * prc
        
        # COLUMN 4: ESTIMASI BIAYA (Cost Estimation)
        with col4:
            st.markdown('<span class="kpi-label">Estimasi Biaya</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="cost-result-box">Rp {biaya_val:,.0f}</div>', unsafe_allow_html=True)
        
        st.session_state.kpi_interventions[name] = {
            "target": val_t, "actual": val_a, "gap": val_gap, "biaya": biaya_val
        }
        total_biaya_push += biaya_val
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close KPI Card
    
    st.divider()
    
    # Total Biaya dengan styling yang menonjol
    st.markdown(f"""
    <div class="total-cost-container">
        <span class="total-cost-text">💰 TOTAL BIAYA PUSH:</span>
        <span class="total-cost-text">Rp {total_biaya_push:,.0f}</span>
    </div>
    """, unsafe_allow_html=True)

# --- TAB 2 ---
total_benefit_push = 0
total_buyback_denda = 0

with tab2:
    st.info("Kalkulator Rincian Benefit & Buyback.")
    st.markdown("### 1. Insentif (Final Fee KPI)")
    with st.container(border=True):
        col_i1, col_i2, col_i3, col_i4 = st.columns([1.5, 1, 1.5, 1.5], gap="small")
        with col_i1:
            prep_rev_val = safe_parse(row_data[f"Tgt_{kpi_config[0]['name']}"])
            prep_rev = st.number_input("Prepaid Revenue (Rp)", value=float(prep_rev_val), step=1000000.0)
        with col_i2:
            final_tarif = st.number_input("Final Tarif (%)", value=2.5, step=0.1) / 100
        with col_i3:
            score_kpi = st.number_input("Score KPI (%)", value=110.0, step=1.0) / 100
        with col_i4:
            ga_trade_val = safe_parse(row_data["Compliance_RGU_Pct"])
            ga_trade = st.number_input("GA Trade", value=float(ga_trade_val))
            st.caption("Min 80")
            
        failed_kpis = []
        if tipe_mitra == "SDP (Indosat)":
            for kpi in kpi_config:
                v_t = safe_parse(row_data[f"Tgt_{kpi['name']}"])
                v_a = safe_parse(row_data[f"Act_{kpi['name']}"])
                ach = (v_a / v_t) if v_t > 0 else 0
                if ach < 0.7: failed_kpis.append(kpi['name'])

        final_fee_res = prep_rev * final_tarif * score_kpi
        st.success(f"Hasil Final Fee KPI: **Rp {final_fee_res:,.0f}**")
        if failed_kpis:
            st.warning(f"**Informasi:** Performa pada **{', '.join(failed_kpis)}** masih di bawah ambang batas SDP (70%).")

    st.markdown("### 2. Trading Benefit (Margin)")
    with st.container(border=True):
        c_u1, c_u2, c_u3 = st.columns([1.8, 0.8, 1.8], gap="small")
        with c_u1:
            base_upfront_val = safe_parse(row_data[f"Tgt_{kpi_config[0]['name']}"])
            base_upfront = st.number_input("Basis Upfront", value=float(base_upfront_val), key="base_upfront_input")
        with c_u2:
            rate_upfront = st.number_input("Upfront (%)", value=1.5, step=0.1, key="rate_upfront_input") / 100
        with c_u3:
            res_upfront = base_upfront * rate_upfront
            st.markdown(f"<div style='margin-top:28px; background-color:#d4e8f7; padding:10px; border-radius:4px; text-align:center; border:1px solid #b3d9f2'><small style='color:#0066cc; font-size:12px'>Hasil Upfront: <b>Rp {res_upfront:,.0f}</b></small></div>", unsafe_allow_html=True)
        
        st.divider()
        c_in1, c_in2, c_in3 = st.columns([1.8, 0.8, 1.8], gap="small")
        with c_in1: base_inner = st.number_input("Basis Inner Trx", value=200000000.0, key="base_inner_input")
        with c_in2: rate_inner = st.number_input("Inner Trx (%)", value=2.5, step=0.1, key="rate_inner_input") / 100
        with c_in3:
            res_inner = base_inner * rate_inner
            st.markdown(f"<div style='margin-top:28px; background-color:#d4e8f7; padding:10px; border-radius:4px; text-align:center; border:1px solid #b3d9f2'><small style='color:#0066cc; font-size:12px'>Hasil Inner Trx: <b>Rp {res_inner:,.0f}</b></small></div>", unsafe_allow_html=True)
            
        st.divider()
        c_tb1, c_tb2, c_tb3 = st.columns([1.8, 0.8, 1.8], gap="small")
        with c_tb1: base_tert = st.number_input("Basis Tertiary B#", value=50000000.0, key="base_tert_input")
        with c_tb2: rate_tert = st.number_input("Tert B# (%)", value=0.5, step=0.1, key="rate_tert_input") / 100
        with c_tb3:
            res_tert = base_tert * rate_tert
            st.markdown(f"<div style='margin-top:28px; background-color:#d4e8f7; padding:10px; border-radius:4px; text-align:center; border:1px solid #b3d9f2'><small style='color:#0066cc; font-size:12px'>Hasil Tert B#: <b>Rp {res_tert:,.0f}</b></small></div>", unsafe_allow_html=True)

    st.markdown("### 3. Buyback Saldo DSE")
    with st.container(border=True):
        c_bb1, c_bb2, c_bb3 = st.columns([1.8, 0.8, 1.8], gap="small")
        with c_bb1: saldo_gap = st.number_input("Saldo DSE / Gap", value=float(gap_omzet_global), key="saldo_gap_input")
        with c_bb2: rate_buyback = st.number_input("Rate Buyback (%)", value=2.5, step=0.1, key="rate_buyback_input") / 100
        with c_bb3:
            total_buyback_denda = saldo_gap * rate_buyback
            st.markdown(f"<div style='margin-top:28px; background-color:#f7d4d4; padding:10px; border-radius:4px; text-align:center; border:1px solid #f0b3b3'><small style='color:#cc0000; font-size:12px'>Hasil Buyback: <b>Rp {total_buyback_denda:,.0f}</b></small></div>", unsafe_allow_html=True)

    total_benefit_push = final_fee_res + res_upfront + res_inner + res_tert
    st.markdown("---")
    st.metric("TOTAL BENEFIT (PUSH)", f"Rp {total_benefit_push:,.0f}")

# --- TAB 3: HASIL AKHIR ---
with tab3:
    st.subheader("⚔️ Keputusan Akhir")
    profit_push = total_benefit_push - total_biaya_push
    tgt_kpi_val = safe_parse(row_data[f"Tgt_{kpi_config[0]['name']}"])
    if tgt_kpi_val > 0:
        fcst_ratio = (safe_parse(row_data[f"Act_{kpi_config[0]['name']}"]) * run_rate) / tgt_kpi_val
        fcst_ratio = min(fcst_ratio, 1.1)
    else:
        fcst_ratio = 0
    benefit_organik = (res_upfront * fcst_ratio) + (res_inner * fcst_ratio) + (res_tert * fcst_ratio)
    insentif_organik = prep_rev * final_tarif * (score_kpi * fcst_ratio) if ga_trade >= 80 else 0
    profit_pull = benefit_organik + insentif_organik + total_buyback_denda
    
    c1, c2 = st.columns([1, 1], gap="medium")
    with c1:
        st.markdown("### 🔥 PUSH")
        st.metric("Profit PUSH", f"Rp {profit_push:,.0f}", label_visibility="collapsed")
        st.caption(f"Benefit: {total_benefit_push:,.0f} | Biaya: {total_biaya_push:,.0f}")
    with c2:
        st.markdown("### 🛑 LEPAS")
        st.metric("Profit LEPAS", f"Rp {profit_pull:,.0f}", label_visibility="collapsed")
        st.caption(f"Benefit Org: {benefit_organik+insentif_organik:,.0f} | Denda: {total_buyback_denda:,.0f}")

    # LOGIKA REKOMENDASI TAMBAHAN (SIMULASI OPSI 2)
    st.divider()
    st.markdown("#### 🚀 Simulasi Perubahan Target (Opsi 2)")
    sim_score = st.slider("Simulasi Score KPI Opsi 2 (%)", 0.0, 110.0, 100.0, step=1.0) / 100
    multiplier_sim = min(sim_score, 1.05) # Capping 105%
    fee_sim = prep_rev * final_tarif * multiplier_sim * (ga_trade / 100)
    total_benefit_sim = fee_sim + res_upfront + res_inner + res_tert
    biaya_sim = total_biaya_push * (sim_score / 1.0) if total_biaya_push > 0 else 0
    net_profit_sim = total_benefit_sim - biaya_sim

    col_rec1, col_rec2 = st.columns(2)
    with col_rec1: st.info(f"**OPSI 1 (Input Saat Ini)**\n\nNet Profit: **Rp {profit_push:,.0f}**")
    with col_rec2: st.success(f"**OPSI 2 (Simulasi Slider)**\n\nNet Profit: **Rp {net_profit_sim:,.0f}**")

    st.markdown("---")
    if profit_push >= net_profit_sim and profit_push > profit_pull:
        st.success(f"✅ **REKOMENDASI UTAMA: JALANKAN OPSI 1**")
        st.write(f"Strategi PUSH saat ini menghasilkan profit tertinggi senilai **Rp {profit_push:,.0f}**. Biaya operasional masih sebanding dengan bonus.")
    elif net_profit_sim > profit_push and net_profit_sim > profit_pull:
        st.success(f"✅ **REKOMENDASI UTAMA: JALANKAN OPSI 2**")
        st.write(f"Mengejar target baru lebih menguntungkan. Profit bersih simulasi: **Rp {net_profit_sim:,.0f}**.")
    else:
        st.error(f"✅ **REKOMENDASI UTAMA: LEPAS / TAGIH DENDA**")
        st.write("Biaya intervensi terlalu mahal. Lebih baik menjaga profit organik.")

    # TIGA SARAN STRATEGIS UNTUK MANAJEMEN
    st.markdown("### 💡 Saran Strategis (Key Takeaways)")
    with st.container(border=True):
        st.markdown("""
        1. **Fokus pada Keuntungan Bersih (Net Profit)**: Jangan hanya mengejar bonus besar di Tab 2. Pastikan biaya yang kamu keluarkan di Tab 1 lebih kecil daripada bonus yang didapat. Jika biaya > bonus, lebih baik pilih strategi **LEPAS**.
        2. **Waspadai Batas Minimal SDP (70%)**: Jika salah satu variabel (seperti Trade Supply) di bawah 70%, insentif kamu berisiko tidak cair saat audit, meskipun kalkulator menunjukkan angka bonus yang besar.
        3. **Gunakan Simulasi Slider untuk Target Mendadak**: Jika Indosat mengubah target di tengah bulan, gunakan slider 'Opsi 2' untuk mengecek apakah mengejar target baru tersebut masih memberikan untung atau malah merugi.
        """)

    selisih = profit_push - profit_pull
    st.divider()
    if selisih > 0:
        st.success(f"STATUS AWAL: **PUSH TARGET** (Lebih untung Rp {selisih:,.0f} dari Organik)")
    else:
        st.error(f"STATUS AWAL: **LEPAS / TAGIH DENDA** (Lebih untung Rp {abs(selisih):,.0f} dari Push)")