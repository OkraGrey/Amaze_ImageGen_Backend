from openai import OpenAI

client = OpenAI()

import base64

def get_prompting_details(image_path):
    try:
        with open("test_client.png", "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        image_data_uri = f"data:image/png;base64,{image_base64}"

        response = client.chat.completions.create(
            model="gpt-4.1",   
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert translator that converts image structure into detailed JSON descriptions for image generation models."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this image and return a JSON description structured for image generation models like gpt-image-1."},
                        # 👇 Attach your local file here
                        {"type": "image_url", "image_url": {"url": image_data_uri}}
                    ]
                }
            ],
            temperature=0
        )
        return response.choices[0].message.content  
    except Exception as e:
        print(f"Error getting prompting details: {str(e)}")
        raise