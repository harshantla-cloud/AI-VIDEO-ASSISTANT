import os
import tempfile
import streamlit as st
from dotenv import load_dotenv


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()


def get_secret(key):
    """
    Get API key from:
    1. Environment variable / .env
    2. Streamlit Cloud Secrets
    """

    value = os.getenv(key)

    if value:
        return value

    try:
        return st.secrets[key]
    except Exception:
        return None


# --------------------------------------------------
# API Keys
# --------------------------------------------------

MISTRAL_API_KEY = get_secret("MISTRAL_API_KEY")
SARVAM_API_KEY = get_secret("SARVAM_API_KEY")


# IMPORTANT:
# Other project modules use os.getenv().
# Therefore, copy Streamlit Secrets into environment variables.

if MISTRAL_API_KEY:
    os.environ["MISTRAL_API_KEY"] = MISTRAL_API_KEY

if SARVAM_API_KEY:
    os.environ["SARVAM_API_KEY"] = SARVAM_API_KEY


# --------------------------------------------------
# Streamlit Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# Custom Styling
# --------------------------------------------------

st.markdown(
    """
    <style>

        .main {
            padding-top: 1rem;
        }

        .hero {
            padding: 2rem 1.5rem;
            border-radius: 18px;
            margin-bottom: 1.5rem;
            background: linear-gradient(
                135deg,
                rgba(30, 41, 59, 0.95),
                rgba(15, 23, 42, 0.98)
            );
            border: 1px solid rgba(148, 163, 184, 0.20);
        }

        .hero h1 {
            font-size: 2.5rem;
            margin-bottom: 0.4rem;
        }

        .hero p {
            color: #cbd5e1;
            font-size: 1.05rem;
            margin-bottom: 0;
        }

        .metric-card {
            padding: 1rem;
            border-radius: 14px;
            border: 1px solid rgba(148, 163, 184, 0.20);
            background: rgba(15, 23, 42, 0.45);
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 700;
            margin-top: 1rem;
            margin-bottom: 0.8rem;
        }

        .stButton > button {
            width: 100%;
            border-radius: 10px;
            font-weight: 600;
        }

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Session State
# --------------------------------------------------

if "result" not in st.session_state:
    st.session_state.result = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# --------------------------------------------------
# Header
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <h1>🎥 AI Video Assistant</h1>
        <p>
            Transform videos and meetings into transcripts, summaries,
            action items, decisions, and intelligent answers.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:

    st.header("⚙️ Input Settings")

    source_type = st.radio(
        "Choose input type",
        ["YouTube URL", "Local Video / Audio"],
    )

    language = st.selectbox(
        "Transcription mode",
        ["english", "hinglish"],
        format_func=lambda x: (
            "English — Whisper"
            if x == "english"
            else "Hinglish — Sarvam AI"
        ),
    )

    st.divider()

    st.markdown("### 🔑 API Configuration")

    # Check API keys
    mistral_status = bool(MISTRAL_API_KEY)
    sarvam_status = bool(SARVAM_API_KEY)

    st.write(
        f"{'🟢' if mistral_status else '🔴'} Mistral API"
    )

    if language == "hinglish":
        st.write(
            f"{'🟢' if sarvam_status else '🔴'} Sarvam API"
        )

    st.divider()

    st.caption(
        "AI Video Assistant • RAG-powered meeting intelligence"
    )


# --------------------------------------------------
# Input Section
# --------------------------------------------------

st.markdown(
    '<div class="section-title">📥 Add Your Video</div>',
    unsafe_allow_html=True,
)

source = None
uploaded_file = None


if source_type == "YouTube URL":

    source = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
    )

else:

    uploaded_file = st.file_uploader(
        "Upload a video or audio file",
        type=[
            "mp4",
            "mkv",
            "mov",
            "avi",
            "mp3",
            "wav",
            "m4a",
            "webm",
        ],
    )


# --------------------------------------------------
# Process Button
# --------------------------------------------------

process_clicked = st.button(
    "🚀 Analyze Video",
    type="primary",
)


if process_clicked:
    from main import run_pipeline
    from core.rag_engine import ask_question


    # ----------------------------------------------
    # Validate API keys
    # ----------------------------------------------

    if not mistral_status:

        st.error(
            "MISTRAL_API_KEY is missing. "
            "Add it to Streamlit Cloud Secrets."
        )

        st.stop()


    if language == "hinglish" and not sarvam_status:

        st.error(
            "SARVAM_API_KEY is required for Hinglish transcription."
        )

        st.stop()


    # ----------------------------------------------
    # Prepare source
    # ----------------------------------------------

    if source_type == "YouTube URL":

        if not source:

            st.warning(
                "Please enter a valid YouTube URL."
            )

            st.stop()

        input_source = source

    else:

        if uploaded_file is None:

            st.warning(
                "Please upload a video or audio file."
            )

            st.stop()

        suffix = os.path.splitext(
            uploaded_file.name
        )[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:

            temp_file.write(
                uploaded_file.getbuffer()
            )

            input_source = temp_file.name


    # ----------------------------------------------
    # Run AI Pipeline
    # ----------------------------------------------

    try:

        with st.status(
            "Processing your video...",
            expanded=True,
        ) as status:

            st.write(
                "🎵 Extracting and processing audio..."
            )

            st.write(
                "🎙️ Generating transcript..."
            )

            st.write(
                "🧠 Creating AI summary..."
            )

            st.write(
                "📋 Extracting action items and decisions..."
            )

            st.write(
                "🔎 Building RAG knowledge base..."
            )

            result = run_pipeline(
                input_source,
                language,
            )

            status.update(
                label="Analysis completed successfully!",
                state="complete",
                expanded=False,
            )


        # Save result
        st.session_state.result = result

        # Reset chat
        st.session_state.chat_history = []


        # Remove temporary uploaded file
        if source_type == "Local Video / Audio":

            try:
                os.remove(input_source)

            except OSError:
                pass


        st.success(
            "Your video has been analyzed successfully."
        )


    except Exception as e:

        st.error(
            "Something went wrong while processing the video."
        )

        with st.expander("Technical details"):

            st.exception(e)


# --------------------------------------------------
# Results
# --------------------------------------------------

result = st.session_state.result


if result:

    st.divider()


    # ----------------------------------------------
    # Title
    # ----------------------------------------------

    st.markdown(
        '<div class="section-title">📌 Meeting Overview</div>',
        unsafe_allow_html=True,
    )

    st.subheader(
        result["title"]
    )


    # ----------------------------------------------
    # Main Results
    # ----------------------------------------------

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📝 Summary",
            "✅ Action Items",
            "🔑 Decisions",
            "❓ Open Questions",
            "📄 Transcript",
        ]
    )


    with tab1:

        st.markdown(
            "### Meeting Summary"
        )

        st.markdown(
            result["summary"]
        )


    with tab2:

        st.markdown(
            "### Action Items"
        )

        st.markdown(
            result["action_items"]
        )


    with tab3:

        st.markdown(
            "### Key Decisions"
        )

        st.markdown(
            result["key_decisions"]
        )


    with tab4:

        st.markdown(
            "### Open Questions"
        )

        st.markdown(
            result["open_questions"]
        )


    with tab5:

        st.markdown(
            "### Full Transcript"
        )

        st.text_area(
            "Transcript",
            value=result["transcript"],
            height=500,
            label_visibility="collapsed",
        )


    # ----------------------------------------------
    # Download Transcript
    # ----------------------------------------------

    st.download_button(
        label="⬇️ Download Transcript",
        data=result["transcript"],
        file_name="meeting_transcript.txt",
        mime="text/plain",
    )


    # ----------------------------------------------
    # RAG Chat
    # ----------------------------------------------

    st.divider()

    st.markdown(
        '<div class="section-title">💬 Chat With Your Video</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Ask questions about the analyzed meeting. "
        "Answers are generated using the transcript RAG pipeline."
    )


    # ----------------------------------------------
    # Chat History
    # ----------------------------------------------

    for message in st.session_state.chat_history:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )


    # ----------------------------------------------
    # Chat Input
    # ----------------------------------------------

    question = st.chat_input(
        "Ask something about the meeting..."
    )


    if question:

        # Save user message
        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": question,
            }
        )


        with st.chat_message("user"):

            st.markdown(
                question
            )


        # Generate answer
        with st.chat_message("assistant"):

            with st.spinner(
                "Searching the meeting transcript..."
            ):

                try:

                    answer = ask_question(
                        result["rag_chain"],
                        question,
                    )

                    st.markdown(
                        answer
                    )

                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )


                except Exception as e:

                    st.error(
                        "Unable to generate an answer right now."
                    )

                    with st.expander(
                        "Technical details"
                    ):

                        st.exception(e)


# --------------------------------------------------
# Empty State
# --------------------------------------------------

else:

    st.info(
        "👆 Add a YouTube URL or upload a video/audio file "
        "to start the AI analysis."
    )

    st.markdown(
        """
        ### ✨ What this assistant can do

        - 🎙️ Transcribe video/audio
        - 📝 Generate professional meeting summaries
        - ✅ Extract action items
        - 🔑 Identify key decisions
        - ❓ Find unresolved questions
        - 🧠 Build a vector-based knowledge base
        - 💬 Answer questions using RAG
        """
    )
