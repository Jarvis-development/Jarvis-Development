import requests
import time
import threading
import platform
import psutil
import webbrowser
import spacy

# Load the spaCy English model
nlp = spacy.load("en_core_web_sm")

# Google Cloud Function URL (replace with your actual URL)
CLOUD_FUNCTION_URL = '<https://us-west2-jaanis-ai-assitant.cloudfunctions.net/JAANIS_api>'

# Initialize variables to store user data
user_name = None
reminders = []

# Function to simulate an API call for weather information
def get_weather():
    return "It's currently sunny with a temperature of 75°F."

# Reminder function
def set_reminder(reminder, delay):
    time.sleep(delay)
    print(f"\nReminder: {reminder}")

# Function for system diagnostics
def get_system_info():
    uname = platform.uname()
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    system_info = (
        f"System: {uname.system} {uname.release} ({uname.version})\n"
        f"Machine: {uname.machine}\n"
        f"Processor: {uname.processor}\n"
        f"CPU Usage: {cpu_usage}%\n"
        f"Memory Usage: {memory.percent}% of {memory.total / (1024 ** 3):.2f} GB"
    )
    return system_info

# Function to interact with the Google Cloud Function API
def call_cloud_function(method, endpoint='', json=None):
    url = f"{CLOUD_FUNCTION_URL}{endpoint}"
    response = requests.request(method, url, json=json)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}

# Function to get a response based on user input with NLP
def get_response(user_input):
    global user_name
    
    # Use spaCy to process the user input
    doc = nlp(user_input.lower())
    
    # Check for name input
    if user_name is None and any(token.text == "my" and token.nbor().text == "name" for token in doc):
        user_name = user_input.split('my name is ')[-1].strip()
        return f"Nice to meet you, {user_name}!"
    
    if user_name is not None and any(token.text == "what" and token.nbor().text == "my" and token.nbor(2).text == "name" for token in doc):
        return f"Your name is {user_name}."

    if any(token.text == "set" and token.nbor().text == "a" and token.nbor(2).text == "reminder" for token in doc):
        parts = user_input.split('set a reminder ')[-1].strip()
        delay = 10  # Default to 10 seconds for simplicity
        reminders.append(parts)
        threading.Thread(target=set_reminder, args=(parts, delay)).start()
        return f"Reminder set: {parts}. I will remind you in {delay} seconds."
    
    if any(token.text == "add" and token.nbor().text == "task" for token in doc):
        task = user_input.split('add task ')[-1].strip()
        response = call_cloud_function('POST', '/tasks', json={'task': task})
        return response.get('message', "Couldn't add task.")
    
    if any(token.text == "list" and token.nbor().text == "tasks" for token in doc):
        response = call_cloud_function('GET', '/tasks')
        tasks = response if isinstance(response, list) else []
        return "Your tasks are:\n" + "\n".join(f"{i + 1}. {task['task']} (Completed: {task['completed']})" for i, task in enumerate(tasks)) if tasks else "You have no tasks."

    if any(token.text == "complete" and token.nbor().text == "task" for token in doc):
        task_num = int(user_input.split('complete task ')[-1].strip())
        response = call_cloud_function('PUT', f'/tasks/complete/{task_num}')
        return response.get('message', "Couldn't mark task as complete.")
    
    if any(token.text == "delete" and token.nbor().text == "task" for token in doc):
        task_num = int(user_input.split('delete task ')[-1].strip())
        response = call_cloud_function('DELETE', f'/tasks/delete/{task_num}')
        return response.get('message', "Couldn't delete task.")

    if any(token.text == "what" and token.nbor().text == "the" and token.nbor(2).text == "weather" for token in doc):
        return get_weather()
    
    if any(token.text == "system" and token.nbor().text == "diagnostics" for token in doc) or any(token.text == "system" and token.nbor().text == "info" for token in doc):
        return get_system_info()

    return "I'm sorry, I didn't understand that."

# Main function to run the chatbot
def run_chatbot():
    print("Welcome Sir, I am J.A.A.N.I.S., your personal assistant! Type 'exit' to stop.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            confirmation = input("Will that be all sir? (yes/no): ")
            if confirmation.lower() == 'yes':
                print("Chatbot: Goodbye!")
                break
        response = get_response(user_input)
        print(f"Chatbot: {response}")

if __name__ == "__main__":
    run_chatbot()