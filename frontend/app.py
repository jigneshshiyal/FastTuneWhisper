import streamlit as st
import requests
import tempfile

st.title("🎙️ Upload Audio for Hindi Whisper Transcription")

uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a"])

if uploaded_file:
    st.audio(uploaded_file, format="audio/wav")

    if st.button("Transcribe"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(uploaded_file.read())
            tmp.seek(0)
            files = {'file': tmp}
            response = requests.post("http://localhost:8000/transcribe/", files=files)

        if response.status_code == 200:
            result = response.json()
            st.success("✅ Transcription Complete!")
            st.markdown(f"**📝 Transcription:**\n\n{result['text']}")
            st.markdown(f"**🌐 Language:** {result['language']}")
            st.markdown(f"**⏱️ Duration:** {result['duration']:.2f} sec")
        else:
            st.error("❌ Error: " + response.text)
