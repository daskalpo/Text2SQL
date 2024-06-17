from PIL import Image
import operations as op
import pandas as pd
import os
import streamlit as st
from streamlit_chat import message
from pathlib import Path
import tempfile
import ast
import re
from dotenv import load_dotenv
# import wikipedia
from typing import Any, List, Tuple
# from streamlit_searchbox import st_searchbox

load_dotenv()
temppath = os.getenv("tempfolder")
GPT35_TURBO_MODEL_NAME = os.getenv("GPT35_TURBO_MODEL_NAME")


def check_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system",
           "content": "YOU are an expert SQL developer. Follow the instructions strictly.You will provide accurate and precise responses. You will avoid generating any explanations."}]

    if 'run_first' not in st.session_state:
        st.session_state.run_first = True


def display_previous_messages():    
    for message in st.session_state.messages[1:]:
        if message['role'] in ["user","assistant"]:
        # print('************\n',message)
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # function with list of labels


# def search_wikipedia(searchterm: str) -> List[any]:
#     # return [f"{searchterm}_{i}" for i in range(10)]
#     return wikipedia.search(searchterm) if searchterm else []


def search(searchterm: str) -> List[Tuple[str, any]]:
    data = [
        ("apple", {"type": "fruit", "color": "red"}),
        ("banana", {"type": "fruit", "color": "yellow"}),
        ("carrot", {"type": "vegetable", "color": "orange"}),
        ("date", {"type": "fruit", "color": "brown"}),
        ("grape", {"type": "fruit", "color": "purple"}),
    ]

    # Search for items that contain the searchterm in their name
    results = [item for item in data if searchterm.lower() in item[0].lower()]

    # Return the list of matching tuples
    return results

# st.session_state.messages = []
# st.session_state.messages.append({"role": "system",
#              "content": "YOU are an expert SQL developer. Follow the instructions strictly.You will provide accurate and precise responses. You will avoid generating any explanations."})

# Streamlit app code
def main():
    st.set_page_config(
        page_title="Talk to DATA",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    hide_menu_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                .appview-container {
                    padding-bottom: 3.35rem;
                }
                .appview-container .main .block-container {
                    padding-top: 0rem;
                    padding-bottom: 0rem;
                    padding-left: 1rem;
                    padding-right: 1rem;

                }
                .block-container{
                    top: 0.3rem;
                    bottom: 0rem;
                    padding-bottom: 10rem;
                }
                .footer {
                    position: fixed;
                    left: 0px;
                    bottom: 0px;
                    width: 100%;
                    background-color: #C5C5C5;
                    color: black;
                    text-align: center;
                    padding-left: 0px;
                    padding-top: 12px;

                }
                </style>
                <div class="footer">
                <p><a style='display: block; color: black; text-align: center;' href="" target="_blank">©️ All rights reserved by Capgemini</a></p>
                </div>
                """
    st.markdown(hide_menu_style, unsafe_allow_html=True)
    # dg.ingest_csv()
    image = Image.open(r'C:/Users/kalpdas/Downloads/image 1.png')
    st.image(image, use_column_width=True, channels="RGB")

    st.markdown(
        "<h1 style='text-align: center; color: #ffffff; margin-top: -125px'>Talk to DATA</h1>",
        unsafe_allow_html=True,
    )

    # pass search function to searchbox
    # selected_value = st_searchbox(
    #     search,
    #     key="wiki_searchbox",
    # )
    client = op.azureclient()
    check_session_state()
    display_previous_messages()

    # st.session_state.messages.append({"role": "system", "content": system_message})
    user_input = st.chat_input("Enter query")
    if user_input:
        with st.chat_message("user"):  st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            with st.spinner(text="Generating Result..."):
                # response = op.generate_prompt(client, user_input)
                # data = ast.literal_eval(response)]
                # print(st.session_state.messages)
                response, m = op.generate_prompt(client, user_input, st.session_state.messages)
                st.code(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
        # st.write(st.session_state.messages)


if __name__ == "__main__":
    main()

