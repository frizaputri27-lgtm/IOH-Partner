import streamlit as st
import pandas as pd
import numpy as np
import io
import requests
import datetime

# ==========================================
# 0. KONFIGURASI LINK EXCEL
# ==========================================
URL_MASTER_EXCEL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQeyU9rZr1_chZ4uCARDn_t8zeoRPZM5EyXv6wBWkySRkpsvguSOUAb-Xzd4mKOVA/pub?output=xlsx"

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS
# ==========================================
st.set_page_config(page_title="IOH Super System", layout="wide")

st.markdown("""
    <style>
    /* CSS DASHBOARD */
    .kpi-card { background-color: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .card-title { font-size: 12px; font-weight: bold; color: #64748b; text-transform: uppercase; margin-bottom: 5px; }
    .card-value { font-size: 24px; font-weight: 800; color: #1e293b; }
    .card-sub { font-size: 11px; color: #94a3b8; }
    .highlight-yellow { border-left: 5px solid #fbbf24; }
    .highlight-purple { border-left: 5px solid #a855f7; }
    
    /* CSS SALDO & SALES BOX */
    .saldo-box { background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 15px; border-radius: 8px; text-align: center; }
    .saldo-title { color: #166534; font-weight: 700; font-size: 14px; margin-bottom: 5px; }
    .saldo-value { color: #15803d; font-weight: 800; font-size: 22px; }
    
    .sales-box-nat { background-color: #eff6ff; border: 1px solid #bfdbfe; padding: 10px; border-radius: 8px; text-align: center; }
    .sales-val-nat { color: #1d4ed8; font-weight: 800; font-size: 18px; }
    .sales-box-boost { background-color: #fef2f2; border: 1px solid #fecaca; padding: 10px; border-radius: 8px; text-align: center; }
    .sales-val-boost { color: #b91c1c; font-weight: 800; font-size: 18px; }

    /* CSS KALKULATOR (JANGAN UBAH) */
    .stNumberInput small, .stTextInput small { display: none; }
    .sidebar-metric-value-red { color: #dc2626; font-weight: 700; }
    .sidebar-metric-value-green { color: #16a34a; font-weight: 700; }
    .kpi-header-cost { background: linear-gradient(135deg, #1f77b4 0%, #2b8cc4 100%); color: #ffffff; font-size: 20px; font-weight: 700; padding: 12px 16px; border-radius: 6px; margin-bottom: 10px; }
    .gap-amount-display { background: linear-gradient(135deg, #f5f7fa 0%, #eef2f7 100%); border: 2px solid #cbd5e1; border-radius: 8px; padding: 10px; text-align: center; min-height: 60px; display: flex; align-items: center; justify-content: center; }
    .gap-value-red { color: #dc2626; font-size: 18px; font-weight: 700; }
    .gap-value-green { color: #16a34a; font-size: 18px; font-weight: 700; }
    .total-cost-container { background-color: #fef2f2; border-left: 5px solid #dc2626; border-radius: 6px; padding: 16px; margin-top: 16px; display: flex; justify-content: space-between; align-items: center; }
    .total-cost-text { color: #991b1b; font-size: 16px; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

st.title("🏢 IOH Partner Super System")

# ==========================================
# 2. ENGINE PEMBACA DATA
# ==========================================
def safe_parse(val):
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        clean_val = val.replace(",", "").replace("%", "").strip()
        try:
            num = float(clean_val)
            return num / 100 if "%" in val else num
        except: return 0.0
    return 0.0

if "kpi_interventions" not in st.session_state:
    st.session_state.kpi_interventions = {}

@st.cache_data(ttl=60) 
def load_all_sheets(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        all_dfs = pd.read_excel(io.BytesIO(r.content), sheet_name=None, header=None, engine='openpyxl')
        return all_dfs
    except Exception as e:
        st.error(f"Gagal memuat Excel: {e}")
        return None

def get_sheet_fuzzy(dfs, key):
    for k in dfs.keys():
        if key.upper() in k.upper():
            return dfs[k]
    return None

def get_kpi_values(df, region, keyword):
    tgt, act = 0, 0
    col_idx = -1
    for r in range(min(30, len(df))):
        for c in range(len(df.columns)):
            val = str(df.iloc[r,c]).upper()
            if region in val:
                col_idx = c
                break
        if col_idx != -1: break
    if col_idx == -1: return 0, 0

    target_section = False
    for idx, row in df.iterrows():
        lbl = str(row.iloc[0]).upper()
        if "TARGET" in lbl and "DES" in lbl: target_section = True
        
        if keyword in lbl:
            try:
                raw_val = row.iloc[col_idx]
                val = float(str(raw_val).replace(",","").replace("%",""))
            except: val = 0
            if target_section: tgt = val
            else: act = val
    return tgt, act

def get_stock_values(df, region):
    ga, fwa = 0, 0
    key = region.replace("3KIOSK ", "").replace("SDP ", "").strip()
    for idx, row in df.iterrows():
        if key in str(row.iloc[1]).upper():
            try:
                ga = float(row.iloc[2])
                fwa = float(row.iloc[3])
            except: pass
            break
    return ga, fwa

# --- FUNGSI SALDO INDOSAT ---
def get_daily_saldo_data_indosat(df, region, target_month_idx):
    daily_data = {} 
    header_idx = -1
    col_sdp, col_detail, col_paid, col_time, col_tgl = -1, -1, -1, -1, -1
    
    for r in range(5):
        row_vals = [str(x).upper() for x in df.iloc[r].tolist()]
        if "DETAILS" in row_vals and ("PAID IN" in row_vals or "PAID" in row_vals):
            header_idx = r
            for i, v in enumerate(row_vals):
                if "SDP" in v: col_sdp = i
                if "DETAILS" in v: col_detail = i
                if "PAID" in v and "IN" in v: col_paid = i
                if "COMPLETION" in v and "TIME" in v: col_time = i
                if "TGL" in v: col_tgl = i 
            break
            
    if header_idx == -1: return pd.DataFrame(), 0

    keyword_trx = "ESCM Allocation from SAP| |API".upper()
    region_key = region.upper()
    total_filtered = 0
    
    for idx in range(header_idx + 1, len(df)):
        try:
            row = df.iloc[idx]
            val_sdp = str(row[col_sdp]).upper() if col_sdp != -1 else ""
            if region_key not in val_sdp: continue
            
            val_detail = str(row[col_detail]).upper()
            if keyword_trx not in val_detail: continue
            
            day_key = 0
            if col_tgl != -1:
                try: day_key = int(float(str(row[col_tgl]).strip()))
                except: pass
            
            if day_key == 0 and col_time != -1:
                val_time = row[col_time]
                try: 
                    dt_obj = pd.to_datetime(val_time, dayfirst=True) if isinstance(val_time, str) else val_time
                    if dt_obj.month == target_month_idx: day_key = dt_obj.day
                except: pass
            
            if day_key > 0:
                val_duit = row[col_paid]
                if pd.notna(val_duit):
                    nominal = float(str(val_duit).replace(",",""))
                    daily_data[day_key] = daily_data.get(day_key, 0) + nominal
                    total_filtered += nominal
        except: continue
        
    chart_df = pd.DataFrame(list(daily_data.items()), columns=['Tanggal', 'Pembelian']).sort_values('Tanggal').set_index('Tanggal') if daily_data else pd.DataFrame()
    return chart_df, total_filtered

# --- FUNGSI SALDO TRI (PRIM) ---
def get_daily_saldo_data_tri(df, region, target_month_idx):
    daily_data = {}
    total_filtered = 0
    region_map = {"KEDUNGPRING": "KDUNGPRING"}
    search_key = region_map.get(region, region).upper()
    
    header_idx = -1
    col_order, col_amt, col_date = -1, -1, -1
    
    for r in range(5):
        row_vals = [str(x).upper() for x in df.iloc[r].tolist()]
        if "AMOUNT" in row_vals and ("ORDER DATE" in row_vals or "TRANSFER DATE" in row_vals):
            header_idx = r
            for i, v in enumerate(row_vals):
                if "AMOUNT" in v: col_amt = i
                if "ORDER DATE" in v: col_date = i
                if "ORDER FOR" in v: col_order = i
            if col_order == -1:
                for i, v in enumerate(row_vals):
                    if "TRANSFER NUMBER" in v: col_order = i
            break
            
    if header_idx == -1: return pd.DataFrame(), 0
    
    for idx in range(header_idx + 1, len(df)):
        try:
            row = df.iloc[idx]
            val_order = str(row[col_order]).upper() if col_order != -1 else ""
            
            if search_key in val_order:
                val_date = row[col_date]
                dt_obj = None
                
                if isinstance(val_date, str):
                    try: dt_obj = pd.to_datetime(val_date, dayfirst=True)
                    except: pass
                elif isinstance(val_date, (datetime.datetime, pd.Timestamp)):
                    dt_obj = val_date
                    
                if dt_obj and dt_obj.month == target_month_idx:
                    val_amt = row[col_amt]
                    if pd.notna(val_amt):
                        nominal = float(str(val_amt).replace(",",""))
                        day_key = dt_obj.day
                        daily_data[day_key] = daily_data.get(day_key, 0) + nominal
                        total_filtered += nominal
        except: continue
        
    chart_df = pd.DataFrame(list(daily_data.items()), columns=['Tanggal', 'Pembelian']).sort_values('Tanggal').set_index('Tanggal') if daily_data else pd.DataFrame()
    return chart_df, total_filtered

# --- FUNGSI SALES TRI (DENGAN BREAKDOWN SUB-WILAYAH) ---
def get_tri_sales_analysis(df, region):
    """
    Analisis Penjualan Tri dari Sheet SEC DSE.
    Filter: 'Transfer Sub type' = 'Transfer' AND 'BANTU DSE' contains Region.
    Breakdown: Group by 'BANTU DSE' (e.g. SIDAYU 1, SIDAYU 2)
    """
    total_natural = 0
    total_boosting = 0
    
    # Dictionary untuk menyimpan breakdown per sub-wilayah
    # Format: {'SIDAYU 1': {'Nat': 0, 'Boost': 0}, 'SIDAYU 2': ...}
    breakdown_data = {}
    
    region_map = {"KEDUNGPRING": "KDUNGPRING"}
    search_key = region_map.get(region, region).upper()
    
    # Cari Header
    header_idx = -1
    col_type, col_bantu, col_cek, col_amt = -1, -1, -1, -1
    
    for r in range(5):
        row_vals = [str(x).upper() for x in df.iloc[r].tolist()]
        if "TRANSFER SUB TYPE" in row_vals and "AMOUNT(IDR)" in row_vals:
            header_idx = r
            for i, v in enumerate(row_vals):
                if "TRANSFER SUB TYPE" in v: col_type = i
                if "BANTU DSE" in v: col_bantu = i
                if "CEK" in v: col_cek = i
                if "AMOUNT(IDR)" in v: col_amt = i
            break
    
    if header_idx == -1 or col_bantu == -1 or col_cek == -1:
        return 0, 0, pd.DataFrame()
        
    # Loop Data
    for idx in range(header_idx + 1, len(df)):
        try:
            row = df.iloc[idx]
            
            # 1. Filter Sub Type == Transfer
            sub_type = str(row[col_type]).upper() if col_type != -1 else ""
            if "TRANSFER" not in sub_type: continue
            
            # 2. Filter Wilayah (BANTU DSE)
            bantu_dse = str(row[col_bantu]).upper().strip()
            if search_key not in bantu_dse: continue
            
            # 3. Ambil Amount
            val_amt = row[col_amt]
            nominal = 0
            if pd.notna(val_amt):
                nominal = float(str(val_amt).replace(",",""))
                
            # 4. Logic Kategori
            cek_val = str(row[col_cek]).upper()
            is_boost = "BMS" in cek_val
            
            if is_boost: total_boosting += nominal
            else: total_natural += nominal
            
            # 5. Masukkan ke Breakdown Data
            if bantu_dse not in breakdown_data:
                breakdown_data[bantu_dse] = {'Natural': 0, 'Boosting': 0, 'Total': 0}
            
            breakdown_data[bantu_dse]['Total'] += nominal
            if is_boost:
                breakdown_data[bantu_dse]['Boosting'] += nominal
            else:
                breakdown_data[bantu_dse]['Natural'] += nominal
                
        except: continue
        
    # Buat DataFrame dari breakdown
    if breakdown_data:
        df_breakdown = pd.DataFrame.from_dict(breakdown_data, orient='index')
        df_breakdown.index.name = 'Sub Wilayah'
        df_breakdown = df_breakdown.sort_index()
    else:
        df_breakdown = pd.DataFrame()
        
    return total_natural, total_boosting, df_breakdown

# ==========================================
# 3. SIDEBAR & DATA LOADING
# ==========================================
with st.sidebar:
    st.header("🔄 Sinkronisasi")
    if st.button("Refresh Data Excel"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.header("📍 Filter Data")

dfs = load_all_sheets(URL_MASTER_EXCEL)

with st.sidebar:
    if dfs is None: st.stop()
    
    mitra = st.selectbox("Tipe Mitra", ["SDP (Indosat)", "3KIOSK (Tri)"])
    if "Indosat" in mitra:
        sheet_kpi = "EST LR IM3"
        areas = ["KEDAMEAN", "DAWARBLANDONG", "SANGKAPURA"]
        theme = "highlight-yellow"
    else:
        sheet_kpi = "EST LR 3"
        areas = ["SIDAYU", "BENJENG", "JATIREJO", "KEMLAGI", "BABAT", "KEDUNGPRING"]
        theme = "highlight-purple"
        
    wilayah = st.selectbox("Wilayah", areas)
    
    bulan_map = {"Januari": 1, "Februari": 2, "Maret": 3, "April": 4, "Mei": 5, "Juni": 6, 
                 "Juli": 7, "Agustus": 8, "September": 9, "Oktober": 10, "November": 11, "Desember": 12}
    pilih_bulan = st.selectbox("Pilih Bulan (Grafik)", list(bulan_map.keys()))
    bulan_idx = bulan_map[pilih_bulan]
    
    st.divider()
    menu = st.radio("Menu", ["📊 Dashboard Utama", "🧮 Kalkulator Strategi"])
    
    st.divider()
    days = st.number_input("Jml Hari", value=31)
    curr = st.number_input("Hari Ke-", value=18)
    run_rate = days/curr if curr>0 else 0
    
    st.header("⚙️ Konfigurasi KPI")
    kpi_config = []
    def_kpis = [("Trade Supply", 40), ("M2S Absolute", 40), ("RGU FWA", 20)]
    for i, (d_name, d_w) in enumerate(def_kpis):
        c1, c2 = st.columns([3, 1], gap="small")
        with c1: kn = st.text_input(f"KPI {i+1}", value=d_name, key=f"kn{i}", label_visibility="collapsed")
        with c2: kw = st.number_input("W", value=d_w, key=f"kw{i}", label_visibility="collapsed")
        kpi_config.append({"name": kn, "weight": kw/100})
        
        if kn in st.session_state.kpi_interventions:
            inv = st.session_state.kpi_interventions[kn]
            gc = "sidebar-metric-value-red" if inv['gap'] > 0 else "sidebar-metric-value-green"
            with st.container(border=True):
                r1a, r1b = st.columns(2)
                r1a.markdown(f"<span style='font-size:10px'>Tgt</span><br><b>{inv['target']:,.0f}</b>", unsafe_allow_html=True)
                r1b.markdown(f"<span style='font-size:10px'>Act</span><br><b>{inv['actual']:,.0f}</b>", unsafe_allow_html=True)
                st.markdown(f"Gap: <span class='{gc}'>{inv['gap']:,.0f}</span>", unsafe_allow_html=True)

# PREPARE DATA
df_kpi_sheet = get_sheet_fuzzy(dfs, sheet_kpi.replace(" ", "")) 
if df_kpi_sheet is None: df_kpi_sheet = get_sheet_fuzzy(dfs, sheet_kpi)

t_tr, a_tr, t_m2, a_m2, t_fw, a_fw = 0,0,0,0,0,0
rgu_compliance = 0

if df_kpi_sheet is not None:
    t_tr, a_tr = get_kpi_values(df_kpi_sheet, wilayah, "TRADE SUPPLY")
    t_m2, a_m2 = get_kpi_values(df_kpi_sheet, wilayah, "M2S")
    t_fw, a_fw = get_kpi_values(df_kpi_sheet, wilayah, "RGU GA")
    rgu_compliance = (a_fw/t_fw*100) if t_fw > 0 else 0

# --- PROSES DATA SALDO ---
saldo_chart_df = pd.DataFrame()
saldo_total_bulan_ini = 0
source_info = ""

if "Indosat" in mitra:
    df_sal = get_sheet_fuzzy(dfs, "SAL")
    if df_sal is not None:
        saldo_chart_df, saldo_total_bulan_ini = get_daily_saldo_data_indosat(df_sal, wilayah, bulan_idx)
        source_info = "Sumber: Sheet SAL (Filter: 'ESCM Allocation')"
else: # TRI (3KIOSK)
    df_prim = get_sheet_fuzzy(dfs, "PRIM")
    if df_prim is not None:
        saldo_chart_df, saldo_total_bulan_ini = get_daily_saldo_data_tri(df_prim, wilayah, bulan_idx)
        source_info = "Sumber: Sheet PRIM (Kolom: Amount)"

# --- PROSES SALES TRI (NATURAL VS BOOSTING & BREAKDOWN) ---
tri_sales_nat = 0
tri_sales_boost = 0
df_sales_breakdown = pd.DataFrame()

if "Tri" in mitra:
    df_sec = get_sheet_fuzzy(dfs, "SEC DSE")
    if df_sec is not None:
        tri_sales_nat, tri_sales_boost, df_sales_breakdown = get_tri_sales_analysis(df_sec, wilayah)

# ==========================================
# 4. MENU 1: DASHBOARD UTAMA
# ==========================================
if menu == "📊 Dashboard Utama":
    st.subheader(f"Dashboard Monitoring: {wilayah}")
    st.caption("Monitoring Pembelian Saldo / Primary")
    st.markdown("---")
    
    # --- BAGIAN 1: SALDO ---
    c1, c2 = st.columns([1, 2]) 
    
    with c1:
        st.markdown(f"""
        <div class="saldo-box">
            <div class="saldo-title">💰 TOTAL PEMBELIAN SALDO</div>
            <div style="font-size:12px; margin-bottom:5px;">(Bulan {pilih_bulan})</div>
            <div class="saldo-value">Rp {saldo_total_bulan_ini:,.0f}</div>
            <div style="margin-top:10px; font-size:11px; color:#6b7280;">{source_info}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"##### 📈 Tren Pembelian Harian ({pilih_bulan})")
        if not saldo_chart_df.empty:
            st.bar_chart(saldo_chart_df, color="#16a34a", height=250)
        else:
            st.warning(f"Tidak ada data pembelian saldo untuk bulan {pilih_bulan}.")

    # --- BAGIAN 2: SALES TRI (KHUSUS TRI) ---
    if "Tri" in mitra:
        st.markdown("---")
        st.subheader("🛍️ Analisis Penjualan (Secondary)")
        st.caption("Sumber: Sheet SEC DSE (Filter: Transfer)")
        
        c_s1, c_s2, c_s3 = st.columns([1, 1, 2])
        
        with c_s1:
            st.markdown(f"""
            <div class="sales-box-nat">
                <div style="font-size:12px; color:#1e40af; font-weight:700;">NATURAL (NON-BMS)</div>
                <div class="sales-val-nat">Rp {tri_sales_nat:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c_s2:
            st.markdown(f"""
            <div class="sales-box-boost">
                <div style="font-size:12px; color:#991b1b; font-weight:700;">BOOSTING (BMS)</div>
                <div class="sales-val-boost">Rp {tri_sales_boost:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c_s3:
            data_sales = pd.DataFrame({
                "Tipe": ["Natural", "Boosting"],
                "Amount": [tri_sales_nat, tri_sales_boost]
            })
            st.bar_chart(data_sales.set_index("Tipe"), color=["#3b82f6"], height=200)
            
        # --- TABEL BREAKDOWN PER BANTU DSE ---
        st.markdown("##### 📋 Rincian per Sub-Wilayah (BANTU DSE)")
        if not df_sales_breakdown.empty:
            # Format Angka jadi Rupiah
            st.dataframe(
                df_sales_breakdown.style.format("{:,.0f}"),
                use_container_width=True
            )
        else:
            st.info("Belum ada data penjualan Secondary untuk wilayah ini.")

# ==========================================
# 5. MENU 2: KALKULATOR STRATEGI (TETAP SAMA)
# ==========================================
elif menu == "🧮 Kalkulator Strategi":
    st.subheader(f"🧮 Kalkulator Strategi: {wilayah}")
    
    # --- A. INPUT MANUAL (AUTO-FILL) ---
    st.caption("Data terisi otomatis dari Excel (bisa diedit untuk simulasi).")
    input_struct = {"Wilayah": [wilayah]}
    val_map = {"Trade Supply": (t_tr, a_tr), "M2S Absolute": (t_m2, a_m2), "RGU FWA": (t_fw, a_fw)}
    
    for kpi in kpi_config:
        vt, va = val_map.get(kpi['name'], (0,0))
        input_struct[f"Tgt_{kpi['name']}"] = [str(vt)]
        input_struct[f"Act_{kpi['name']}"] = [str(va)]
    input_struct["Compliance_RGU_Pct"] = [rgu_compliance]
    
    df_sim = pd.DataFrame(input_struct)
    edited_df = st.data_editor(df_sim, use_container_width=True, hide_index=True)
    row_data = edited_df.iloc[0]

    st.divider()
    tab1, tab2, tab3 = st.tabs(["💰 Analisis Biaya (Cost)", "🧮 KALKULATOR BENEFIT", "⚖️ Hasil Akhir"])

    # TAB 1: BIAYA
    total_biaya_push = 0
    gap_omzet_global = 0 
    
    with tab1:
        st.caption("Rincian Biaya Intervensi per KPI.")
        for i, kpi in enumerate(kpi_config):
            name = kpi['name']
            val_t = safe_parse(row_data[f"Tgt_{name}"])
            val_a = safe_parse(row_data[f"Act_{name}"])
            val_gap = max(0.0, val_t - (val_a * run_rate))
            if i == 0: gap_omzet_global = val_gap 
            
            st.markdown(f'<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-header-cost">📊 {name}</div>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="small")
            with col1:
                st.markdown('<span class="card-sub">Gap (Forecast)</span>', unsafe_allow_html=True)
                color_class = "gap-value-red" if val_gap > 0 else "gap-value-green"
                st.markdown(f'<div class="gap-amount-display"><span class="{color_class}">Rp {val_gap:,.0f}</span></div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<span class="card-sub">Catatan</span>', unsafe_allow_html=True)
                st.text_area("", value="-", height=60, label_visibility="collapsed", key=f"nt{i}")
            with col3:
                st.markdown('<span class="card-sub">Satuan Biaya</span>', unsafe_allow_html=True)
                idx = 0 if i==0 else 1
                satuan = st.selectbox("", ["Rupiah (%)", "Picis (Rp)"], index=idx, key=f"st{i}", label_visibility="collapsed")
                if satuan == "Rupiah (%)":
                    st.markdown('<span class="card-sub" style="margin-top:5px">%</span>', unsafe_allow_html=True)
                    pct = st.number_input(f"", value=1.0, step=0.1, key=f"cp{i}", label_visibility="collapsed")
                    biaya_val = val_gap * (pct/100)
                else:
                    st.markdown('<span class="card-sub" style="margin-top:5px">Rp/Unit</span>', unsafe_allow_html=True)
                    prc = st.number_input(f"", value=5000, step=500, key=f"cr{i}", label_visibility="collapsed")
                    biaya_val = val_gap * prc
            with col4:
                st.markdown('<span class="card-sub">Estimasi Biaya</span>', unsafe_allow_html=True)
                st.info(f"Rp {biaya_val:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.session_state.kpi_interventions[name] = {"target": val_t, "actual": val_a, "gap": val_gap, "biaya": biaya_val}
            total_biaya_push += biaya_val
            
        st.markdown(f"""<div class="total-cost-container"><span class="total-cost-text">💰 TOTAL BIAYA PUSH:</span><span class="total-cost-text">Rp {total_biaya_push:,.0f}</span></div>""", unsafe_allow_html=True)

    # TAB 2: BENEFIT
    total_benefit_push = 0
    total_buyback_denda = 0
    
    with tab2:
        st.info("Kalkulator Rincian Benefit & Buyback.")
        def_base = safe_parse(row_data[f"Tgt_{kpi_config[0]['name']}"])
        
        st.markdown("### 1. Insentif (Final Fee KPI)")
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1: prep_rev = st.number_input("Prepaid Rev (Rp)", value=float(def_base), step=1000000.0)
            with c2: final_tarif = st.number_input("Final Tarif (%)", value=2.5, step=0.1) / 100
            with c3: score_kpi = st.number_input("Score KPI (%)", value=110.0, step=1.0) / 100
            with c4: ga_trade = st.number_input("GA Trade", value=float(safe_parse(row_data["Compliance_RGU_Pct"])))
            final_fee_res = prep_rev * final_tarif * score_kpi
            st.success(f"Hasil Final Fee KPI: **Rp {final_fee_res:,.0f}**")

        st.markdown("### 2. Trading Benefit")
        with st.container(border=True):
            c_u1, c_u2, c_u3 = st.columns([2, 1, 2])
            with c_u1: base_upfront = st.number_input("Basis Upfront", value=float(def_base))
            with c_u2: rate_upfront = st.number_input("Upfront (%)", value=1.5, step=0.1) / 100
            with c_u3: res_upfront = base_upfront * rate_upfront; c_u3.info(f"Hasil: **Rp {res_upfront:,.0f}**")
            st.divider()
            c_in1, c_in2, c_in3 = st.columns([2, 1, 2])
            b_in = c_in1.number_input("Basis Inner Trx", value=200000000.0)
            r_in = c_in2.number_input("Inner (%)", value=2.5, step=0.1) / 100
            res_inner = b_in * r_in; c_in3.info(f"Hasil: **Rp {res_inner:,.0f}**")
            st.divider()
            c_tb1, c_tb2, c_tb3 = st.columns([2, 1, 2])
            b_te = c_tb1.number_input("Basis Tert B#", value=50000000.0)
            r_te = c_tb2.number_input("Tert B# (%)", value=0.5, step=0.1) / 100
            res_tert = b_te * r_te; c_tb3.info(f"Hasil: **Rp {res_tert:,.0f}**")

        st.markdown("### 3. Buyback Saldo DSE")
        with st.container(border=True):
            c_bb1, c_bb2, c_bb3 = st.columns([2, 1, 2])
            with c_bb1: saldo_gap = st.number_input("Saldo DSE / Gap", value=float(gap_omzet_global))
            with c_bb2: rate_buyback = st.number_input("Rate Buyback (%)", value=2.5, step=0.1) / 100
            with c_bb3: total_buyback_denda = saldo_gap * rate_buyback; c_bb3.error(f"Hasil: **Rp {total_buyback_denda:,.0f}**")

        total_benefit_push = final_fee_res + res_upfront + res_inner + res_tert
        st.markdown("---")
        st.metric("TOTAL BENEFIT (PUSH)", f"Rp {total_benefit_push:,.0f}")

    # TAB 3: HASIL AKHIR
    with tab3:
        st.subheader("⚔️ Keputusan Akhir")
        profit_push = total_benefit_push - total_biaya_push
        
        tgt_kpi_val = safe_parse(row_data[f"Tgt_{kpi_config[0]['name']}"])
        act_kpi_val = safe_parse(row_data[f"Act_{kpi_config[0]['name']}"])
        if tgt_kpi_val > 0:
            fcst_ratio = min((act_kpi_val * run_rate) / tgt_kpi_val, 1.1)
        else: fcst_ratio = 0
        
        benefit_organik = (res_upfront * fcst_ratio) + (res_inner * fcst_ratio) + (res_tert * fcst_ratio)
        insentif_organik = (prep_rev * final_tarif * (score_kpi * fcst_ratio)) if ga_trade >= 80 else 0
        profit_pull = benefit_organik + insentif_organik + total_buyback_denda
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("### 🔥 Skenario PUSH")
            st.metric("Profit PUSH", f"Rp {profit_push:,.0f}", label_visibility="collapsed")
            st.caption(f"Benefit: {total_benefit_push:,.0f} | Biaya: {total_biaya_push:,.0f}")
        with c2:
            st.markdown("### 🛑 Skenario LEPAS")
            st.metric("Profit LEPAS", f"Rp {profit_pull:,.0f}", label_visibility="collapsed")
            st.caption(f"Benefit Org: {benefit_organik+insentif_organik:,.0f} | Denda: {total_buyback_denda:,.0f}")
            
        st.divider()
        st.markdown("#### 🚀 Simulasi Perubahan Target (Opsi 2)")
        sim_score = st.slider("Simulasi Score (%)", 0.0, 110.0, 100.0) / 100
        multiplier = min(sim_score, 1.05)
        net_sim = (prep_rev * final_tarif * multiplier) + res_upfront + res_inner + res_tert - total_biaya_push
        
        c_op1, c_op2 = st.columns(2)
        c_op1.info(f"OPSI 1 (Current): **Rp {profit_push:,.0f}**")
        c_op2.success(f"OPSI 2 (Simulasi): **Rp {net_sim:,.0f}**")
        
        st.markdown("---")
        if profit_push > profit_pull:
            st.success(f"REKOMENDASI: **PUSH TARGET** (Lebih untung Rp {profit_push - profit_pull:,.0f})")
        else:
            st.error(f"REKOMENDASI: **LEPAS / TAGIH DENDA** (Lebih untung Rp {profit_pull - profit_push:,.0f})")
