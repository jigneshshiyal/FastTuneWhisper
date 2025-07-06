from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel
import torch
import torchaudio
import soundfile as sf
import tempfile
import os

# Set backend for torchaudio
torchaudio.set_audio_backend("soundfile")  # or "sox_io" if available

# Init FastAPI app
app = FastAPI()

# Load Faster-Whisper model
model_path = "./models/ctranslate2-whisper-hindi-custom-model"  # Replace with your actual converted model path
device = "cuda" if torch.cuda.is_available() else "cpu"
model = WhisperModel(model_path, compute_type="int8", device=device)

# Audio preprocessing: convert to 16kHz mono WAV
def preprocess_audio_from_path(path: str, target_sr: int = 16000) -> str:
    waveform, sample_rate = sf.read(path)
    waveform = torch.tensor(waveform).float()

    # Convert stereo to mono if needed
    if waveform.ndim == 1:
        waveform = waveform.unsqueeze(0)
    elif waveform.shape[1] > 1:
        waveform = waveform.mean(dim=1).unsqueeze(0)

    if sample_rate != target_sr:
        waveform = torchaudio.functional.resample(waveform, sample_rate, target_sr)

    # Save as 16kHz mono WAV for transcription
    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    torchaudio.save(output_path, waveform, target_sr)
    return output_path

# Handle single file transcription
@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        # Save uploaded file to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".input") as tmp:
            tmp.write(await file.read())
            tmp.flush()
            tmp_path = tmp.name

        # Preprocess audio to standard format
        processed_path = preprocess_audio_from_path(tmp_path)

        # Transcribe with Faster-Whisper
        segments, info = model.transcribe(processed_path, beam_size=5)
        transcription = " ".join([seg.text for seg in segments])

        # Clean up temp files
        os.remove(tmp_path)
        os.remove(processed_path)

        return {
            "text": transcription,
            "language": info.language,
            "duration": info.duration
        }

    except Exception as e:
        return {"error": str(e)}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000,)