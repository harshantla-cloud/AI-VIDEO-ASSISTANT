import os

import streamlit as st
from dotenv import load_dotenv

from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough, RunnableLambda


# --------------------------------------------------
# Environment / Secrets
# --------------------------------------------------

load_dotenv()


def get_mistral_api_key():
    """
    Get Mistral API key from:
    1. Environment variable / .env
    2. Streamlit Cloud Secrets
    """

    api_key = os.getenv("MISTRAL_API_KEY")

    if api_key:
        return api_key

    try:
        api_key = st.secrets["MISTRAL_API_KEY"]
    except Exception:
        api_key = None

    if not api_key:
        raise ValueError(
            "MISTRAL_API_KEY is missing. "
            "Add it to Streamlit Cloud Secrets."
        )

    return api_key


# --------------------------------------------------
# Mistral LLM
# --------------------------------------------------

def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=get_mistral_api_key(),
        temperature=0.3,
    )


# --------------------------------------------------
# Transcript Chunking
# --------------------------------------------------

def split_transcript(transcript: str) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200,
    )

    return splitter.split_text(transcript)


# --------------------------------------------------
# Meeting Summary
# --------------------------------------------------

def summarize(transcript: str) -> str:

    llm = get_llm()

    map_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Summarize this portion of a meeting transcript concisely.",
            ),
            (
                "human",
                "{text}",
            ),
        ]
    )

    map_chain = (
        map_prompt
        | llm
        | StrOutputParser()
    )

    chunks = split_transcript(transcript)

    chunk_summaries = [
        map_chain.invoke({"text": chunk})
        for chunk in chunks
    ]

    combined = "\n\n".join(chunk_summaries)

    combined_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert meeting summarizer. "
                "Combine these partial summaries into one final "
                "professional meeting summary in bullet points.",
            ),
            (
                "human",
                "{text}",
            ),
        ]
    )

    combined_chain = (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | combined_prompt
        | llm
        | StrOutputParser()
    )

    return combined_chain.invoke(combined)


# --------------------------------------------------
# Meeting Title
# --------------------------------------------------

def generate_title(transcript: str) -> str:

    llm = get_llm()

    title_chain = (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Based on the meeting transcript, generate a short "
                    "professional meeting title (max 8 words). "
                    "Only return the title, nothing else.",
                ),
                (
                    "human",
                    "{text}",
                ),
            ]
        )
        | llm
        | StrOutputParser()
    )

    return title_chain.invoke(transcript[:2000])

