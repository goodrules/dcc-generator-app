## Dungeon Crawler Carl Achievement Generator

A hilarious web application that generates satirical achievements in the style of the "Dungeon Crawler Carl" book series. Uses AI to create darkly humorous, inappropriate achievements with sarcastic commentary and generates visual rewards to match.

## Features

- **Authentic DCC Style**: Generates achievements with the signature sarcastic, judgmental System AI voice
- **Streaming Text Generation**: Watch achievements generate in real-time with dramatic effect
- **Visual Rewards**: AI-generated images of reward boxes that match the achievement's dark humor
- **Custom Examples**: Upload your own example files to customize the generation style
- **Multi-Model Support**: Choose between different Gemini and Imagen models
- **Secure Authentication**: Simple login system to control access

## Getting Started

### Prerequisites
- Google Cloud Platform account with Vertex AI access
- Streamlit
- Python 3.8+
- Required environment variables (see setup below)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/goodrules/dcc-generator-app
cd dcc-generator-app
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
```bash
# For Google Cloud Vertex AI (recommended)
export PROJECT_ID="your-gcp-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"

# Alternative: Google AI Studio (if not using Vertex AI)
# export AISTUDIO_API_KEY="your_ai_studio_api_key"
```

### Running the App Locally

Launch the Streamlit app:
```bash
streamlit run app.py
```

### Authentication

Default login credentials:
- **Username**: `thunderdome`
- **Password**: `bookclub`

*Note: Change these credentials in `app.py` for production use.*

### Deploy the App to Cloud Run

Build and deploy container:
```bash
gcloud run deploy dccbot --source . --region="us-central1" --allow-unauthenticated
```

## Usage

1. **Login** using the provided credentials
2. **Enter a topic** - anything you want a DCC achievement for (e.g., "eating pizza", "procrastinating", "bad coding")
3. **Watch the achievement generate** with streaming text
4. **View your reward** - an AI-generated image of your appropriately inappropriate reward box
5. **Upload custom examples** (optional) - provide your own .txt file with one achievement per line

## Technical Details

- **Frontend**: Streamlit with custom navigation and authentication
- **AI Models**: Google Gemini 2.5 for text generation, Imagen 4.0 for images  
- **Architecture**: Modular design with separate achievement and image generation
- **Deployment**: Containerized for Google Cloud Run

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Matt Dinniman** for creating the incredible Dungeon Crawler Carl universe
- **Google Cloud Platform** for providing the Gemini and Imagen APIs
- **Streamlit team** for their amazing framework
- **Contributors and maintainers**

## Disclaimer

This is a fan-made demonstration project and is not officially associated with Matt Dinniman, Dungeon Crawler Carl, or Google Cloud Platform. Please ensure you comply with Google Cloud's terms of service and API usage guidelines when using these models.

**Content Warning**: This application generates adult humor with profanity, dark themes, and inappropriate content in the style of Dungeon Crawler Carl.


Made by [GoodRules](https://github.com/goodrules)