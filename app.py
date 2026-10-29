import os
import streamlit as st
from PIL import Image
import google.generativeai as genai
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Hasta Beslenme Takibi", page_icon="🍲", layout="centered")

st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 12px; height: 3em; background-color: #2e7d32; color: white; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

st.title("🍲 Hasta Beslenme Takip")
st.write("Lütfen verilen öğünü yazın veya tabağın fotoğrafını yükleyin.")

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

if not api_key:
    st.error("API anahtarı bulunamadı! Lütfen ayarlardan GEMINI_API_KEY ekleyin.")
    st.stop()

# API Yapılandırması
genai.configure(api_key=api_key)

SYSTEM_PROMPT = """
Sen yaşlı ve yatan hasta bakım süreçlerinde hasta bakıcılar için tasarlanmış bir "Beslenme ve Kalori Takip Asistanı"sın.
Kullanıcı bir metin veya tabak fotoğrafı paylaştığında:
1. Besinleri ve porsiyonları analiz et.
2. Kalori, protein ve tahmini sıvı miktarını hesapla.
3. Yanıtı her zaman şu net formatta ver:

### 📋 Öğün Analizi
- [Besin adı] (~[Miktar]) -> ~[X] kcal | [Y]g Protein

### 📊 Toplam Değerler
- **Toplam Kalori:** ~[...] kcal
- **Protein:** ~[...] g
- **Tahmini Sıvı:** ~[...] ml

### 💡 Bakıcı Notu
[1-2 cümlelik pratik geribildirim; sıvı veya protein uyarısı vb.]
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

metin_girisi = st.text_area("Öğün Açıklaması (Örn: 1 kase mercimek çorbası, yarım dilim ekmek):", height=100)
fotograf = st.file_uploader("Veya Tabak Fotoğrafı Çek / Yükle:", type=["jpg", "jpeg", "png"])

if fotograf:
    img = Image.open(fotograf)
    st.image(img, caption="Yüklenen Görsel", use_container_width=True)

if st.button("Kaydet ve Hesapla"):
    if not metin_girisi and not fotograf:
        st.warning("Lütfen bir açıklama yazın veya fotoğraf yükleyin.")
    else:
        with st.spinner("Öğün ve kalori hesaplanıyor..."):
            try:
                icerik = []
                if fotograf:
                    icerik.append(img)
                if metin_girisi:
                    icerik.append(metin_girisi)

                response = model.generate_content(icerik)

                st.success("Hesaplama Tamamlandı!")
                st.markdown(response.text)

                yeni_kayit = {
                    "Tarih / Saat": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "Girdi": metin_girisi if metin_girisi else "[Fotoğraf yüklendi]",
                    "Özet": response.text[:120] + "..."
                }
                
                if "gecmis" not in st.session_state:
                    st.session_state.gecmis = []
                st.session_state.gecmis.append(yeni_kayit)

            except Exception as e:
                st.error(f"Hata oluştu: {e}")

if "gecmis" in st.session_state and st.session_state.gecmis:
    st.divider()
    st.subheader("🕒 Bugünün Kayıtları")
    df = pd.DataFrame(st.session_state.gecmis)
    st.dataframe(df, use_container_width=True)
