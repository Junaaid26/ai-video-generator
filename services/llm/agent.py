import os
import time
from pydantic import BaseModel, ValidationError
from api.schemas import VideoPlan
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.api_core import exceptions as api_exceptions

load_dotenv()

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
    return genai.Client(api_key=api_key)

def generate_video_plan(prompt: str, duration: str, language: str, style: str, target_platform: str) -> VideoPlan:
    """
    Calls the LLM to generate a structured video plan based on the user's prompt.
    """
    client = get_gemini_client()
    
    system_prompt = f"""You are an expert social media video producer. 
Your goal is to create a highly engaging, viral-ready video script and scene plan.
You must output the result strictly as a JSON object matching the requested schema.

Target Duration: {duration}
Language: {language}
Style/Tone: {style}
Target Platform: {target_platform}
"""

    user_prompt = f"Create a video plan for the following request: {prompt}"
    full_prompt = f"{system_prompt}\n\nUser Request: {user_prompt}"

    max_retries = 5
    base_delay = 1  # seconds
    import random
    from google.api_core import exceptions as api_exceptions

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=VideoPlan,
                ),
            )
            # Ensure response contains text
            if not getattr(response, "text", None):
                raise Exception("Empty response from Gemini")
            return VideoPlan.model_validate_json(response.text)
        except ValidationError as e:
            raise Exception(f"Failed to parse valid video plan structure from Gemini response: {str(e)}")
        except (api_exceptions.ServiceUnavailable, api_exceptions.ResourceExhausted, api_exceptions.TooManyRequests) as e:
            # Transient errors – retry with exponential backoff and jitter
            if attempt < max_retries - 1:
                jitter = random.random()
                delay = base_delay * (2 ** attempt) + jitter
                time.sleep(delay)
                continue
            else:
                raise Exception("Gemini API is temporarily unavailable or experiencing high demand. Please try again later.")
        except genai_errors.ClientError as e:
            # Distinguish quota exhaustion from temporary rate limits
            error_str = str(e)
            if "GenerateRequestsPerDayPerModel-FreeTier".lower() in error_str.lower() or "free-tier quota" in error_str.lower():
                raise Exception("Gemini free-tier quota has been reached for this model. Please wait for the quota reset or use another available Gemini API project/model.")
            # For other 429 errors, treat as transient and retry if attempts remain
            if attempt < max_retries - 1:
                retry_delay = None
                try:
                    import json, re
                    json_part = re.search(r"\{.*\}", error_str).group(0)
                    data = json.loads(json_part)
                    for item in data.get("error", {}).get("details", []):
                        if item.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                            retry_delay = item.get("retryDelay")
                            break
                except Exception:
                    retry_delay = None
                if retry_delay:
                    try:
                        delay_secs = float(re.findall(r"[0-9.]+", retry_delay)[0])
                    except Exception:
                        delay_secs = base_delay * (2 ** attempt) + random.random()
                else:
                    delay_secs = base_delay * (2 ** attempt) + random.random()
                time.sleep(delay_secs)
                continue
            else:
                raise Exception("Gemini API rate limit reached. Please try again later.")
        except Exception as e:
            # Non-transient errors – do not retry
            raise Exception(f"Failed to generate video plan: {str(e)}")
            raise Exception(f"Failed to parse valid video plan structure from Gemini response: {str(e)}")
        except (api_exceptions.ServiceUnavailable, api_exceptions.ResourceExhausted, api_exceptions.TooManyRequests) as e:
            # Transient errors – retry with exponential backoff and jitter
            if attempt < max_retries - 1:
                jitter = random.random()
                delay = base_delay * (2 ** attempt) + jitter
                time.sleep(delay)
                continue
            else:
                raise Exception("Gemini API is temporarily unavailable or experiencing high demand. Please try again later.")
            # Transient errors – retry with exponential backoff and jitter
            if attempt < max_retries - 1:
                jitter = random.random()
                delay = base_delay * (2 ** attempt) + jitter
                time.sleep(delay)
                continue
            else:
                raise Exception("Gemini API is temporarily unavailable or experiencing high demand. Please try again later.")
        except genai_errors.ClientError as e:
            # Distinguish quota exhaustion from temporary rate limits
            error_str = str(e)
            if "GenerateRequestsPerDayPerModel-FreeTier" in error_str or "free-tier quota" in error_str.lower():
                raise Exception("Gemini free-tier quota has been reached for this model. Please wait for the quota reset or use another available Gemini API project/model.")
            # For other 429 errors, treat as transient and retry if attempts remain
            if attempt < max_retries - 1:
                # Attempt to extract retry delay from error details if present
                retry_delay = None
                try:
                    import json, re
                    json_part = re.search(r"\{.*\}", error_str).group(0)
                    data = json.loads(json_part)
                    retry_info = data.get("error", {}).get("details", [])
                    for item in retry_info:
                        if item.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                            retry_delay = item.get("retryDelay")
                            break
                except Exception:
                    retry_delay = None
                if retry_delay:
                    try:
                        delay_secs = float(re.findall(r"[0-9.]+", retry_delay)[0])
                    except Exception:
                        delay_secs = base_delay * (2 ** attempt) + random.random()
                else:
                    delay_secs = base_delay * (2 ** attempt) + random.random()
                time.sleep(delay_secs)
                continue
            else:
                raise Exception("Gemini API rate limit reached. Please try again later.")
            # Distinguish quota exhaustion from temporary rate limits
            error_str = str(e)
            if "GenerateRequestsPerDayPerModel-FreeTier" in error_str or "free-tier quota" in error_str.lower():
                raise Exception("Gemini free-tier quota has been reached for this model. Please wait for the quota reset or use another available Gemini API project/model.")
            # For other 429 errors, treat as transient and retry if attempts remain
            if attempt < max_retries - 1:
                # Attempt to extract retry delay from error details if present
                retry_delay = None
                try:
                    import json, re
                    # Extract JSON part from the exception string
                    json_part = re.search(r"\{.*\}", error_str).group(0)
                    data = json.loads(json_part)
                    retry_info = data.get("error", {}).get("details", [])
                    for item in retry_info:
                        if item.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                            retry_delay = item.get("retryDelay")
                            break
                except Exception:
                    retry_delay = None
                if retry_delay:
                    # retryDelay format like '58s' – convert to seconds
                    try:
                        delay_secs = float(re.findall(r"[0-9.]+", retry_delay)[0])
                    except Exception:
                        delay_secs = base_delay * (2 ** attempt) + random.random()
                else:
                    delay_secs = base_delay * (2 ** attempt) + random.random()
                time.sleep(delay_secs)
                continue
            else:
                raise Exception("Gemini API rate limit reached. Please try again later.")
        except Exception as e:
            # Non-transient errors – do not retry
            raise Exception(f"Failed to generate video plan: {str(e)}")
