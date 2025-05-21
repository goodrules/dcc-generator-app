# app.py
import os
from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from google import genai
from google.genai import types
import time
from typing import Iterator

# Initialize Flask app
flask_app = Flask(__name__)

# Initialize Slack app with your credentials
slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Create a SlackRequestHandler using your Slack app
handler = SlackRequestHandler(slack_app)

# Set up Google Generative AI client
PROJECT_ID = os.environ.get("PROJECT_ID")
LOCATION = "us-central1"

google_genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# Configure generation settings
generate_content_config = types.GenerateContentConfig(
    temperature=1,
    top_p=0.95,
    max_output_tokens=8192,
    response_modalities=["TEXT"],
    safety_settings=[
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
    ]
)

def stream_generate(query: str, model="gemini-2.0-flash-exp") -> Iterator[str]:
    """Stream chat responses from Gemini."""
    
    pre_prompt = f"""Write a funny achievement description for the following topic in the Dungeon Crawler Carl style.  Achievements should vary in length, complexity, silliness, and vulgarness.  Only generate 1 achievement.
    
    Topic: {query}

    Some examples:
    "New achievement! You've killed an armed mob with your bare fucking hands! Holy crap, dude. That's kinda fucked up. Reward: You've received a Bronze Weapon Box!"
    "New Achievement! You're the reason why daddy drinks! You have, for an unspecified reason, raised the ire of the System AI. You have corrected the issue, and everything is back to normal. The acceleration action has been suspended. This time. Good boy. Reward: You've received a Gold Makeup Sex is the Best Sex box. You're not going to break me. Fuck you all. I will break you."
    "New achievement! PETA Enthusiast! You somehow managed to remove the hostility of an aggravated, non-sapient enemy. That enemy then fought against other enemies to your benefit. The ghost of Steve Irwin smiles down upon you.Reward: I SAID THE GHOST OF STEVE IRWIN SMILES DOWN UPON YOU."
    "New achievement! Battlefield Construction! You built a structure and deployed it in battle. And your mother thought you were wasting your life away while you spent all those hours eating Doritos and playing Minecraft. If only she could see you now. Too bad she's probably dead. Reward: You've received a Silver Mechanic's Box!"
    "New achievement! War Criminal. You have killed more than 20 non-combatants in a single attack! Question: What's the only thing standing between an innocent child and a happy, fulfilling life? Answer: You. The answer is you. Reward: You've received a Gold Asshole's Box!"
    "New achievement! Bully and a Thief! You've stolen property from a fellow crawler who is a lower level than you. What's next, tough guy? Kicking puppies? Reward: You've received a Bronze Asshole's Box."
    
    Format your response with the following structure:
    **New achievement!** <topic>! \n\n
    <achievement_description> \n\n
    **Reward:** <reward>"
    """
    
    prompt = f"{pre_prompt}\n\nAchievement Description:"
    
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(prompt)]
        )
    ]
    
    # Get streaming response
    response = google_genai_client.models.generate_content_stream(
        model=model, 
        contents=contents, 
        config=generate_content_config
    )
    
    for chunk in response:
        if hasattr(chunk, "text"):
            yield chunk.text

def retry_gemini(prompt, model_name, generation_config, retries=3):
    """Retry function for Gemini API calls"""
    for retry in range(retries):
        try:
            response = google_genai_client.models.generate_content(
                model=model_name, 
                contents=prompt,
                config=generation_config
            )
            return response.text
        except Exception as e:
            print(f"Attempt {retry + 1} failed: {e}")
            if retry < retries - 1:
                time.sleep(0.5 * 2 ** retry)
            else:
                raise

def retry_imagen(prompt, model_name, retries=3):
    """Retry function for Imagen API calls"""
    for retry in range(retries):
        try:
            response_image = google_genai_client.models.generate_image(
                model=model_name,
                prompt=prompt,
                config=types.GenerateImageConfig(
                    number_of_images=1,
                    include_rai_reason=True,
                )
            )
            return response_image
        except Exception as e:
            print(f"Attempt {retry + 1} failed: {e}")
            if retry < retries - 1:
                time.sleep(0.5 * 2 ** retry)
            else:
                raise

# Command handler for /dcc-achievement command
@slack_app.command("/dcc-achievement")
def handle_dcc_achievement(ack, respond, command):
    # Acknowledge command request
    ack()
    
    topic = command["text"]
    if not topic:
        respond("Please provide a topic for the achievement.")
        return
    
    # Initial response
    respond({
        "response_type": "in_channel",
        "text": f"Generating DCC achievement for: *{topic}*..."
    })
    
    try:
        # Generate the achievement text
        full_response = ""
        model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-exp")
        
        # Since we can't stream directly to Slack, collect the full response
        for chunk in stream_generate(query=topic, model=model):
            full_response += chunk
        
        # Send the achievement to the channel
        respond({
            "response_type": "in_channel", 
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": full_response
                    }
                }
            ]
        })
        
        # Generate image for the achievement (optional based on GENERATE_IMAGES env var)
        if os.environ.get("GENERATE_IMAGES", "false").lower() == "true":
            try:
                image_setup_prompt = f"""Can you extract key phrases and words from the following achievement, and create a prompt to generate an image that represents what was extracted? The focus should be on the reward. The image generation prompt should be silly and ridiculous but not include any people. The output should only include the image generation prompt.

                Achievement text: 
                {full_response}

                Image generation prompt:
                """

                respond({
                    "response_type": "in_channel",
                    "text": "Generating reward image..."
                })
                
                # Generate image prompt
                image_model = os.environ.get("IMAGEN_MODEL", "imagen-3.0-fast-generate-001")
                image_prompt = retry_gemini(image_setup_prompt, "gemini-1.5-flash", generate_content_config)
                
                # Generate image
                response_image = retry_imagen(image_prompt, image_model)
                
                # Currently, we'd need to upload this image somewhere to share it in Slack
                # For this example, we'll just send the prompt that would generate the image
                respond({
                    "response_type": "in_channel",
                    "text": f"Image prompt: {image_prompt}\n\n(Image generation requires additional setup for storage)"
                })
            except Exception as e:
                respond({
                    "response_type": "in_channel",
                    "text": f"Error generating image: {str(e)}"
                })
    except Exception as e:
        respond({
            "response_type": "in_channel",
            "text": f"Error generating achievement: {str(e)}"
        })

# Example event handler for messages
@slack_app.event("message")
def handle_message_events(body, say):
    # Only respond to messages in DMs with the bot
    if "channel_type" in body["event"] and body["event"]["channel_type"] == "im":
        user = body["event"]["user"]
        text = body["event"]["text"]
        
        # If message seems to be asking for an achievement
        if "achievement" in text.lower():
            # Extract topic after "achievement" or "achievement for"
            words = text.lower().split()
            if "for" in words and words.index("for") > words.index("achievement"):
                idx = words.index("for")
                topic = " ".join(words[idx+1:])
                
                if topic:
                    say(f"Generating a DCC achievement for: *{topic}*...")
                    
                    try:
                        # Generate achievement
                        full_response = ""
                        model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-exp")
                        
                        for chunk in stream_generate(query=topic, model=model):
                            full_response += chunk
                        
                        say(full_response)
                    except Exception as e:
                        say(f"Error generating achievement: {str(e)}")
        else:
            # Simple help message
            say("Hi there! You can ask me to generate a Dungeon Crawler Carl style achievement. Just say something like 'achievement for completing my first project'")

# Flask route for handling Slack events and interactions
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

# Health check endpoint
@flask_app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})

# Run the Flask app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)
