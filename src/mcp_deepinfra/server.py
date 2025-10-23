import asyncio
from mcp.server.fastmcp import FastMCP
import httpx
import os
from dotenv import load_dotenv
import json
from openai import AsyncOpenAI

load_dotenv()

DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")

if not DEEPINFRA_API_KEY:
    raise ValueError("DEEPINFRA_API_KEY not set")

app = FastMCP("deepinfra-ai-tools")

# Initialize OpenAI client with DeepInfra base URL
client = AsyncOpenAI(
    api_key=DEEPINFRA_API_KEY,
    base_url="https://api.deepinfra.com/v1/openai"
)

# Configuration
ENABLED_TOOLS_STR = os.getenv("ENABLED_TOOLS", "all")
if ENABLED_TOOLS_STR == "all":
    ENABLED_TOOLS = ["all"]
else:
    ENABLED_TOOLS = [tool.strip() for tool in ENABLED_TOOLS_STR.split(",")]

DEFAULT_MODELS = {
    "generate_image": os.getenv("MODEL_GENERATE_IMAGE", "Bria/Bria-3.2"),
    "text_generation": os.getenv("MODEL_TEXT_GENERATION", "meta-llama/Llama-2-7b-chat-hf"),
    "embeddings": os.getenv("MODEL_EMBEDDINGS", "sentence-transformers/all-MiniLM-L6-v2"),
    "speech_recognition": os.getenv("MODEL_SPEECH_RECOGNITION", "openai/whisper-large-v3"),
    "zero_shot_image_classification": os.getenv("MODEL_ZERO_SHOT_IMAGE_CLASSIFICATION", "openai/gpt-4o-mini"),
    "object_detection": os.getenv("MODEL_OBJECT_DETECTION", "openai/gpt-4o-mini"),
    "image_classification": os.getenv("MODEL_IMAGE_CLASSIFICATION", "openai/gpt-4o-mini"),
    "text_classification": os.getenv("MODEL_TEXT_CLASSIFICATION", "microsoft/DialoGPT-medium"),
    "token_classification": os.getenv("MODEL_TOKEN_CLASSIFICATION", "microsoft/DialoGPT-medium"),
    "fill_mask": os.getenv("MODEL_FILL_MASK", "microsoft/DialoGPT-medium"),
}



if "all" in ENABLED_TOOLS or "generate_image" in ENABLED_TOOLS:
    @app.tool()
    async def generate_image(prompt: str) -> str:
        """Generate an image from a text prompt using DeepInfra OpenAI-compatible API."""
        model = DEFAULT_MODELS["generate_image"]
        try:
            response = await client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
            )
            if response.data:
                return f"Generated image URL: {response.data[0].url}"
            else:
                return "No image generated"
        except Exception as e:
            return f"Error generating image: {type(e).__name__}: {str(e)}"

if "all" in ENABLED_TOOLS or "text_generation" in ENABLED_TOOLS:
    @app.tool()
    async def text_generation(prompt: str) -> str:
        """Generate text completion using DeepInfra OpenAI-compatible API."""
        model = DEFAULT_MODELS["text_generation"]
        try:
            response = await client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=256,
                temperature=0.7,
            )
            if response.choices:
                return response.choices[0].text
            else:
                return "No text generated"
        except Exception as e:
            return f"Error generating text: {type(e).__name__}: {str(e)}"

if "all" in ENABLED_TOOLS or "embeddings" in ENABLED_TOOLS:
    @app.tool()
    async def embeddings(inputs: list[str]) -> str:
        """Generate embeddings for a list of texts using DeepInfra OpenAI-compatible API."""
        model = DEFAULT_MODELS["embeddings"]
        try:
            response = await client.embeddings.create(
                model=model,
                input=inputs,
            )
            embeddings_list = [item.embedding for item in response.data]
            return str(embeddings_list)
        except Exception as e:
            return f"Error generating embeddings: {type(e).__name__}: {str(e)}"

if "all" in ENABLED_TOOLS or "speech_recognition" in ENABLED_TOOLS:
    @app.tool()
    async def speech_recognition(audio_url: str) -> str:
        """Transcribe audio to text using DeepInfra OpenAI-compatible API (Whisper)."""
        model = DEFAULT_MODELS["speech_recognition"]
        try:
            async with httpx.AsyncClient(timeout=120.0) as http_client:
                # Download the audio file
                audio_response = await http_client.get(audio_url)
                audio_response.raise_for_status()
                audio_content = audio_response.content
            
            # Use the OpenAI-compatible Whisper API
            response = await client.audio.transcriptions.create(
                model=model,
                file=("audio.mp3", audio_content),
            )
            return response.text
        except Exception as e:
            return f"Error transcribing audio: {type(e).__name__}: {str(e)}"

if "all" in ENABLED_TOOLS or "zero_shot_image_classification" in ENABLED_TOOLS:
    @app.tool()
    async def zero_shot_image_classification(image_url: str, candidate_labels: list[str]) -> str:
        """Classify an image with zero-shot labels using DeepInfra OpenAI-compatible API (CLIP)."""
        model = DEFAULT_MODELS["zero_shot_image_classification"]
        try:
            # Use chat/completions with vision capability to get classification
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Classify this image into one of these categories: {', '.join(candidate_labels)}. Return a JSON with 'label' and 'score' fields."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=200,
            )
            if response.choices:
                return response.choices[0].message.content
            else:
                return "Unable to classify image"
        except Exception as e:
            return f"Error classifying image: {type(e).__name__}: {str(e)}"

if "all" in ENABLED_TOOLS or "object_detection" in ENABLED_TOOLS:
    @app.tool()
    async def object_detection(image_url: str) -> str:
        """Detect objects in an image using DeepInfra OpenAI-compatible API with multimodal model."""
        model = DEFAULT_MODELS["object_detection"]
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image and detect all objects present. Provide a detailed list of objects you can see, their approximate locations if possible, and confidence scores. Format as JSON."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=500,
            )
            if response.choices:
                return response.choices[0].message.content
            else:
                return "No objects detected"
        except Exception as e:
            return f"Error detecting objects: {type(e).__name__}: {str(e)}"

if "all" in ENABLED_TOOLS or "image_classification" in ENABLED_TOOLS:
    @app.tool()
    async def image_classification(image_url: str) -> str:
        """Classify an image using DeepInfra OpenAI-compatible API with multimodal model."""
        model = DEFAULT_MODELS["image_classification"]
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image and classify what it shows. Provide the main categories and objects visible in the image with confidence scores. Format as JSON."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=500,
            )
            if response.choices:
                return response.choices[0].message.content
            else:
                return "Unable to classify image"
        except Exception as e:
            return f"Error classifying image: {type(e).__name__}: {str(e)}"

if "all" in ENABLED_TOOLS or "text_classification" in ENABLED_TOOLS:
    @app.tool()
    async def text_classification(text: str) -> str:
        """Classify text using DeepInfra OpenAI-compatible API."""
        model = DEFAULT_MODELS["text_classification"]
        prompt = f"""Analyze the following text and classify it. Determine the sentiment (positive, negative, neutral) and main category/topic. Provide your analysis in JSON format with 'sentiment' and 'category' fields.

Text: {text}

Response format: {{"sentiment": "positive/negative/neutral", "category": "topic"}}"""
        try:
            response = await client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=200,
                temperature=0.1,
            )
            if response.choices:
                return response.choices[0].text
            else:
                return "Unable to classify text"
        except Exception as e:
            return f"Error classifying text: {type(e).__name__}: {str(e)}"

if "all" in ENABLED_TOOLS or "token_classification" in ENABLED_TOOLS:
    @app.tool()
    async def token_classification(text: str) -> str:
        """Perform token classification (NER) using DeepInfra OpenAI-compatible API."""
        model = DEFAULT_MODELS["token_classification"]
        prompt = f"""Perform named entity recognition on the following text. Identify all named entities (persons, organizations, locations, dates, etc.) and classify them. Provide your analysis in JSON format with an array of entities, each having 'entity', 'type', and 'position' fields.

Text: {text}

Response format: {{"entities": [{{"entity": "entity_name", "type": "PERSON/ORG/LOC/DATE/etc", "position": [start, end]}}]}}"""
        try:
            response = await client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=500,
                temperature=0.1,
            )
            if response.choices:
                return response.choices[0].text
            else:
                return "Unable to perform token classification"
        except Exception as e:
            return f"Error performing token classification: {type(e).__name__}: {str(e)}"

if "all" in ENABLED_TOOLS or "fill_mask" in ENABLED_TOOLS:
    @app.tool()
    async def fill_mask(text: str) -> str:
        """Fill masked tokens in text using DeepInfra OpenAI-compatible API."""
        model = DEFAULT_MODELS["fill_mask"]
        prompt = f"""Fill in the [MASK] token in the following text with the most appropriate word. Provide the completed sentence and explain your choice.

Text: {text}

Response format: {{"filled_text": "completed sentence", "chosen_word": "word", "explanation": "reasoning"}}"""
        try:
            response = await client.completions.create(
                model=model,
                prompt=prompt,
                max_tokens=200,
                temperature=0.1,
            )
            if response.choices:
                return response.choices[0].text
            else:
                return "Unable to fill mask"
        except Exception as e:
            return f"Error filling mask: {type(e).__name__}: {str(e)}"

def main():
    app.run(transport='stdio')

if __name__ == "__main__":
    main()
