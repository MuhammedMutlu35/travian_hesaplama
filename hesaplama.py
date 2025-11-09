import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import math
from io import BytesIO

# -------------------- Calculs Travian --------------------
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

# -------------------- Streamlit App --------------------
st.set_page_config(page_title="Travian Hesaplayıcı", layout="wide")

st.title("Travian Zaman Hesaplayıcı")


# ---- Villages de départ ----
st.header("Başlangıç Köyleri")
num_starts = st.number_input("Kaç başlangıç köyünüz var?", min_value=1, step=1, value=1)
start_villages = []
for i in range(num_starts):
    st.subheader(f"Köy {i+1}")
    col1, col2, col3, col4 = st.columns(4)
    x = col1.number_input("X koordinatı", step=1, format="%d", key=f"start_x_{i}")
    y = col2.number_input("Y koordinatı", step=1, format="%d", key=f"start_y_{i}")
    speed = col3.number_input("En yavaş birim hızı", min_value=1, value=7, step=1, key=f"unit_{i}")
    tour = col4.slider("Turnuva Meydanı Seviyesi", 0, 20, 7, key=f"tour_{i}")
    start_villages.append({"x": x, "y": y, "speed": speed, "tour": tour})

# ---- Villages cibles ----
st.header("Hedef Köyler")
num_targets = st.number_input("Kaç hedef köy var?", min_value=1, step=1, value=1)
same_arrival = st.checkbox("Tüm hedefler için aynı varış saati?", value=True)

target_villages = []
arrival_times = []

for i in range(num_targets):
    st.subheader(f"Hedef {i+1}")
    col1, col2 = st.columns(2)
    x = col1.number_input("X koordinatı", step=1, format="%d", key=f"target_x_{i}")
    y = col2.number_input("Y koordinatı", step=1, format="%d", key=f"target_y_{i}")
    target_villages.append((x, y))

if same_arrival:
    arrival_str = st.text_input("Varış saati (HH:MM:SS)", value="12:00:00")
    try:
        arrival_time = datetime.strptime(arrival_str, "%H:%M:%S").time()
    except:
        st.error("Geçersiz saat formatı! HH:MM:SS olmalı.")
        arrival_time = datetime.now().time()
    arrival_times = [arrival_time]*num_targets
else:
    for i in range(num_targets):
        arrival_str = st.text_input(f"Hedef {i+1} varış saati (HH:MM:SS)", value="12:00:00", key=f"arrival_{i}")
        try:
            arrival_times.append(datetime.strptime(arrival_str, "%H:%M:%S").time())
        except:
            st.error(f"Hedef {i+1} için geçersiz saat formatı!")
            arrival_times.append(datetime.now().time())

# ---- Calcul et affichage ----
st.header("Hesaplama Sonuçları")
results = []

for s_idx, start in enumerate(start_villages):
    for t_idx, target in enumerate(target_villages):
        dist = toroidal_distance(start["x"], start["y"], target[0], target[1])
        travel = travel_time(dist, start["speed"], start["tour"])
        arrival_dt = datetime.combine(datetime.today(), arrival_times[t_idx])
        departure_dt = arrival_dt - travel
        results.append({
            "Başlangıç Köyü": f"{start['x']},{start['y']}",
            "Hedef Köy": f"{target[0]},{target[1]}",
            "Mesafe": dist,
            "Varış Saati": arrival_times[t_idx].strftime("%H:%M:%S"),
            "Kalkış Saati": departure_dt.strftime("%H:%M:%S"),
            "En Yavaş Birim Hızı": start["speed"],
            "Turnuva Bonus": start["tour"]*20
        })

df = pd.DataFrame(results)
st.dataframe(df)

# ---- Export Excel ----
excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    df.to_excel(writer, index=False, sheet_name="Travian")
st.download_button("Excel Olarak İndir", data=excel_buffer.getvalue(), file_name="travian.xlsx")