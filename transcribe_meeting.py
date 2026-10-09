#!/usr/bin/env python3
"""Clean a meeting recording, split it by speaker and transcribe it.

Usage:
  python3 transcribe_meeting.py RECORDING.mp3 --models MODELS_DIR [--speakers N] [--out OUT_DIR]

Writes to OUT_DIR:
  <name>_clean.mp3     noise-reduced, loudness-normalised audio
  <name>_segments.json one entry per speaker turn: start, end, speaker, text
  <name>_transcript.txt  "[hh:mm:ss] SPEAKER_00: text" lines

Speakers come out as SPEAKER_00, SPEAKER_01, ...; names are matched afterwards
from the self-introductions and the recorder's notes file.

Models (sherpa-onnx GitHub releases), expected under MODELS_DIR:
  sherpa-onnx-pyannote-segmentation-3-0/model.onnx
  3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx
  sherpa-onnx-whisper-<size>/<size>-{encoder,decoder}.int8.onnx, <size>-tokens.txt
"""
import argparse, json, os, subprocess, sys
import numpy as np
import sherpa_onnx
import soundfile as sf

SR = 16000
MAX_CHUNK = 28.0  # Whisper handles at most 30 s per call


def clean_audio(src, out_mp3, out_wav):
    # Gentle denoise, cut rumble, normalise loudness for speech
    filt = "highpass=f=80,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", filt,
                    "-ac", "1", "-ar", "44100", "-b:a", "128k", out_mp3], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", "highpass=f=80,afftdn=nf=-25",
                    "-ac", "1", "-ar", str(SR), out_wav], check=True)


def diarize(audio, models, n_speakers):
    cfg = sherpa_onnx.OfflineSpeakerDiarizationConfig(
        segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
            pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(
                model=os.path.join(models, "sherpa-onnx-pyannote-segmentation-3-0/model.onnx")),
            num_threads=os.cpu_count() or 2),
        embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(
            model=os.path.join(models, "3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx"),
            num_threads=os.cpu_count() or 2),
        clustering=sherpa_onnx.FastClusteringConfig(
            num_clusters=n_speakers if n_speakers else -1, threshold=0.6),
        min_duration_on=0.3, min_duration_off=0.5)
    if not cfg.validate():
        sys.exit("Diarization config is invalid; check the model paths.")
    sd = sherpa_onnx.OfflineSpeakerDiarization(cfg)
    segs = sd.process(audio).sort_by_start_time()
    return [(s.start, s.end, s.speaker) for s in segs]


def merge_turns(segs, gap=0.6):
    # Join consecutive pieces from the same speaker into one turn
    out = []
    for s, e, spk in segs:
        if out and out[-1][2] == spk and s - out[-1][1] <= gap:
            out[-1][1] = e
        else:
            out.append([s, e, spk])
    return out


def make_recognizer(models, size, language):
    d = os.path.join(models, f"sherpa-onnx-whisper-{size}")
    return sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=os.path.join(d, f"{size}-encoder.int8.onnx"),
        decoder=os.path.join(d, f"{size}-decoder.int8.onnx"),
        tokens=os.path.join(d, f"{size}-tokens.txt"),
        language=language, task="transcribe", num_threads=os.cpu_count() or 2)


def transcribe(rec, audio, s, e):
    texts, t = [], s
    while t < e - 0.2:
        u = min(e, t + MAX_CHUNK)
        st = rec.create_stream()
        st.accept_waveform(SR, audio[int(t * SR):int(u * SR)])
        rec.decode_stream(st)
        txt = st.result.text.strip()
        if txt:
            texts.append(txt)
        t = u
    return " ".join(texts)


def hms(x):
    x = int(x)
    return f"{x // 3600:02d}:{x // 60 % 60:02d}:{x % 60:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recording")
    ap.add_argument("--models", required=True)
    ap.add_argument("--speakers", type=int, default=0, help="number of speakers if known")
    ap.add_argument("--whisper", default="small")
    ap.add_argument("--language", default="en")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    name = os.path.splitext(os.path.basename(a.recording))[0]
    clean_mp3 = os.path.join(a.out, f"{name}_clean.mp3")
    wav = os.path.join(a.out, f"{name}_16k.wav")
    print("Cleaning audio...", flush=True)
    clean_audio(a.recording, clean_mp3, wav)
    audio, sr = sf.read(wav, dtype="float32")
    assert sr == SR

    print("Finding speakers...", flush=True)
    turns = merge_turns(diarize(audio, a.models, a.speakers))
    print(f"  {len(turns)} turns, {len({t[2] for t in turns})} speakers", flush=True)

    print("Transcribing...", flush=True)
    rec = make_recognizer(a.models, a.whisper, a.language)
    rows = []
    for i, (s, e, spk) in enumerate(turns):
        text = transcribe(rec, audio, s, e)
        if text:
            rows.append({"start": round(s, 2), "end": round(e, 2), "speaker": f"SPEAKER_{spk:02d}", "text": text})
        if i % 20 == 0:
            print(f"  {i + 1}/{len(turns)} turns", flush=True)

    with open(os.path.join(a.out, f"{name}_segments.json"), "w") as f:
        json.dump(rows, f, indent=1, ensure_ascii=False)
    with open(os.path.join(a.out, f"{name}_transcript.txt"), "w") as f:
        for r in rows:
            f.write(f"[{hms(r['start'])}] {r['speaker']}: {r['text']}\n")
    os.remove(wav)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
