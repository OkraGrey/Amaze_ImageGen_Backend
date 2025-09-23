from openai import OpenAI
import base64
from dotenv import load_dotenv
import os
import uuid
from pathlib import Path

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def remove_bg(image_path):
    """
    Remove background from an image using OpenAI's GPT-image-1 model.

    Args:
        image_path (str): Path to the input image

    Returns:
        str: Path to the processed image with background removed
    """
    print(f"[INFO]--- Starting background removal for image: {image_path} ---")

    try:
        # Ensure the image exists
        if not os.path.exists(image_path):
            print(f"[ERROR]--- Image not found at path: {image_path} ---")
            raise FileNotFoundError(f"Image not found at path: {image_path}")

        print(f"[INFO]--- Opening image file for OpenAI API ---")

        # Call OpenAI API to remove background
        with open(image_path, "rb") as image_file:
            print(f"[INFO]--- Calling OpenAI GPT-image-1 API for background removal ---")
            result = client.images.edit(
                model="gpt-image-1",
                image=image_file,
                prompt="Remove the background completely and make it transparent. Keep the main subject intact and preserve all details of the foreground object.",
                size="1024x1024",
                background="transparent",
                input_fidelity="high"
            )

        print(f"[INFO]--- OpenAI API call successful, processing response ---")

        # Decode the base64 image
        image_base64 = result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        # Generate output filename with _no_bg suffix
        input_path = Path(image_path)
        output_filename = f"{input_path.stem}_no_bg_{uuid.uuid4().hex[:8]}.png"
        output_path = input_path.parent / output_filename

        print(f"[INFO]--- Saving background-removed image to: {output_path} ---")

        # Save the processed image
        with open(output_path, "wb") as f:
            f.write(image_bytes)

        print(f"[INFO]--- Background removal completed successfully ---")
        return str(output_path)

    except Exception as e:
        print(f"[ERROR]--- Failed to remove background: {str(e)} ---")
        raise Exception(f"Failed to remove background: {str(e)}")