import os

import streamlit as st
from dotenv import load_dotenv

from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from core.vector_store import (
    build_vector_store,
    load_vector_store,
    get_retriever,
)


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
# Document Formatting
# --------------------------------------------------

def format_docs(docs):

    return "\n\n".join(
        [doc.page_content for doc in docs]
    )


# --------------------------------------------------
# Build RAG Chain
# --------------------------------------------------

def build_rag_chain(transcript: str):

    vector_store = build_vector_store(transcript)

    retriever = get_retriever(
        vector_store,
        k=4,
    )

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert meeting assistant.

Answer the user's question based ONLY on the meeting transcript
context provided below.

If the answer is not found in the context, say:

"I could not find this information in the meeting transcript."

Always be concise and precise.
If quoting someone, mention it clearly.

Context from meeting transcript:
{context}""",
            ),
            (
                "human",
                "{question}",
            ),
        ]
    )

    # Full LCEL RAG pipeline

    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


# --------------------------------------------------
# Load Existing RAG Chain
# --------------------------------------------------

def load_rag_chain():

    vector_store = load_vector_store()

    retriever = get_retriever(
        vector_store,
        k=4,
    )

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert meeting assistant.

Answer the user's question based ONLY on the meeting transcript
context provided below.

If the answer is not found in the context, say:

"I could not find this information in the meeting transcript."

Always be concise and precise.
If quoting someone, mention it clearly.

Context from meeting transcript:
{context}""",
            ),
            (
                "human",
                "{question}",
            ),
        ]
    )

    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


# --------------------------------------------------
# Ask Question
# --------------------------------------------------

def ask_question(
    rag_chain,
    question: str,
) -> str:

    print(f"Question: {question}")

    answer = rag_chain.invoke(question)

    print(f"Answer: {answer}")

    return answer

