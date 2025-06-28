import pyttsx3
import speech_recognition as sr
import datetime
import wikipedia
import pywhatkit as kit
import requests
import os
import subprocess
import sys
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import threading
import time
import logging

# =========================================
# Setup Logging
# =========================================
logging.basicConfig(filename='isabella.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# =========================================
# Initialize TTS Engine and Recognizer
# =========================================
engine = pyttsx3.init()
engine.setProperty('rate', 150)      # Speech speed
engine.setProperty('volume', 1.0)    # Volume (max is 1.0)
voices = engine.getProperty('voices')

# Select a female voice.
selected_voice = None
for voice in voices:
    if 'female' in voice.name.lower() or 'zira' in voice.name.lower() or 'eva' in voice.name.lower():
        selected_voice = voice
        break
if selected_voice:
    engine.setProperty('voice', selected_voice.id)
else:
    engine.setProperty('voice', voices[0].id)

recognizer = sr.Recognizer()

# Basic Identity Variables
USERNAME = "Sandeep"
BOTNAME = "Isabella"   # Changed from Jarvis to Isabella

# =========================================
# TTS and Listening Functions
# =========================================
def speak(text):
    """Converts text to speech, prints it, and logs the interaction."""
    print("Isabella:", text)
    logging.info("Isabella: " + text)
    engine.say(text)
    engine.runAndWait()

def listen_command():
    """Listens to your voice and returns the recognized command as text."""
    with sr.Microphone() as source:
        print("Listening for command...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio, language='en-US')
        command = command.lower()
        print("You said:", command)
        logging.info("User said: " + command)
        return command
    except sr.UnknownValueError:
        speak("Sorry, I did not understand that. Please say it again.")
        return ""
    except sr.RequestError:
        speak("Sorry, I'm having network issues.")
        logging.error("Network error during speech recognition.")
        return ""

def listen_for_wake_word():
    """Continuously listens until the wake word 'jarvis' is detected.
    (The wake word remains 'jarvis' even though the assistant's name is now Isabella.)"""
    with sr.Microphone() as source:
        speak("Isabella is now listening for the wake word...")
        while True:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            recorded_audio = recognizer.listen(source)
            try:
                text = recognizer.recognize_google(recorded_audio, language='en-US')
                text = text.lower()
                if 'jarvis' in text:  # wake word remains "jarvis"
                    print('Wake word detected!')
                    speak('Hi Sir, how can I help you?')
                    return
            except Exception as e:
                print("Could not understand audio during wake word detection.")

# =========================================
# Greeting Function
# =========================================
def greet_user():
    """Greets the user based on the time of day."""
    hour = datetime.datetime.now().hour
    if 6 <= hour < 12:
        speak("Good Morning " + USERNAME)
    elif 12 <= hour < 18:
        speak("Good Afternoon " + USERNAME)
    else:
        speak("Good Evening " + USERNAME)
    speak("I am " + BOTNAME + ". How can I help you today? For a list of commands, please say 'help'.")

# =========================================
# Previous Core Functions
# =========================================
def tell_time():
    now = datetime.datetime.now().strftime("%H:%M")
    speak("The time is " + now)

def search_wikipedia(query):
    speak("Searching Wikipedia for " + query)
    try:
        result = wikipedia.summary(query, sentences=2)
    except Exception as e:
        logging.error("Wikipedia error: " + str(e))
        result = "Sorry, I could not find information on that topic."
    output = "According to Wikipedia, " + result
    speak(output)
    print(output)

def play_on_youtube(query):
    speak("Playing " + query + " on YouTube")
    kit.playonyt(query)

def google_search(query):
    speak("Searching Google for " + query)
    kit.search(query)

def get_weather(city):
    api_key = "761864a3fd3616c24fd8f44453b90c8a"
    base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(base_url)
    data = response.json()
    if data.get("cod") != "404":
        main_data = data["main"]
        description = data["weather"][0]["description"]
        temperature = main_data["temp"]
        feels_like = main_data["feels_like"]
        output = f"In {city}, the temperature is {temperature}°C, but it feels like {feels_like}°C with {description}."
    else:
        output = "City not found."
    speak(output)

def tell_joke():
    headers = {"Accept": "application/json"}
    response = requests.get("https://icanhazdadjoke.com/", headers=headers)
    data = response.json()
    joke = data.get("joke", "Sorry, I couldn't fetch a joke right now.")
    speak(joke)

def open_notepad():
    speak("Opening Notepad.")
    subprocess.Popen(['notepad.exe'])

def open_calculator():
    speak("Opening Calculator.")
    subprocess.Popen(['calc.exe'])

def get_ip_address():
    try:
        data = requests.get("https://api.ipify.org?format=json").json()
        ip = data.get("ip", "Unknown")
    except Exception as e:
        logging.error("Error fetching IP address: " + str(e))
        ip = "Unable to fetch IP address."
    speak("Your public IP address is " + ip)

# ---- Conversation using a Local Model (DialoGPT) ----
print("Loading conversation model, please wait...")
logging.info("Loading DialoGPT model.")
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
print("Conversation model loaded.")
logging.info("DialoGPT model loaded.")

def chat_with_local_model(prompt):
    """Generates a conversational response using a local model (DialoGPT)."""
    new_user_input_ids = tokenizer.encode(prompt + tokenizer.eos_token, return_tensors='pt')
    chat_history_ids = model.generate(new_user_input_ids, max_length=150, pad_token_id=tokenizer.eos_token_id)
    response = tokenizer.decode(chat_history_ids[:, new_user_input_ids.shape[-1]:][0], skip_special_tokens=True)
    return response

def generate_sentence(topic):
    """Generates a sentence about a topic using a Wikipedia summary."""
    speak("Generating a sentence about " + topic)
    try:
        result = wikipedia.summary(topic, sentences=1)
    except Exception as e:
        logging.error("Error generating sentence: " + str(e))
        result = f"Sorry, I don't have any information on {topic}."
    output = f"Here's something interesting about {topic}: {result}"
    speak(output)
    return output

def chat_with_isabella():
    """Initiates a brief conversation with Isabella."""
    speak("Let's have a conversation. Tell me something.")
    user_input = listen_command()
    output = "You said: " + user_input + ". That's interesting!"
    speak(output)
    return output

def tell_shayari():
    """
    Fetches a random shayari from the PureVichar API and speaks it.
    """
    url = "https://www.purevichar.in/api/shayari/"
    try:
        response = requests.get(url)
        data = response.json()
        if "shayari" in data and data["shayari"]:
            shayari_entry = data["shayari"][0]
            shayari_lines = shayari_entry.get("quote", [])
            shayari_text = "\n".join(shayari_lines)
            author = shayari_entry.get("author", "Unknown")
            output = f"Here's a shayari:\n{shayari_text}\n- {author}"
        else:
            output = "Sorry, no shayari found at the moment."
    except Exception as e:
        logging.error("Error fetching shayari: " + str(e))
        output = "Sorry, I couldn't fetch a shayari right now."
    speak(output)

# =========================================
# New Software Control Functions
# =========================================
def open_software(software_name):
    """Opens software based on the given command keyword."""
    if 'chrome' in software_name:
        speak('Opening Chrome...')
        program = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        subprocess.Popen([program])
    elif 'microsoft edge' in software_name:
        speak('Opening Microsoft Edge...')
        program = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        subprocess.Popen([program])
    elif 'play' in software_name:
        speak('Opening YouTube...')
        pywhatkit.playonyt(software_name)
    elif 'notepad' in software_name:
        speak('Opening Notepad...')
        subprocess.Popen(['notepad.exe'])
    elif 'calculator' in software_name:
        speak('Opening Calculator...')
        subprocess.Popen(['calc.exe'])
    else:
        speak(f"I couldn't find the software {software_name}")

def close_software(software_name):
    """Closes software based on the given command keyword."""
    if 'chrome' in software_name:
        speak('Closing Chrome...')
        os.system("taskkill /f /im chrome.exe")
    elif 'microsoft edge' in software_name:
        speak('Closing Microsoft Edge...')
        os.system("taskkill /f /im msedge.exe")
    elif 'notepad' in software_name:
        speak('Closing Notepad...')
        os.system("taskkill /f /im notepad.exe")
    elif 'calculator' in software_name:
        speak('Closing Calculator...')
        os.system("taskkill /f /im calc.exe")
    else:
        speak(f"I couldn't find any open software named {software_name}")

# =========================================
# Additional New Features: Help, Exit, Extra Phrases
# =========================================
def show_help():
    """Lists available commands."""
    commands = [
        "time - Tell the current time.",
        "wikipedia - Search Wikipedia for a topic.",
        "youtube - Play a video on YouTube.",
        "google - Perform a Google search.",
        "weather - Get the weather for a specific city.",
        "joke - Tell a joke.",
        "notepad - Open Notepad.",
        "calculator - Open Calculator.",
        "ip address - Show your public IP address.",
        "generate sentence - Generate a sentence about a topic.",
        "chat - Talk with Isabella using the conversational model.",
        "set reminder - Set a reminder.",
        "shayari - Hear a random shayari with a link for more.",
        "open [software] - Open a software application (chrome, microsoft edge, etc.).",
        "close [software] - Close a software application.",
        "who is god - Answer a fun question.",
        "what is your name - Tell you my name.",
        "stop - Stop the program.",
        "help - Show this list of commands.",
        "exit - Exit the assistant."
    ]
    speak("Here are the commands you can use:")
    for cmd in commands:
        speak(cmd)

def exit_isabella():
    """Exits the Isabella assistant."""
    speak("Goodbye " + USERNAME + ". Have a great day!")
    logging.info("Exiting Isabella.")
    sys.exit()

# =========================================
# Main Program Loop
# =========================================
if __name__ == '__main__':
    # First, wait for the wake word (still 'jarvis')
    listen_for_wake_word()
    greet_user()
    
    while True:
        command = listen_command()
        if command == "":
            continue

        # New "stop" and extra phrase commands
        if 'stop' in command:
            speak('Stopping the program. Goodbye!')
            sys.exit()
        elif 'who is god' in command:
            speak('Ajitheyyy Kadavuleyy')
        elif 'what is your name' in command:
            speak('My name is Isabella, Your Artificial Intelligence')
        # Original commands
        elif 'time' in command:
            tell_time()
        elif 'wikipedia' in command:
            speak("What should I search on Wikipedia?")
            query = listen_command()
            search_wikipedia(query)
        elif 'youtube' in command:
            speak("What do you want to play on YouTube?")
            query = listen_command()
            play_on_youtube(query)
        elif 'google' in command:
            speak("What should I search on Google?")
            query = listen_command()
            google_search(query)
        elif 'weather' in command:
            speak("Which city are you interested in?")
            city = listen_command()
            get_weather(city)
        elif 'joke' in command:
            tell_joke()
        elif 'notepad' in command:
            open_notepad()
        elif 'calculator' in command:
            open_calculator()
        elif 'ip address' in command:
            get_ip_address()
        elif 'generate sentence' in command:
            speak("What topic would you like me to generate a sentence about?")
            topic = listen_command()
            generate_sentence(topic)
        elif 'set reminder' in command:
            def set_reminder():
                speak("What is your reminder?")
                reminder_text = listen_command()
                speak("In how many seconds should I remind you?")
                try:
                    seconds = int(listen_command())
                except ValueError:
                    speak("I did not understand the number. Please try again later.")
                    return

                def reminder():
                    time.sleep(seconds)
                    speak(f"Reminder: {reminder_text}")
                    logging.info(f"Reminder triggered: {reminder_text}")

                threading.Thread(target=reminder).start()
                speak("Okay, I will remind you in " + str(seconds) + " seconds.")
            set_reminder()
        elif 'chat' in command or 'talk to isabella' in command:
            chat_with_isabella()
        elif 'shayari' in command:
            tell_shayari()
        # New generic open/close commands
        elif 'open' in command:
            open_software(command)
        elif 'close' in command:
            close_software(command)
        elif 'help' in command:
            show_help()
        elif 'exit' in command:
            exit_isabella()
        else:
            # For any unmatched command, use the local conversational model.
            response = chat_with_local_model(command)
            print("Isabella:", response)
            speak(response)
