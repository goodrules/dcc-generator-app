import streamlit as st
from google import genai # new unified SDK
from google.genai import types
import tempfile
import os
import mimetypes
from typing import Iterator
import time
import random
import io

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

# Built-in examples list
DEFAULT_EXAMPLES = [
    "New achievement! You've killed an armed mob with your bare fucking hands! Holy crap, dude. That's kinda fucked up. Reward: You've received a Bronze Weapon Box!",
    "New Achievement! You're the reason why daddy drinks! You have, for an unspecified reason, raised the ire of the System AI. You have corrected the issue, and everything is back to normal. The acceleration action has been suspended. This time. Good boy. Reward: You've received a Gold Makeup Sex is the Best Sex box. You're not going to break me. Fuck you all. I will break you.",
    "New achievement! PETA Enthusiast! You somehow managed to remove the hostility of an aggravated, non-sapient enemy. That enemy then fought against other enemies to your benefit. The ghost of Steve Irwin smiles down upon you.Reward: I SAID THE GHOST OF STEVE IRWIN SMILES DOWN UPON YOU.",
    "New achievement! Battlefield Construction! You built a structure and deployed it in battle. And your mother thought you were wasting your life away while you spent all those hours eating Doritos and playing Minecraft. If only she could see you now. Too bad she's probably dead. Reward: You've received a Silver Mechanic's Box!",
    "New achievement! War Criminal. You have killed more than 20 non-combatants in a single attack! Question: What's the only thing standing between an innocent child and a happy, fulfilling life? Answer: You. The answer is you. Reward: You've received a Gold Asshole's Box!",
    "New achievement! Bully and a Thief! You've stolen property from a fellow crawler who is a lower level than you. What's next, tough guy? Kicking puppies? Reward: You've received a Bronze Asshole's Box.",
    "New achievement! Fall into an obvious trap. Reward: Well, if there's a heaven, and if you haven't been too much of an asshole, maybe they'll let you in. Because you about to meet your maker.",
    "New Achievement! Mass Casualty Event. Okay. Calm your man-tiddies. Did your mother not love you? Is your god promising you unlimited handjobs in heaven or something? You planted and then detonated an improvised explosive device within an urban population center that resulted in more than 250 non-mob casualties. You've done this a few times now, but this was a big one. And on purpose. You really know how to paint the town red. Reward: You've received a Platinum Asshole's Box. \"Damnit,\" I growled. That meant we'd killed more than 200 NPCs.",
    "New Achievement! Sex Pervert! A nipple ring? Really? The next thing you know, you'll be waxing your perineum and attending those parties where you have to put your keys in a bowl. You'll have to grow out your sideburns, buy a Trans Am, and you'll no longer be able to make eye contact with your child's orthodontist. Reward: Whores don't get rewards.",
    "New Achievement! Total, Utter Failure. You failed a quest less than five minutes after you received it. Now that's talent. Reward: Ha.",
    "New achievement! Mentally Unstable Clothing Hoarder! You have over 500 of the exact same, stackable clothing item in your inventory. What the hell is wrong with you? You planning on opening a thrift store? You might want to see a shrink. One that your group doesn't immediately kill. Reward: We don't reward this sort of behavior. It's weird."
]

def load_custom_examples(uploaded_file):
    """Load examples from uploaded file."""
    if uploaded_file is not None:
        content = uploaded_file.read().decode('utf-8')
        examples = [line.strip() for line in content.split('\n') if line.strip()]
        return examples
    return []

def get_examples_list():
    """Get the current examples list (custom or default)."""
    if 'custom_examples' in st.session_state and st.session_state.custom_examples:
        return st.session_state.custom_examples
    return DEFAULT_EXAMPLES

def get_random_examples(num_examples=6):
    """Get random examples from the current examples list."""
    examples = get_examples_list()
    return random.sample(examples, min(num_examples, len(examples)))

def stream_generate(
    query: str, 
    model="gemini-2.5-flash-preview-05-20"
) -> tuple[Iterator[str], str]:
    """Stream chat responses from Gemini and return the prompt used."""
    
    # Get 6 random examples
    random_examples = get_random_examples(6)
    examples_text = "\n    ".join(random_examples)
    
    pre_prompt = f"""You are the sarcastic, judgmental System AI from Dungeon Crawler Carl. Generate a hilariously inappropriate achievement for the following topic. 

CRITICAL STYLE REQUIREMENTS:
- Adopt a sarcastic, sometimes angry/frustrated AI voice that judges the player
- Break the fourth wall: reference gaming mechanics, real world, the player's actual life
- Use dark humor that inappropriately connects game actions to real-world moral issues
- Address the player as "you" - NEVER call them "Carl"
- Make creative personal attacks on the player's character, choices, family, or mental state
- Reference pop culture, social commentary, and real-world comparisons inappropriately
- Vary wildly in length and emotional tone (angry rants, short dismissals, disappointed lectures)
- Use profanity, adult references, and mature themes naturally within the dark humor
- Subvert typical gaming achievement expectations with meta-commentary

REWARD REQUIREMENTS:
- Create themed "Box" rewards that match the achievement tone
- Examples: "Bronze Asshole's Box", "Gold Makeup Sex is the Best Sex box", "Platinum War Criminal's Box"
- Sometimes deny rewards entirely for truly awful behavior
- Be creative and thematic with reward names

Topic: {query}

ACHIEVEMENT EXAMPLES:
{examples_text}

Generate exactly 1 achievement that captures this chaotic, inappropriate, hilarious tone.

FORMAT:
**New achievement!** <creative_title>! 

<achievement_description>

**Reward:** <creative_reward_or_denial>"""
    
    prompt = pre_prompt
    
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )
    ]
    
    # Get streaming response
    response = google_genai_client.models.generate_content_stream(model=model, contents=contents, config=generate_content_config)
    
    def generate_stream():
        for chunk in response:
            if hasattr(chunk, "text") and chunk.text and chunk.text.strip():
                yield chunk.text
    
    return generate_stream(), prompt

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
            #print(response.text)
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
        ["gemini-2.5-flash-preview-05-20", "gemini-2.5-pro-preview-05-06"],
        index=0
    )
    image_model_name = st.selectbox(
        "Select Imagen Model",
        ["imagen-4.0-generate-preview-05-20", "imagen-4.0-ultra-generate-exp-05-20"],
        index=0
    )
    
    st.markdown("---")
    st.subheader("Custom Examples")
    
    # File uploader for custom examples
    uploaded_file = st.file_uploader(
        "Upload custom examples file",
        type=['txt'],
        help="Upload a .txt file with one example per line"
    )
    
    if uploaded_file is not None:
        custom_examples = load_custom_examples(uploaded_file)
        if custom_examples:
            st.session_state.custom_examples = custom_examples
            st.success(f"Loaded {len(custom_examples)} custom examples!")
        else:
            st.warning("No valid examples found in uploaded file.")
    
    # Show current examples count
    current_examples = get_examples_list()
    example_type = "custom" if 'custom_examples' in st.session_state and st.session_state.custom_examples else "default"
    st.info(f"Using {len(current_examples)} {example_type} examples")
    
    # Reset to default examples
    if st.button("Reset to Default Examples"):
        if 'custom_examples' in st.session_state:
            del st.session_state.custom_examples
        st.success("Reset to default examples!")
        st.rerun()
    
    st.markdown("---")
    
    if st.button("Clear"):
        #st.session_state.chat_history = []
        st.session_state["user_input"] = ""
        st.rerun()


MODEL = model_name
IMAGE_MODEL = image_model_name

# Chat input
user_input = st.text_input('What are we "celebrating"?', key="input1")

if st.button("Generate"):
    # Initialize response variables
    full_response = ""
    
    # Create dedicated container for achievement text
    achievement_container = st.container()
    
    with achievement_container:
        st.subheader("🏆 New Achievement Generated!")
        message_placeholder = st.empty()
        
        # Get streaming response and prompt
        stream_generator, achievement_prompt = stream_generate(query=user_input, model=MODEL)
                
        for chunk in stream_generator:
            if chunk:  # Only concatenate if chunk is not None
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.05)
        
        # Update final response without cursor
        message_placeholder.markdown(full_response)
    
    # Only proceed with image generation if we have achievement text
    if full_response.strip():
        st.markdown("---")
        
        image_setup_prompt = f"""Create a visual representation of the REWARD from this Dungeon Crawler Carl achievement. Focus primarily on the reward itself, using the achievement's dark humor, tone, and moral judgment to inform the visual style.

VISUAL REQUIREMENTS:
- Primary subject: The specific reward box/item mentioned in the achievement
- Style: Gaming reward aesthetic with inappropriate/darkly humorous elements  
- Tone: Maintain the achievement's sarcastic judgment and absurdity in visual form
- Irony: Beautiful, appealing reward presentation of morally questionable contents
- DCC Aesthetic: Post-apocalyptic gaming style with corporate cheerfulness applied to dark themes
- Thematic consistency: Visual elements should match the achievement's context and moral theme

Achievement: {full_response}

Generate a concise, specific image prompt focusing on the reward that captures its visual irony and DCC absurdity. Do not include children. Output only the image generation prompt:"""

        with st.status("Generating reward..."):
            st.write("Validating if crawler achieved the reward.")
            image_prompt = retry_gemini(image_setup_prompt, MODEL, generate_content_config)
            st.write("Digging through the digital junk drawer of slightly used rewards... Found it!")
            response_image = retry_imagen(image_prompt, IMAGE_MODEL)
            st.write("Slapping a new label on it.")
            st.image(response_image.generated_images[0].image.image_bytes, caption=["Generated by Imagen 3"])
            st.write("Reward deployed.")
    
    # Add debug info to sidebar
    with st.sidebar:
        with st.expander("🔧 Debug Information", expanded=False):
            st.subheader("Achievement Generation Prompt")
            st.code(achievement_prompt, language="text")
            
            st.subheader("Image Setup Prompt")
            st.code(image_setup_prompt, language="text")
            
            st.subheader("Generated Image Prompt")
            st.code(image_prompt, language="text")
            
            st.subheader("Models Used")
            st.write(f"**Text Model:** {MODEL}")
            st.write(f"**Image Model:** {IMAGE_MODEL}")

 #   with st.spinner("Generating reward..."):
        
        
        
        