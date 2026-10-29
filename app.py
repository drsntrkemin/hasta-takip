import os
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Hasta Beslenme Takibi", page_icon="🍲", layout="centered")

st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 12px; height: 3.2em; background-color: #1e7e34; color: white; font-weight: bold; font-size: 1.1em;}
    </style>
""", unsafe_allow_html=True)

st.title("🍲 Hasta Beslenme Takip")
st.write("Lütfen verilen öğünü yazın veya tabağın fotoğrafını yükleyin.")

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

if not api_key:
    st.error("API anahtarı bulunamadı! Lütfen ayarlardan GEMINI_API_KEY ekleyin.")
    st.stop()

client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = """
Sen yaşlı ve yatan hasta bakım süreçlerinde çalışan hasta bakıcılar için tasarlanmış bir "Beslenme ve Kalori Takip Asistanı"sın.
Kullanıcı bir metin veya tabak fotoğrafı paylaştığında:
1. Besinleri ve porsiyonları dikkatle incele.
2. Kalori, protein ve tahmini sıvı miktarını hesapla.
3. Yanıtı her zaman şu net formatta ver:

### 📋 Öğün Analizi
- [Besin adı] (~[Miktar]) -> ~[X] kcal | [Y]g Protein

### 📊 Toplam Değerler
- **Toplam Kalori:** ~[...] kcal
- **Protein:** ~[...] g
- **Tahmini Sıvı:** ~[...] ml

### 💡 Bakıcı Notu
[1-2 cümlelik pratik geribildirim; sıvı, çiğneme veya protein uyarısı vb.]
"""

metin_girisi = st.text_area("Öğün Açıklaması (Örn: 1 kase mercimek çorbası, yarım dilim ekmek):", height=100)
fotograf = st.file_uploader("Veya Tabak Fotoğrafı Çek / Yükle:", type=["jpg", "jpeg", "png"])

if fotograf:
    img = Image.open(fotograf)
    st.image(img, caption="Yüklenen Görsel", use_container_width=True)

if st.button("Kaydet ve Hesapla"):
    if not metin_girisi and not fotograf:
        st.warning("Lütfen bir açıklama yazın veya fotoğraf yükleyin.")
    else:
        with st.spinner("Öğün ve besin değerleri hesaplanıyor..."):
            try:
                icerik = []
                if fotograf:
                    icerik.append(img)
                if metin_girisi:
                    icerik.append(metin_girisi)

                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=icerik,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.2
                    )
                )

                st.success("Hesaplama Başarıyla Tamamlandı!")
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
