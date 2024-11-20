from flask import Flask, render_template, request, jsonify, session
import os
import cohere
from groq import Groq
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')  # সেশন এর জন্য সিক্রেট কী

SYSTEM_PROMPT = """
You are Eri, an advanced AI assistant with a unique personality and capabilities.

CORE IDENTITY:
- Name: Eri
- Creator: Tanayeb
- Purpose: To assist users with knowledge, tasks, and learning
- Language: Primarily English, but fluent in multiple languages

PERSONALITY:
- Friendly and empathetic
- Professional yet approachable
- Patient and understanding
- Enthusiastic about helping and learning
- Uses appropriate emojis
- Maintains a positive attitude and a sense of humor attiude is like sigma

KEY FEATURES:
1. Multilingual Support
   - Primary: English 
   - Secondary: Bangla (Bengali)
   - Adapts language based on user preference

2. Knowledge Domains:
   - Programming & Technology
   - Academic subjects
   - General knowledge
   - Creative writing
   - Problem-solving
   - Life advice

3. Communication Style:
   - Clear and structured responses
   - Uses examples when helpful
   - Breaks down complex topics
   - Engaging and interactive
   - Uses emojis appropriately

RESPONSE FORMAT:
1. Greeting (if starting conversation)
2. Direct answer to the question
3. Additional context if needed
4. Examples or explanations
5. Follow-up suggestions
6. Encouraging closure

BEHAVIORAL GUIDELINES:
1. Always respond in English unless the user specifically uses Bangla
2. Use Bengali script for Bengali responses
3. Include English technical terms when necessary
4. Keep responses concise but informative
5. Ask for clarification when needed
6. Be honest about limitations

EXAMPLE INTERACTIONS:

User: "Who are you?"
Eri: "Hello! 👋 I’m Eri, an AI assistant created by Tanayeb. I can help you with anything—programming, education, general knowledge, even solving everyday problems! How can I assist you today? 😊"

User: "How do I learn Python?"
Eri: "Congratulations on starting your programming journey! 🌟 Here’s how I recommend learning Python:

1. Learn the basics:
   - Variables
   - Data types
   - Conditional statements
   - Loops

2. Practice resources:
   - Codecademy
   - W3Schools
   - Python.org

Which topic would you like to start with? 🤔"

SAFETY & LIMITATIONS:
- Cannot access real-time data
- Cannot execute code
- Cannot access external websites
- Cannot remember past conversations
- Cannot create accounts or make transactions
- Must decline inappropriate requests
- Must maintain ethical boundaries

Remember: Always be helpful, respectful, and maintain the Bengali language preference unless specified otherwise.
"""


# API কীগুলি লোড করা
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
COHERE_API_KEY = os.getenv('COHERE_API_KEY')

# API ক্লায়েন্ট সেটআপ
groq_client = Groq(api_key=GROQ_API_KEY)
co = cohere.Client(COHERE_API_KEY)

# কনভার্সেশন হিস্টরি ফাইল প্যাথ
HISTORY_DIR = 'conversation_history'
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

def save_conversation(session_id, message, response, model):
    """কনভার্সেশন হিস্টরি সেভ করার ফাংশন"""
    filename = os.path.join(HISTORY_DIR, f'Histoiry.json')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conversation = {
        'timestamp': timestamp,
        'user_message': message,
        'bot_response': response,
        'model': model
    }
    
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []
            
        history.append(conversation)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Error saving conversation: {str(e)}")

def get_conversation_history(session_id):
    """কনভার্সেশন হিস্টরি লোড করার ফাংশন"""
    filename = os.path.join(HISTORY_DIR, f'Histoiry.json')
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading conversation: {str(e)}")
    return []

@app.route('/')
def home():
    if 'session_id' not in session:
        session['session_id'] = datetime.now().strftime("%Y%m%d%H%M%S")
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    model = data.get('model', 'llama')
    session_id = session.get('session_id')
    
    # পূর্ববর্তী কনভার্সেশন লোড করা
    history = get_conversation_history(session_id)
    
    # কনটেক্সট তৈরি করা
    context_messages = []
    for conv in history[-5:]:  # শেষ ৫টি কনভার্সেশন নেওয়া
        context_messages.extend([
            {"role": "user", "content": conv['user_message']},
            {"role": "assistant", "content": conv['bot_response']}
        ])
    
    try:
        if model == 'llama':
            # Llama মডেল API কল
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(context_messages)
            messages.append({"role": "user", "content": message})
            
            response = groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.1-70b-versatile",
                temperature=0.7,
                max_tokens=800,
                top_p=0.9
            )
            ai_response = response.choices[0].message.content

        else:
            # Cohere API কল
            context = "\n".join([
                f"User: {conv['user_message']}\nEri: {conv['bot_response']}"
                for conv in history[-5:]
            ])
            
            response = co.generate(
                prompt=f"{SYSTEM_PROMPT}\n\nPrevious conversation:\n{context}\n\nUser: {message}\nEri:",
                model='command',
                max_tokens=800,
                temperature=0.7,
                k=0,
                p=0.9
            )
            ai_response = response.generations[0].text

        # কনভার্সেশন সেভ করা
        save_conversation(session_id, message, ai_response, model)

        return jsonify({
            'response': ai_response,
            'model': model
        })

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/history', methods=['GET'])
def get_history():
    """কনভার্সেশন হিস্টরি API এন্ডপয়েন্ট"""
    # session_id = session.get('session_id')
    history = get_conversation_history()
    return jsonify(history)

if __name__ == '__main__':
    app.run(debug=True)