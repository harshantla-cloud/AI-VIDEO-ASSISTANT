import os
import yt_dlp
from pydub import AudioSegment


# --------------------------------------------------
# Configuration
# --------------------------------------------------

DOWNLOAD_DIR = "downloads"

os.makedirs(
    DOWNLOAD_DIR,
    exist_ok=True
)


# --------------------------------------------------
# YouTube Audio Download
# --------------------------------------------------

def download_youtube_audio(url: str) -> str:
    """
    Download audio from a YouTube URL and convert it to WAV.
    """

    output_template = os.path.join(
        DOWNLOAD_DIR,
        "%(id)s.%(ext)s"
    )

    ydl_opts = {
        # Prefer audio-only formats.
        "format": "bestaudio/best",

        "outtmpl": output_template,

        # Extract audio as WAV.
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],

        # Network / YouTube compatibility
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,

        # Use a normal browser-like client.
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        },

        # Retry temporary failures.
        "retries": 5,
        "fragment_retries": 5,

        # Do not use browser cookies by default.
        "cookiefile": None,
    }


    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            video_id = info.get("id")

            if not video_id:
                raise RuntimeError(
                    "Could not determine YouTube video ID."
                )

            # FFmpegExtractAudio changes the extension to .wav
            wav_path = os.path.join(
                DOWNLOAD_DIR,
                f"{video_id}.wav"
            )

            if not os.path.exists(wav_path):

                raise FileNotFoundError(
                    "YouTube audio was downloaded, "
                    "but the WAV file could not be found."
                )

            return wav_path


    except yt_dlp.utils.DownloadError as e:

        raise RuntimeError(
            "Unable to download this YouTube video. "
            "YouTube returned an access/download error. "
            "Try another public video."
        ) from e


# --------------------------------------------------
# Convert Local File to WAV
# --------------------------------------------------

def convert_to_wav(input_path: str) -> str:
    """
    Convert any audio/video file to WAV format using pydub.
    """

    output_path = (
        os.path.splitext(input_path)[0]
        + "_converted.wav"
    )

    audio = AudioSegment.from_file(
        input_path
    )

    # Whisper works well with mono 16 kHz audio.
    audio = (
        audio
        .set_channels(1)
        .set_frame_rate(16000)
    )

    audio.export(
        output_path,
        format="wav"
    )

    return output_path


# --------------------------------------------------
# Split Audio into Chunks
# --------------------------------------------------

def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10
) -> list:
    """
    Split WAV audio into smaller chunks.
    """

    audio = AudioSegment.from_wav(
        wav_path
    )

    chunk_ms = (
        chunk_minutes
        * 60
        * 1000
    )

    chunks = []


    for i, start in enumerate(
        range(
            0,
            len(audio),
            chunk_ms
        )
    ):

        chunk = audio[
            start:start + chunk_ms
        ]

        chunk_path = (
            f"{wav_path}_chunk_{i}.wav"
        )

        chunk.export(
            chunk_path,
            format="wav"
        )

        chunks.append(
            chunk_path
        )


    return chunks


# --------------------------------------------------
# Main Input Processor
# --------------------------------------------------

def process_input(source: str) -> list:
    """
    Detect whether the input is a URL or local file,
    convert it to WAV, and split it into chunks.
    """

    if (
        source.startswith("http://")
        or source.startswith("https://")
    ):

        print(
            "Detected YouTube URL. "
            "Downloading audio..."
        )

        wav_path = download_youtube_audio(
            source
        )

    else:

        print(
            "Detected local file. "
            "Converting to WAV..."
        )

        wav_path = convert_to_wav(
            source
        )


    print(
        "Chunking audio..."
    )

    chunks = chunk_audio(
        wav_path
    )


    print(
        f"Audio ready — "
        f"{len(chunks)} chunk(s) created."
    )


    return chunks

