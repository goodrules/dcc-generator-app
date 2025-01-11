
import streamlit as st
from google import genai # new unified SDK
from google.genai import types
import tempfile
import os
import mimetypes
from typing import Iterator
import time

#aistudio_key = os.getenv("AISTUDIO_API_KEY")  # google ai studio

# Use this if using GCP - Vertex
from google.oauth2 import service_account
import os

PROJECT_ID = os.environ.get("PROJECT_ID")
LOCATION = "us-central1"

google_genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
#google_genai_client = genai.Client(api_key=aistudio_key) # instantiate client

generate_content_config = types.GenerateContentConfig(
        temperature = 1,
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
    model="gemini-2.0-flash-exp"
) -> Iterator[str]:
    """Stream chat responses from Gemini."""
    
    pre_prompt = f"""Can you write a funny achievement description for the following topic in the Dungeon Crawler Carl style?
    
    Topic: {query}

    Some examples:
    “New achievement! You’ve killed an armed mob with your bare fucking hands! Holy crap, dude. That’s kinda fucked up. Reward: You’ve received a Bronze Weapon Box!”
    “New Achievement! You’re the reason why daddy drinks! You have, for an unspecified reason, raised the ire of the System AI. You have corrected the issue, and everything is back to normal. The acceleration action has been suspended. This time. Good boy. Reward: You’ve received a Gold Makeup Sex is the Best Sex box. You’re not going to break me. Fuck you all. I will break you.”
    "New achievement! PETA Enthusiast!You somehow managed to remove the hostility of an aggravated, non-sapient enemy. That enemy then fought against other enemies to your benefit. The ghost of Steve Irwin smiles down upon you.Reward: I SAID THE GHOST OF STEVE IRWIN SMILES DOWN UPON YOU."
    
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
    response = google_genai_client.models.generate_content_stream(model=model, contents=contents, config=generate_content_config)
    
    for chunk in response:
        if hasattr(chunk, "text"):
            yield chunk.text

def main():
    st.title("DCC Achievement Generator")

    # Add clear history button in the sidebar
    with st.sidebar:
        model_name = st.selectbox(
            "Select Gemini Model",
            ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
            index=0
        )
        image_model_name = st.selectbox(
            "Select Imagen Model",
            ["imagen-3.0-generate-001"],
            index=0
        )
        if st.button("Clear"):
            #st.session_state.chat_history = []
            st.session_state["input1"] = ""
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
        
    #if st.button("Generate Image"):
        
        image_setup_prompt = f"""Can you extract key phrases and words from the following achievement, and create a prompt to generate an image that represents what was extracted?  The focus should be on the reward.  The image generation prompt should be silly and ridiculous but not include any people.  The output should only include the image generation prompt.

        Achievement test: 
        {full_response}

        Image generation prompt:
        """
        
        image_prompt = google_genai_client.models.generate_content(
            model=MODEL, 
            contents=image_setup_prompt,
            config = generate_content_config
        ).text
        
        response_image = google_genai_client.models.generate_image(
            model=IMAGE_MODEL,
            prompt=image_prompt,
            config=types.GenerateImageConfig(
                number_of_images=1,
                include_rai_reason=True,
            )
        )
            
        st.image(response_image.generated_images[0].image.image_bytes, caption=["Generated by Imagen 3"])

        
if __name__ == "__main__":
    main()
