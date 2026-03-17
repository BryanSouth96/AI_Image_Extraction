from openai import AzureOpenAI
from azure.identity import AzureCliCredential, get_bearer_token_provider

import base64
import json
import requests
from pathlib import Path
import pandas as pd

def llm_extract(prompt_path, doctype, data_path):    

    with open(prompt_path, encoding='utf8') as file:
        # Read the contents of the file
        prompt = file.read()

    # Read image and encode as base64
    with open(data_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    token_provider = get_bearer_token_provider(
        AzureCliCredential(), "https://cognitiveservices.azure.com/.default"
    )

    client = AzureOpenAI(
        azure_ad_token_provider=token_provider,
        api_version="2025-01-01-preview",
        azure_endpoint = "https://aimd-expl-ai-production.openai.azure.com"
    )

    deployment_name='gpt-5-mini-ptu-2025-08-07'
       
    messages=[
        { "role": "system", "content": prompt },
        { "role": "user", "content": [  
            { 
                "type": "text", 
                "text": "", 
            },
            { 
                "type": "image_url",
                "image_url":
                {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": "high"
                }
            }
        ] } 
    ],


    # Send a completion call to generate an answer
    response = client.chat.completions.create(model=deployment_name, messages = messages[0])

    # Convert to JSON 
    llm_response = response.choices[0].message.content
    start_index = llm_response.find('[')
    end_index = llm_response.rfind(']') + 1              
    llm_response = llm_response[start_index:end_index]
    try:
        llm_response = json.loads(llm_response)
    except:
        llm_response = []

    return llm_response

def get_jpg_paths(dir_path):
    p = Path(dir_path)
    return [str(p.resolve()) for p in p.rglob('*') if p.suffix.lower() in {'.jpg', '.jpeg'}]

# Running 
prompt_path = "prompt.txt" 
data_directory = get_jpg_paths("images/") # Only example, change to your directory

df = pd.DataFrame()
for i, data_path in enumerate(data_directory):
    print(f'Processing {i+1} of {len(data_directory)}')    
    out = llm_extract(prompt_path, 'img', data_path)
    df = pd.concat([df, pd.DataFrame(out)], ignore_index=True)  

df.to_excel('Output.xlsx')

