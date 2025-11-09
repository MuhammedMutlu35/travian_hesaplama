import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import math
from io import BytesIO
from PIL import Image
import base64

# -------------------- AYARLAR --------------------
st.set_page_config(page_title="Travian Zaman Hesaplayıcı", layout="wide")

# -------------------- BANNIERE --------------------
def display_banner_with_title(image_path, alliance_name="REBEL TM", max_height=120):
    try:
        with open(image_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode("utf-8")
        st.markdown(
            f"""
            <div style="
                display:flex; 
                align-items:center; 
                justify-content:center; 
                gap:20px; 
                margin-bottom:30px;">
                <img src="data:image/png;base64,{img_data}" 
                     style="max-height:{max_height}px; border-radius:10px; box-shadow:0 0 10px rgba(0,0,0,0.4);">
                <h1 style="
                    font-family: 'Trebuchet MS', sans-serif; 
                    font-weight: 900; 
                    font-size: 48px; 
                    color: #FFD700; 
                    text-shadow: 2px 2px 5px #000;">
                    {alliance_name}
                </h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        st.warning("⚠️ İttifak banner'ı bulunamadı (birlik_sancagi.JPG)")

display_banner_with_title("birlik_sancagi.JPG", "REBEL TM")

st.markdown(
    """
    <h1 style="text-align:center; color:#C19A6B;">
        🏰 <b>Travian Zaman Hesaplayıcı</b> ⚔️
    </h1>
    <p style="text-align:center; font-size:16px; color:gray;">
        <i>İttifak koordinasyonunu kolaylaştırmak için geliştirilmiştir ⚙️</i>
    </p>
    <hr style="border: 2px solid #C19A6B;">
    """,
    unsafe_allow_html=True,
)

# -------------------- TRAVIAN FONKSİYONLARI --------------------
def shortest_axis_distance(coord1: int, coord2: int) -> int:
    direct = abs(coord2 - coord1)
    via_border = (200 - abs(coord1)) + (200 - abs(coord2) + 1)
    return min(direct, via_border)

def toroidal_distance(x1: int, y1: int, x2: int, y2: int) -> float:
    dx = shortest_axis_distance(x1, x2)
    dy = shortest_axis_distance(y1, y2)
    return math.sqrt(dx**2 + dy**2)

def tournament_bonus(level: int) -> float:
    level = max(0, min(level, 20))
    return level * 0.20

def travel_time(distance: float, unit_speed: float, tournament_level: int) -> timedelta:
    bonus = tournament_bonus(tournament_level)
    base_distance = min(distance, 20)
    base_time = base_distance / unit_speed
    bonus_distance = max(distance - 20, 0)
    bonus_time = bonus_distance / (unit_speed * (1 + bonus))
    total_hours = base_time + bonus_time
    return timedelta(seconds=round(total_hours * 3600))

# -------------------- UNITE TRAVIAN --------------------
unit_speeds = {
    "Roma - Legionnaire / Lejyoner": 6,
    "Roma - Praetorian / Pretoryan": 5,
    "Roma - Imperian / İmperiyal": 7,
    "Roma - Equites Legati / Lejyon Süvarisi": 16,
    "Roma - Equites Imperatoris / İmparator Süvarisi": 14,
    "Roma - Equites Caesaris / Sezar Süvarisi": 10,
    "Roma - Battering Ram / Koçbaşı": 4,
    "Roma - Catapult / Mancınık": 3,
    "Roma - Senator / Senatör": 4,
    "Roma - Settler / Kolcu": 5,
    
    "Kelt - Phalanx / Phalanx": 7,
    "Kelt - Swordsman / Kılıççı": 6,
    "Kelt - Pathfinder / İzci": 17,
    "Kelt - Theutates Thunder / Thor Savaşçısı": 19,
    "Kelt - Druidrider / Druid Süvarisi": 16,
    "Kelt - Haeduan / Haeduan Süvarisi": 13,
    "Kelt - Ram / Koçbaşı": 4,
    "Kelt - Catapult / Mancınık": 3,
    "Kelt - Chieftain / Şef": 5,
    "Kelt - Settler / Kolcu": 5,

    "Teuton - Clubman / Sopacı": 7,
    "Teuton - Spearman / Mızrakçı": 7,
    "Teuton - Axeman / Baltacı": 6,
    "Teuton - Scout / Casus": 9,
    "Teuton - Paladin / Süvari Şövalye": 10,
    "Teuton - Teutonic Knight / Teuton Şövalyesi": 9,
    "Teuton - Ram / Koçbaşı": 4,
    "Teuton - Catapult / Mancınık": 3,
    "Teuton - Chief / Şef": 4,
    "Teuton - Settler / Kolcu": 5
}

# -------------------- VERI YUKLEME --------------------
@st.cache_data
def load_villages_from_file(path: str):
    try:
        df = pd.read_excel(path)
        df = df.rename(columns=lambda c: c.strip())
        if not all(col in df.columns for col in ["PlayerName", "VillageName", "X", "Y"]):
            raise ValueError("Excel dosyasında gerekli sütunlar yok. Gerekli: PlayerName, VillageName, X, Y")
        df = df.dropna(subset=["PlayerName", "VillageName", "X", "Y"])
        df["X"] = df["X"].astype(int)
        df["Y"] = df["Y"].astype(int)
        return df
    except Exception as e:
        st.error(f"🏕️ Köy dosyası okunamadı: {e}")
        return pd.DataFrame(columns=["PlayerName", "VillageName", "X", "Y"])

# -------------------- KÖY LİSTESİ --------------------
try:
    villages_df = load_villages_from_file("travian_alliance.xlsx")
except Exception:
    villages_df = pd.DataFrame(columns=["PlayerName", "VillageName", "X", "Y"])

has_villages = not villages_df.empty
villages_display = (
    villages_df["VillageName"].astype(str) + " (" + villages_df["PlayerName"].astype(str) + ")"
).tolist() if has_villages else []

# -------------------- BAŞLANGIÇ KÖYLERİ --------------------
st.header("🚩 Başlangıç Köyleri (Giriş)")
num_starts = st.number_input("Kaç başlangıç köyü?", min_value=1, step=1, value=1, key="num_starts")
start_villages = []

for i in range(num_starts):
    st.subheader(f"⚒️ Başlangıç #{i+1}")
    choose_from_list = st.checkbox("📜 Listeden seç", value=True if has_villages else False, key=f"start_use_list_{i}")
    if choose_from_list and has_villages:
        choice = st.selectbox("Köy seç", villages_display, key=f"start_select_{i}")
        sel_row = villages_df.loc[
            (villages_df["VillageName"].astype(str) + " (" + villages_df["PlayerName"].astype(str) + ")") == choice
        ].iloc[0]
        x, y = int(sel_row["X"]), int(sel_row["Y"])
        player, village_name = str(sel_row["PlayerName"]), str(sel_row["VillageName"])
    else:
        col1, col2 = st.columns(2)
        x = col1.number_input("🧭 X koordinatı", step=1, format="%d", key=f"start_x_{i}")
        y = col2.number_input("🧭 Y koordinatı", step=1, format="%d", key=f"start_y_{i}")
        player = st.text_input("👤 Oyuncu adı", key=f"start_player_{i}")
        village_name = st.text_input("🏠 Köy adı", key=f"start_village_{i}")

    # -------------------- UNIT SELECTION --------------------
    col3, col4 = st.columns(2)
    unit_choice = col3.selectbox(
        "🐎 En yavaş birim / Birim seç", 
        options=list(unit_speeds.keys()), 
        index=list(unit_speeds.keys()).index("Roma - Legionnaire / Lejyoner"),
        key=f"start_unit_{i}"
    )
    speed = unit_speeds[unit_choice]

    tour = col4.slider("🏅 Turnuva seviyesi", 0, 20, 7, key=f"start_tour_{i}")

    start_villages.append({
        "PlayerName": player or "",
        "VillageName": village_name or "",
        "x": int(x), "y": int(y),
        "speed": int(speed), "tour": int(tour)
    })

# -------------------- HEDEF KÖYLER --------------------
st.header("🎯 Hedef Köyler")
num_targets = st.number_input("Kaç hedef köy?", min_value=1, step=1, value=1, key="num_targets")
target_villages, arrival_times = [], []

for i in range(num_targets):
    st.subheader(f"⚔️ Hedef #{i+1}")
    choose_from_list = st.checkbox("📜 Listeden seç", value=True if has_villages else False, key=f"target_use_list_{i}")
    if choose_from_list and has_villages:
        choice = st.selectbox("Köy seç", villages_display, key=f"target_select_{i}")
        sel_row = villages_df.loc[
            (villages_df["VillageName"].astype(str) + " (" + villages_df["PlayerName"].astype(str) + ")") == choice
        ].iloc[0]
        x, y = int(sel_row["X"]), int(sel_row["Y"])
        player, village_name = str(sel_row["PlayerName"]), str(sel_row["VillageName"])
    else:
        col1, col2 = st.columns(2)
        x = col1.number_input("🧭 X koordinatı", step=1, format="%d", key=f"target_x_{i}")
        y = col2.number_input("🧭 Y koordinatı", step=1, format="%d", key=f"target_y_{i}")
        player = st.text_input("👤 Oyuncu adı", key=f"target_player_{i}")
        village_name = st.text_input("🏠 Köy adı", key=f"target_village_{i}")

    arrival_str = st.text_input("⏰ Varış saati (HH:MM:SS)", value="12:00:00", key=f"arrival_str_{i}")
    try:
        arrival_time = datetime.strptime(arrival_str, "%H:%M:%S").time()
    except:
        st.error("❌ Saat formatı hatalı, HH:MM:SS olmalı.")
        arrival_time = datetime.strptime("12:00:00", "%H:%M:%S").time()

    target_villages.append({"PlayerName": player or "", "VillageName": village_name or "", "x": int(x), "y": int(y)})
    arrival_times.append(arrival_time)

# -------------------- HESAPLAMA --------------------
st.header("📊 Hesaplama Sonuçları")
results = []

for s in start_villages:
    for t_idx, t in enumerate(target_villages):
        dist = toroidal_distance(s["x"], s["y"], t["x"], t["y"])
        travel = travel_time(dist, s["speed"], s["tour"])
        arrival_dt = datetime.combine(datetime.today(), arrival_times[t_idx])
        departure_dt = arrival_dt - travel
        results.append({
            "Başlangıç Oyuncu": s["PlayerName"],
            "Başlangıç Köy": s["VillageName"],
            "X Başlangıç": s["x"], "Y Başlangıç": s["y"],
            "Hedef Oyuncu": t["PlayerName"],
            "Hedef Köy": t["VillageName"],
            "X Hedef": t["x"], "Y Hedef": t["y"],
            "Mesafe": round(dist, 2),
            "Varış": arrival_times[t_idx].strftime("%H:%M:%S"),
            "Çıkış": departure_dt.strftime("%H:%M:%S"),
            "Süre": str(travel),
            "En Yavaş Hız": s["speed"], "Turnuva Seviyesi": s["tour"]
        })

df_results = pd.DataFrame(results)
st.dataframe(df_results, width='stretch')

# -------------------- EXCEL ÇIKTISI --------------------
excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
    df_results.to_excel(writer, index=False, sheet_name="Travian")
st.download_button("📥 Excel olarak indir (.xlsx)", data=excel_buffer.getvalue(), file_name="travian_calculs.xlsx")
