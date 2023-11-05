from flask import Flask, request, jsonify, session
import openai
import os
import re
from flask import render_template

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key for session management

openai.api_key = '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'

from flask import render_template

@app.route('/')
def index():
    session.pop('chat_log', None)  # Reset the chat session for the user
    return render_template('index.html')


@app.route('/start_adventure', methods=['POST'])
def start_adventure():
    data = request.json
    name = data.get('name')
    appearance = data.get('appearance')
    genre = data.get('genre')

    # The first message to the model setting up the context
    system_message = {
        "role": "system",
    "content": "You are a helpful AI creating a story in the genre of {genre}. Please format your response with the chapter name, then newline 'Story:' followed by the story text. Then 'Choices:' followed by the list of choices. End with 'End.'"
    }

    # The user message with the initial story setup
    user_message = {
        "role": "user",
        "content": f"Start a story about a character named {name} who looks like {appearance} in the genre {genre}. Please create a story in the specified genre. Please format your response with the chapter name, then 'Story:' followed by the story text. Then 'Choices:' followed by the list of choices. End with 'End."
    }

    messages = [system_message, user_message]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )

    session['chat_log'] = response['choices'][0]['message']['content']
    return jsonify(parse_story(session['chat_log']))

@app.route('/continue_adventure', methods=['POST'])
def continue_adventure():
    data = request.json
    user_input = data.get('choice')

    # Retrieve the full chat log from the session
    chat_log = session.get('chat_log')

    # Construct a new user message with the user's input
    user_message = {
        "role": "user",
        "content": user_input
    }

    # Send the full chat log along with the new user message to GPT
    response = openai.ChatCompletion.create(
        model="gpt-4",  # make sure to use "gpt-4" if that's what you've been using
        messages=[{"role": "system", "content": "You are a helpful AI creating a story in the genre of {genre}. Please format your response with the chapter name, then newline 'Story:' followed by the story text. Then 'Choices:' followed by the list of choices. End with 'End.'"}, {"role": "user", "content": chat_log}, user_message]
    )

    # Append the new content to the chat log in the session
    session['chat_log'] += "\n" + response['choices'][0]['message']['content']

    # Instead of sending the entire chat log to the frontend, send only the new content
    # We parse this new content to extract the story, choices etc.
    return jsonify(parse_story(response['choices'][0]['message']['content']))

def parse_story(text):
    # Regex pattern to extract the chapter title, assuming the format "Chapter X: Title"
    chapter_match = re.search(r'(Chapter \d+): (.+)', text)
    chapter_number_title = chapter_match.group(0) if chapter_match else "Chapter Unknown"

    # Assuming the story part is always before "Choices:"
    parts = text.split('Choices:')
    story_part = parts[0].strip() if len(parts) > 1 else text
    
    # If we have a chapter match, remove it from the story part
    if chapter_match:
        story_part = story_part.replace(chapter_match.group(0), '').strip()

    # Extract choices, general pattern assuming each choice starts with a digit followed by a period
    choices = re.findall(r'\d+\.\s(.+?)(?=\d+\.|$)', text, re.DOTALL)

    # Clean the choices by removing any leading/trailing whitespace and newlines
    choices = [choice.strip().replace('\n', ' ') for choice in choices]
    
    dict = {
        'chapter': chapter_number_title,
        'story': story_part,
        'choices': choices
    }
    print(dict)

    return {
        'chapter': chapter_number_title,
        'story': story_part,
        'choices': choices
    }



if __name__ == '__main__':
    app.run(debug=True)