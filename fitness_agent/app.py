import streamlit as st
import google.generativeai as genai
import re
from PIL import Image
import speech_recognition as sr
from io import BytesIO
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure Google Generative AI
GOOGLE_API_KEY = ""
genai.configure(api_key=GOOGLE_API_KEY)

# Action regex to identify actions in the chatbot response
action_re = re.compile(r'^Action:\s*(\w+)\s*:\s*(.+)$')

# Define the chatbot class and action functions
class Chatbot:
    def __init__(self, system):
        self.system = system
        self.messages = []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result

    def execute(self):
        prompt = "\n".join([f'{msg["role"]}:{msg["content"]}' for msg in self.messages])
        model = genai.GenerativeModel("gemini-1.5-flash")
        raw_response = model.generate_content(prompt)
        result_text = raw_response.candidates[0].content.parts[0].text
        return result_text

# Action functions using Gemini API
def generate_workout(level):
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(f"Generate a workout plan for a {level} fitness level")
    return response.candidates[0].content.parts[0].text

def suggest_meal(preferences):
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(f"Suggest a meal plan with {preferences}")
    return response.candidates[0].content.parts[0].text

def motivational_quotes():
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content("Give me a motivational quote.")
    return response.candidates[0].content.parts[0].text

# Known actions mapping
known_actions = {
    "generate_workout": generate_workout,
    "suggest_meal": suggest_meal,
    "motivational_quotes": motivational_quotes
}

# Query function that interacts with the chatbot
def query(question, max_turns=5):
    i = 0
    bot = Chatbot(prompt)
    next_prompt = question
    while i < max_turns:
        i += 1
        result = bot(next_prompt)
        actions = [action_re.match(a) for a in result.split('\n') if action_re.match(a)]
        
        if actions:
            action, action_input = actions[0].groups()
            if action not in known_actions:
                raise Exception(f"Unknown action: {action}: {action_input}")
            observation = known_actions[action](action_input.strip())
            next_prompt = f"Answer: {observation}"
        else:
            return result

# Define the system prompt
prompt = """ 
You are a fitness assistant. You help users with workout plans, dietary advice, and motivational quotes.
Your available actions are:
generate_workout:
e.g. generate_workout: Beginner 
Generates a workout plan based on the user's fitness level.
suggest_meal:
e.g. suggest_meal: Low-carb breakfast 
Suggests a meal plan based on the user's dietary preferences.
motivational_quotes:
e.g. motivational_quotes:
Returns a motivational quote to inspire the user.
"""

# Function for visual query answering
def visual_query_answer(image, user_query):
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
    prompt = f"Using the uploaded image and the query '{user_query}', provide fitness-related advice or suggestions."
    # Send the image and the query
    response = model.generate_content([image, prompt])
    return response.candidates[0].content.parts[0].text

# Function to handle voice input using SpeechRecognition
def voice_search():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening for your voice query...")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I could not understand the audio."
        except sr.RequestError as e:
            return f"Could not request results from Google Speech Recognition; {e}"

# Streamlit App Chatbot Interface
st.title("Fitness Assistant Chatbot")
#st.write("Interact with the chatbot for workout plans, meal suggestions, motivational quotes, or image-based advice!")

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# Display chat history
def display_chat_history():
    if st.session_state['chat_history']:
        st.write("Chat History")
        for chat in st.session_state['chat_history']:
            st.write(f"**You**: {chat['user']}")
            st.write(f"**Assistant**: {chat['bot']}")

# Chatbot input method - Text, Voice, Image Queries
user_input = st.text_input("Ask anything, or upload an image below:")

# Text Query Handling
if user_input:
    response = query(user_input)
    st.session_state['chat_history'].append({"user": user_input, "bot": response})

# Voice Query Handling
st.write("Or, record a voice query:")
if st.button("Record Voice"):
    user_voice_query = voice_search()
    if user_voice_query:
        response = query(user_voice_query)
        st.session_state['chat_history'].append({"user": user_voice_query, "bot": response})

# Image Query Handling
st.write("Or, upload a fitness-related image for visual question answering:")
uploaded_image = st.file_uploader("Upload a fitness-related image", type=["jpg", "png"])
if uploaded_image:
    img = Image.open(uploaded_image)
    st.image(img, caption="Uploaded Image", use_column_width=True)
    image_query = st.text_input("Ask a question related to the image")
    if image_query:
        result = visual_query_answer(uploaded_image, image_query)
        st.session_state['chat_history'].append({"user": image_query, "bot": result})

# Display chat history
display_chat_history()
