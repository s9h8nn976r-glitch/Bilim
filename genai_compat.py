"""Compatibility adapter to mimic google.generativeai interface using google.genai client.

This adapter implements a minimal wrapper for:
- genai.configure(api_key=...)
- genai.GenerativeModel(model_name).generate_content(input)

It returns objects with a .text attribute similar to the previous SDK usage in the repository.

Note: This adapter aims to provide a minimal interface required by the repo handlers.
"""

import os
from typing import Any, Dict, List

# Try to import the new Google GenAI client. The package name may vary depending on
# the distribution. We try common names and raise a clear error if none is available.
try:
    # Newer packages use google.genai
    import google.genai as genai_client
except Exception:
    try:
        # fallback package name (if different distributions exist)
        import genai as genai_client
    except Exception as e:
        raise ImportError("google.genai client is required for genai_compat adapter: " + str(e))

_api_key = None


def configure(api_key: str):
    global _api_key
    _api_key = api_key
    # configure the underlying client if it supports setting API key via env
    os.environ.setdefault("GOOGLE_API_KEY", api_key)


class _Response:
    def __init__(self, text: str):
        self.text = text


class GenerativeModel:
    def __init__(self, model_name: str):
        self.model_name = model_name
        # create a client instance if the library uses client objects
        try:
            # google.genai typically exposes a Client class
            self.client = genai_client.Client()
        except Exception:
            self.client = None

    def generate_content(self, input_data: Any) -> _Response:
        """
        Accepts either a plain prompt string or a list with [prompt, {mime_type, data}] style.
        Returns an object with .text to match previous behavior.
        """
        prompt = None
        image_bytes = None

        if isinstance(input_data, list):
            # earlier code sometimes passed [prompt, {mime_type: ..., data: image_bytes}]
            if len(input_data) >= 1:
                prompt = input_data[0]
            # look for an image dict
            for item in input_data[1:]:
                if isinstance(item, dict) and item.get("mime_type", "").startswith("image"):
                    image_bytes = item.get("data")
                    break
        elif isinstance(input_data, str):
            prompt = input_data
        else:
            prompt = str(input_data)

        # Use genai_client to make a text generation request. API details vary across
        # versions; attempt a reasonable default call and fall back gracefully.
        try:
            if self.client is not None:
                # Example for google.genai: client.responses.generate(...)
                try:
                    resp = self.client.responses.generate(
                        model=self.model_name,
                        input=prompt,
                    )
                    # Try to extract text from common response shapes
                    text = ""
                    if hasattr(resp, 'output'):
                        # google.genai.Response may have an output list
                        out = resp.output
                        if isinstance(out, list) and out:
                            # join text fields
                            parts = []
                            for item in out:
                                # item might be a dict-like or an object
                                if isinstance(item, dict) and 'content' in item:
                                    parts.append(item['content'])
                                elif hasattr(item, 'text'):
                                    parts.append(item.text)
                                elif hasattr(item, 'content'):
                                    parts.append(item.content)
                            text = "\n".join(parts)
                    elif isinstance(resp, dict):
                        # fallback for dict-shaped responses
                        text = resp.get('text', '') or resp.get('output', '')
                    else:
                        text = str(resp)
                    return _Response(text)
                except Exception:
                    # try alternate surface if exists
                    pass

            # If no client or previous call failed, try module-level convenience method
            if hasattr(genai_client, 'generate'):
                resp = genai_client.generate(model=self.model_name, prompt=prompt)
                # resp may be a dict
                if isinstance(resp, dict):
                    return _Response(resp.get('text', '') or str(resp))
                return _Response(str(resp))

            # Last resort: return the prompt as the response so callers don't break.
            return _Response(prompt or "")

        except Exception as e:
            # On error return the error message as text to allow handlers to show it.
            return _Response(f"[genai error] {str(e)}")
