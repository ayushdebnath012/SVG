import os
from diffusvg import DiffusionConfig, PipelineConfig, DiffuSVGPipeline

def test_token_loading():
    print("Testing token retrieval...")
    
    # Temporarily remove HF_TOKEN to test fallback mechanism
    original_token = os.environ.get("HF_TOKEN")
    if "HF_TOKEN" in os.environ:
        del os.environ["HF_TOKEN"]
        
    config = DiffusionConfig()
    print(f"Fallback Token: {config.hf_token}")
    assert config.hf_token == "YOUR_HF_TOKEN_HERE", "Fallback token mismatch!"
    
    # Test environment variable overrides fallback
    os.environ["HF_TOKEN"] = "hf_test_env_token_123"
    config_env = DiffusionConfig()
    print(f"Env Token: {config_env.hf_token}")
    assert config_env.hf_token == "hf_test_env_token_123", "Environment token mismatch!"
    
    # Test complete pipeline config parsing
    pipe_cfg = PipelineConfig()
    pipe_cfg.diffusion.hf_token = "hf_test_env_token_123"
    
    # Try to initialize pipeline without running VLM or generating
    print("Initializing DiffuSVGPipeline (lazy loading check)...")
    pipeline = DiffuSVGPipeline(config=pipe_cfg)
    print(f"Pipeline initialized. Config Token: {pipeline.config.diffusion.hf_token}")
    
    if original_token:
        os.environ["HF_TOKEN"] = original_token
    else:
        del os.environ["HF_TOKEN"]
        
    print("All token loading tests passed.")

if __name__ == "__main__":
    test_token_loading()
