import streamlit as st
from qa_model import build_retriever, answer_question

st.title("Gemini Based QA App")

urls = [
    "https://en.wikipedia.org/wiki/Tata_Motors",
    "https://en.wikipedia.org/wiki/Tesla,_Inc."
]

# Cache retriever
@st.cache_resource
def get_retriever():
    return build_retriever(urls)

retriever = get_retriever()

question = st.text_input("Ask a question:")

if st.button("Get Answer") and question:
    answer, sources = answer_question(question, retriever)

    st.subheader("Answer")
    st.write(answer)

    st.subheader("Sources")
    for s in sources:
        st.write("-", s)
