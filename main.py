import openai
import os
import time
import logging
from datetime import datetime
import json
import streamlit as st
client = openai.OpenAI()
model_i = "gpt-3.5-turbo"
openai.api_key = os.environ.get('OPENAI_API_KEY')
news_api_key = os.environ.get('news_api_key')

import requests

def get_news_articles(topic):
    url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={news_api_key}&pageSize=5"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            news = json.dumps(response.json(), indent = 4)
            news_json = json.loads(news)

            data = news_json
            status = data["status"]
            totalResult = data["totalResults"]
            articles = data["articles"]
            finalNews = []

            for article in articles:
                source_name = article['source']['name']
                author = article['author']
                title = article['title']
                description = article['description']
                url = article['url']
                title_description = f"""
                Title: {title}
                Author: {author}
                Description: {description}
                URL: {url}
                Source: {source_name}
                """

         
         
                finalNews.append(title_description)
            
            return finalNews
        else:
            return ['hello','kitty']
        






    

        
    except requests.exceptions.RequestException as e:
        print("Error occurred",e)

   



class AssistantManger:
    thread_id = "thread_d68wrK0oRXZ2Sj0hVdvB3pNL"
    assistant_id = "asst_LJ6M4xQbabvlzFSMc0swXcSj"
    def __init__(self, model: str = model_i):
        self.client = client
        self.model = model_i
        self.assistant = None
        self.thread = None
        self.run = None
        self.summary = None

        if AssistantManger.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(
                assistant_id= AssistantManger.assistant_id,
            )
        if AssistantManger.thread_id:
            self.thread = self.client.beta.threads.retrieve(
                thread_id=AssistantManger.thread_id
            )
    def createAssistant(self,name,instructions,tools):
        if not self.assistant:
            assistant_client = self.client.beta.assistants.create(
                name=name,
                model=self.model,
                instructions=instructions,
                tools=tools,
            )
            AssistantManger.assistant_id = assistant_client.id
            self.assistant = assistant_client
            print(f"Assistant_id = {self.assistant.id}")
    
    def createThread(self):
        if not self.thread_id:
            threadObject = self.client.beta.threads.create()
            AssistantManger.thread_id = threadObject.id
            self.thread = threadObject
            print(f"Thread_id = {self.thread_id}")

    def add_messages_to_thread(self, role,content):
        if self.thread_id:
            self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role=role,
                content=content,
            )
    def run_assistant(self,instruction):
        if self.assistant and self.thread:
            self.run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id,
                instructions = instruction,
                )
    def callRequiredFunction(self, required_action):
        if not self.run:
            return
        tool_outputs = []
        for action in required_action["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action['function']['arguments'])

            if func_name == "get_news_articles":
                
                output = get_news_articles(topic=arguments['topic'])
                print(f"Stuff:::::{output}")
                final_str = ""
                for item in output:
                    final_str += "".join(item)
               
                tool_outputs.append({
                    
                    "tool_call_id": action["id"],
                    "output":final_str,
                    })
            else:
                raise ValueError("Maa chuda")
        try:
            print(f"Submitting output back to the function")
            self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread_id,
            run_id=self.run.id,
            tool_outputs=tool_outputs
            )
        except Exception as e:
             print(f"An error occurred when submitting tool outputs: {e}")
             raise
            

    def getSummary(self):
        return self.summary
    


    def process_messages(self):
        if self.thread:
            mes = self.client.beta.threads.messages.list(thread_id=self.thread_id)
            summary  = []
            last_message = mes.data[0]
            role = last_message.role
            responce = last_message.content[0].text.value
            summary.append(responce)
            self.summary = "\n".join(summary)
            print(f"Summary------->{role.capitalize()}: {responce}")
        return summary
    def waitForResponse(self):
        if self.thread and self.run:
            while True:
                time.sleep(5)
                run_status = self.client.beta.threads.runs.retrieve(run_id=self.run.id,thread_id=self.thread_id)
                print(f"Run status {run_status.model_dump_json(indent=4)}")
                if run_status.status== "completed":
                    self.process_messages()
                    break
                elif run_status.status== "requires_action":
                    print("Function calling now ...")
                    self.callRequiredFunction(
                        required_action=run_status.required_action.submit_tool_outputs.model_dump()
                    )

    def run_steps(self):
        run_steps = self.client.beta.threads.runs.steps.list(
            thread_id=self.thread_id,
            run_id=self.run.id,
        )







import streamlit as st

def main():
    # Set page configuration
    st.set_page_config(page_title="News Aggregator", layout="wide")

    # Apply custom CSS for styling
    st.markdown(
        """
        <style>
        /* General page background */
       .reportview-container {
            background: #ffffff; /* Lighter background for better readability */
            color: #555; /* Darker text for readability */
            font-family: Arial, sans-serif; /* Clean and readable font */
            font-size: 16px; /* Larger font size for easier reading */
            line-height: 1.5; /* Increased line height for better text flow */
}
        
        /* Sidebar background */
        .sidebar .sidebar-content {
            background: #e8e8e8;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 8px;
        }
        
        /* Text input styling */
        .stTextInput > div > input {
            font-size: 18px;
            border-radius: 8px;
            padding: 10px;
            border: 1px solid #ccc;
        }
        
        /* Title positioning */
        .reportview-container .main .block-container {
            padding-top: 10px;
            padding-left: 20px;
            max-width: 800px;
        }
        
        /* General text styling */
        .stMarkdown {
            font-size: 16px;
            color: #555;
        }
        </style>
        """, unsafe_allow_html=True
    )

    st.title("News Aggregator")

    with st.form(key="user_input_form"):
        st.write("Enter the topic name to get the latest news articles:")
        instructions = st.text_input("Topic Name", placeholder="e.g., India")
        submit_button = st.form_submit_button(label="Run")

        if submit_button:
            st.write("Processing your request...")
            
            manager =AssistantManger()
            manager.createAssistant(
                name="News Aggregator",
                instructions="You are an article summarizer who can take a list of article titles and descriptions and write a short summary of all the news articles. You are also capable of categorizing the article as negative, positive, or neutral toward the topic.",
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "get_news_articles",
                        "description": "Get the list of articles/news for the given topic",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "topic": {
                                    "type": "string",
                                    "description": "The topic for the news, e.g., Pakistan"
                                }
                            },
                            "required": ["topic"],
                        },
                    },
                }]
            )

            manager.createThread()
            manager.add_messages_to_thread(
                role="user",
                content=f"Summarize the news for this topic: {instructions}"
            )
            manager.run_assistant(
                instruction="Summarize the news and determine its sentiment towards the topic."
            )

            manager.waitForResponse()
            summary = manager.getSummary()
            st.write("### Summary:")
            st.write(summary)
           # st.code(manager.run_steps(), line_numbers=True)

if __name__ == "__main__":
    main()
