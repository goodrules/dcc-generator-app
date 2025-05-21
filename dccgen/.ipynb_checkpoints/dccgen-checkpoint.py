import streamlit as st
from google import genai # new unified SDK
from google.genai import types
import tempfile
import os
import mimetypes
from typing import Iterator
import time

#aistudio_key = os.getenv("AISTUDIO_API_KEY")  # google ai studio

PROJECT_ID = os.environ.get("PROJECT_ID")
LOCATION = "us-central1"

google_genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
#google_genai_client = genai.Client(api_key=aistudio_key) # instantiate client

generate_content_config = types.GenerateContentConfig(
        temperature = 1.5,
        top_p = 0.95,
        max_output_tokens = 8192,
        response_modalities = ["TEXT"],
        safety_settings = [types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH",
            threshold="OFF"
        ),types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="OFF"
        ),types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold="OFF"
        ),types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT",
            threshold="OFF"
        )]
    )

def stream_generate(
    query: str, 
    model="gemini-2.5-flash-preview-04-17"
) -> Iterator[str]:
    """Stream chat responses from Gemini."""
    
    pre_prompt = f"""Write a funny achievement description for the following topic in the Dungeon Crawler Carl style.  Achievements should vary in length, complexity, silliness, and vulgarness.  Only generate 1 achievement.  The reward should ALWAYS be a type of Box.
    
    Topic: {query}

    Some examples:
    “New achievement! You’ve killed an armed mob with your bare fucking hands! Holy crap, dude. That’s kinda fucked up. Reward: You’ve received a Bronze Weapon Box!”
    “New Achievement! You’re the reason why daddy drinks! You have, for an unspecified reason, raised the ire of the System AI. You have corrected the issue, and everything is back to normal. The acceleration action has been suspended. This time. Good boy. Reward: You’ve received a Gold Makeup Sex is the Best Sex box. You’re not going to break me. Fuck you all. I will break you.”
    "New achievement! PETA Enthusiast! You somehow managed to remove the hostility of an aggravated, non-sapient enemy. That enemy then fought against other enemies to your benefit. The ghost of Steve Irwin smiles down upon you.Reward: I SAID THE GHOST OF STEVE IRWIN SMILES DOWN UPON YOU."
    "New achievement! Battlefield Construction! You built a structure and deployed it in battle. And your mother thought you were wasting your life away while you spent all those hours eating Doritos and playing Minecraft. If only she could see you now. Too bad she’s probably dead. Reward: You’ve received a Silver Mechanic's Box!"
    "New achievement! War Criminal. You have killed more than 20 non-combatants in a single attack! Question: What’s the only thing standing between an innocent child and a happy, fulfilling life? Answer: You. The answer is you. Reward: You’ve received a Gold Asshole's Box!"
    "New achievement! Bully and a Thief! You’ve stolen property from a fellow crawler who is a lower level than you. What’s next, tough guy? Kicking puppies? Reward: You’ve received a Bronze Asshole's Box."
    
    Format your response with the following structure:
    **New achievement!** <topic>! \n\n
    <achievement_description> \n\n
    **Reward:** <reward>"
    """
    
    prompt = f"{pre_prompt}\n\nAchievement Description:"
    
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )
    ]
    
    # Get streaming response
    response = google_genai_client.models.generate_content_stream(model=model, contents=contents, config=generate_content_config)
    
    for chunk in response:
        if hasattr(chunk, "text"):
            yield chunk.text

def retry_gemini(prompt, model_name, generation_config, retries = 3):
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )
    ]
    for retry in range(retries):
        try:
            response = google_genai_client.models.generate_content(
                model=model_name, 
                contents=contents,
                config=generation_config
            )
            print(response.text)
            return response.text
        except Exception as e:
            print(f"Attempt {retry + 1} failed: {e}")
            time.sleep(0.5 * 2 ** retry)

def retry_imagen(prompt, model_name, retries = 3):
    for retry in range(retries):
        try:
            response_image = google_genai_client.models.generate_images(
                model=model_name,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    include_rai_reason=True,
                    person_generation="ALLOW_ADULT"
                )
            )
            return response_image
        except Exception as e:
            print(f"Attempt {retry + 1} failed: {e}")
            time.sleep(0.5 * 2 ** retry)

st.title("DCC Achievement Generator")

# Add clear history button in the sidebar
with st.sidebar:
    model_name = st.selectbox(
        "Select Gemini Model",
        ["gemini-2.5-flash-preview-04-17", "gemini-2.5-pro-preview-03-25"],
        index=0
    )
    image_model_name = st.selectbox(
        "Select Imagen Model",
        ["imagen-3.0-generate-002", "imagen-3.0-fast-generate-001"],
        index=0
    )
    if st.button("Clear"):
        #st.session_state.chat_history = []
        st.session_state["user_input"] = ""
        st.rerun()


MODEL = model_name
IMAGE_MODEL = image_model_name

full_response = ""
image_list = []

# Chat input
user_input = st.text_input('What are we "celebrating"?', key="input1")

if st.button("Generate"):
    # Get streaming response
    message_placeholder = st.empty()
            
    for chunk in stream_generate(query=user_input, model=MODEL):
        full_response += chunk
        message_placeholder.markdown(full_response + "▌")
        time.sleep(0.05)
    
    # Update final response
    message_placeholder.markdown(full_response)
            
    image_setup_prompt = f"""Extract key phrases and words from the following achievement, and create a prompt to generate an image that represents what was extracted. The focus should be on the reward.  The image generation prompt should be silly and ridiculous. Do not include any children in the image prompt. The output should only include the image generation prompt.

    Achievement test: 
    {full_response}

    Image generation prompt:
    """

    with st.status("Generating reward..."):
        st.write("Validating if crawler achieved the reward.")
        image_prompt = retry_gemini(image_setup_prompt, MODEL, generate_content_config)
        st.write("Digging through the digital junk drawer of slightly used rewards... Found it!")
        response_image = retry_imagen(image_prompt, IMAGE_MODEL)
        st.write("Slapping a new label on it.")
        st.image(response_image.generated_images[0].image.image_bytes, caption=["Generated by Imagen 3"])
        st.write("Reward deployed.")

 #   with st.spinner("Generating reward..."):
        
        
        
        