"""Lightweight Hugging Face integration (optional).

Supports two modes (in order of preference):
1. Inference API using `HF_API_TOKEN` environment variable or dynamically set token.
2. Local `transformers` pipeline if installed.

The module never stores tokens in the repo; it reads `HF_API_TOKEN` at runtime
or accepts a token dynamically via the `set_token()` function.
"""
import os
from typing import List, Optional

HF_MODEL = os.environ.get('HF_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2')
HF_DEVICE = int(os.environ.get('HF_DEVICE', '-1'))  # -1 means CPU for local pipeline

# Token can be set via environment variable or dynamically
_DYNAMIC_TOKEN = None

def _get_token():
    """Get the token from dynamic setting or environment variable."""
    if _DYNAMIC_TOKEN is not None:
        return _DYNAMIC_TOKEN
    return os.environ.get('HF_API_TOKEN')

HF_TOKEN = _get_token()

_PIPELINE = None

def _check_use_api():
    """Check if we should use the API based on token availability."""
    return bool(_get_token())

_USE_API = _check_use_api()

def set_token(token: str) -> bool:
    """Dynamically set the Hugging Face API token.
    
    Args:
        token: The Hugging Face API token (can be a read or write token)
        
    Returns:
        True if token was set successfully, False otherwise
    """
    global _DYNAMIC_TOKEN, _USE_API
    if token and len(token) > 10:
        _DYNAMIC_TOKEN = token
        _USE_API = True
        return True
    return False

def get_token_status() -> dict:
    """Get the current status of the Hugging Face token configuration.
    
    Returns:
        Dictionary with token status information
    """
    token = _get_token()
    return {
        'token_set': token is not None,
        'token_prefix': token[:10] + '...' if token else None,
        'model': HF_MODEL,
        'use_api': _check_use_api(),
        'local_pipeline_available': _ensure_local_pipeline() if not _check_use_api() else False
    }

def _ensure_local_pipeline():
    global _PIPELINE
    if _PIPELINE is not None:
        return True
    try:
        from transformers import pipeline
    except Exception:
        return False

    try:
        _PIPELINE = pipeline('feature-extraction', model=HF_MODEL, tokenizer=HF_MODEL, device=HF_DEVICE)
        return True
    except Exception:
        _PIPELINE = None
        return False

def available() -> bool:
    """Return True if either the Inference API token is set or local transformers are available."""
    if _check_use_api():
        return True
    return _ensure_local_pipeline()

def _call_inference_api(text: str) -> Optional[List[float]]:
    """Call the Hugging Face Inference API models endpoint to get feature-extraction output."""
    try:
        import requests
        url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
        token = _get_token()
        if not token:
            return None
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"inputs": text}
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            # Expecting list(batch) -> list(tokens) -> list(features) or list(features) for sentence models
            if isinstance(data, list) and len(data) > 0:
                # If token-level vectors returned, mean-pool tokens
                first = data[0]
                try:
                    # If first is list of token vectors
                    import numpy as _np
                    arr = _np.array(first, dtype=_np.float32)
                    vec = arr.mean(axis=0)
                    return vec.tolist()
                except Exception:
                    # If first is already a vector
                    if all(isinstance(x, (int, float)) for x in first):
                        return [float(x) for x in first]
        return None
    except Exception:
        return None

def get_embedding(text: str) -> Optional[List[float]]:
    """Return a 1-D embedding vector (mean-pooled) for `text` or None if unavailable.

    Tries Inference API first (when `HF_API_TOKEN` is set), then falls back to local `transformers`.
    """
    # Prefer remote inference API when token provided
    if _USE_API:
        emb = _call_inference_api(text)
        if emb is not None:
            return emb

    # Fallback to local pipeline
    if not _ensure_local_pipeline():
        return None

    try:
        outputs = _PIPELINE(text)
        if isinstance(outputs, list) and len(outputs) > 0:
            token_vectors = outputs[0]
            import numpy as _np
            arr = _np.array(token_vectors, dtype=_np.float32)
            vec = arr.mean(axis=0)
            return vec.tolist()
    except Exception:
        return None

    return None
