"""
Tərs GPA Kalkulyatoru — Login + Qeydiyyat ilə
------------------------------------------------
İşə salmaq üçün: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth


# ============================================================
# 1. SƏHİFƏ TƏNZİMLƏMƏLƏRİ
# ============================================================

st.set_page_config(page_title="Tərs GPA Kalkulyatoru", page_icon="🎓", layout="centered")


# ============================================================
# 2. LOGİN SİSTEMİNİ QURAŞDIRMAQ
# ============================================================
# config.yaml faylını oxuyuruq. Bu fayl istifadəçilərin
# (şifrələnmiş parolla) siyahısını saxlayır.

with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    "config.yaml",              # path veririk ki, qeydiyyatdan sonra fayl özü yenilənsin
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)


# ============================================================
# 3. LOGİN / QEYDİYYAT SƏHİFƏSİ
# ============================================================
# İstifadəçi hələ daxil olmayıbsa, bu hissə göstərilir.

if not st.session_state.get("authentication_status"):

    st.title("🎓 Tərs GPA Kalkulyatoru")

    tab_login, tab_register = st.tabs(["Daxil ol", "Qeydiyyatdan keç"])

    with tab_login:
        authenticator.login(location="main")

        if st.session_state.get("authentication_status") is False:
            st.error("İstifadəçi adı və ya parol yanlışdır.")
        elif st.session_state.get("authentication_status") is None:
            st.info("Zəhmət olmasa daxil ol, ya da hesabın yoxdursa qeydiyyatdan keç.")

    with tab_register:
        try:
            email, username, name = authenticator.register_user(
                location="main",
                captcha=False,   # istəsən True elə, robot-yoxlama əlavə olunar
            )
            if email:
                st.success("Qeydiyyat uğurlu oldu! İndi 'Daxil ol' bölməsindən sistemə gir.")
        except Exception as e:
            st.error(f"Xəta: {e}")

    st.stop()  # aşağıdakı kalkulyator hissəsini göstərmə, daxil olmayıb


# ============================================================
# 4. BURADAN SONRASI YALNIZ DAXİL OLMUŞ İSTİFADƏÇİYƏ GÖRÜNÜR
# ============================================================

with st.sidebar:
    st.write(f"👋 Salam, **{st.session_state['name']}**")
    authenticator.logout(location="sidebar")


# ============================================================
# 5. BAL -> HƏRF ÇEVİRMƏ CƏDVƏLİ
# ============================================================

SCORE_TO_LETTER = [
    (91, "A", 4.0),
    (81, "B", 3.0),
    (71, "C", 2.0),
    (61, "D", 1.0),
    (51, "E", 0.5),
    (0,  "F", 0.0),
]


def score_to_letter(score: float) -> tuple[str, float]:
    for min_score, letter, gpa in SCORE_TO_LETTER:
        if score >= min_score:
            return letter, gpa
    return "F", 0.0


# ============================================================
# 6. HESABLAMA MƏNTİQİ
# ============================================================

def calculate_current_average(df: pd.DataFrame) -> float:
    known = df[df["Bal"].notna()]
    if known["Kredit"].sum() == 0:
        return 0.0
    return (known["Bal"] * known["Kredit"]).sum() / known["Kredit"].sum()


def reverse_engineer_score(df: pd.DataFrame, target_average: float, min_pass_score: float = 51.0):
    total_credits = df["Kredit"].sum()
    results = []
    unknown_rows = df[df["Bal"].isna()]

    for idx, target in unknown_rows.iterrows():
        fixed_points = 0.0
        for jdx, s in df.iterrows():
            if jdx == idx:
                continue
            if pd.notna(s["Bal"]):
                fixed_points += s["Bal"] * s["Kredit"]
            else:
                fixed_points += min_pass_score * s["Kredit"]

        required_score_raw = (target_average * total_credits - fixed_points) / target["Kredit"]
        feasible = required_score_raw <= 100
        required_score = max(0, round(required_score_raw))
        letter, gpa = score_to_letter(required_score)

        results.append({
            "name": target["Fənn"],
            "credit": target["Kredit"],
            "required_score": required_score,
            "required_letter": letter if feasible else "MÜMKÜN DEYİL",
            "gpa": gpa,
            "feasible": feasible,
        })

    return results


# ============================================================
# 7. ƏSAS TƏTBİQ (Kalkulyator)
# ============================================================

st.title("🎓 Tərs GPA Kalkulyatoru")
st.write("Fənlərini daxil et, hədəf ortalamanı seç — sistem sənə hansı fənndən neçə bal lazım olduğunu göstərsin.")

st.subheader("1. Fənlərini daxil et")
st.caption("Qiyməti bəlli olmayan fənlər üçün 'Bal' xanasını boş burax.")

default_data = pd.DataFrame({
    "Fənn": ["Fənn A", "Fənn B", "Fənn C"],
    "Kredit": [6, 4, 8],
    "Bal": [85, 70, None],
})

edited_df = st.data_editor(
    default_data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Bal": st.column_config.NumberColumn(min_value=0, max_value=100, help="0-100 arası, bilinmirsə boş burax"),
        "Kredit": st.column_config.NumberColumn(min_value=1, max_value=20),
    }
)

st.subheader("2. Hədəf ortalamanı seç")
target_average = st.slider("Hədəf ortalama (0-100)", min_value=0, max_value=100, value=75)

if st.button("Hesabla", type="primary"):

    current_avg = calculate_current_average(edited_df)
    st.metric("Cari ortalama (bəlli fənlərdən)", f"{current_avg:.1f}")

    recommendations = reverse_engineer_score(edited_df, target_average)

    if not recommendations:
        st.info("Bütün fənlərin qiyməti artıq bəllidir.")
    else:
        st.subheader("3. Nəticə")

        for r in recommendations:
            if r["feasible"]:
                st.success(
                    f"**{r['name']}** ({r['credit']} kredit): minimum **{r['required_score']} bal** "
                    f"({r['required_letter']}, GPA {r['gpa']}) lazımdır."
                )
            else:
                st.error(
                    f"**{r['name']}** ({r['credit']} kredit): hədəfə çatmaq **mümkün deyil**."
                )

        names = [r["name"] for r in recommendations]
        scores = [min(r["required_score"], 100) for r in recommendations]
        colors = []
        for r in recommendations:
            if not r["feasible"]:
                colors.append("#d62728")
            elif r["required_score"] >= 85:
                colors.append("#ff7f0e")
            else:
                colors.append("#2ca02c")

        fig = go.Figure(data=[
            go.Bar(x=names, y=scores, marker_color=colors, text=scores, textposition="outside")
        ])
        fig.update_layout(
            yaxis_range=[0, 100],
            yaxis_title="Tələb olunan bal",
            xaxis_title="Fənn",
            title="Naməlum fənlərdən tələb olunan minimum ballar",
        )
        st.plotly_chart(fig, use_container_width=True)