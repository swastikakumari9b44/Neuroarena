from fastapi import APIRouter
from ..schemas import AIMoveRequest, AIMoveResponse
router = APIRouter()

@router.post("/move", response_model=AIMoveResponse)
def ai_move(request: AIMoveRequest):
    """Get AI action for given state"""
    # Load model and predict
    try:
        from stable_baselines3 import PPO
        import os
        
        model_path = f"{request.model_name or 'ppo_neuroarena_1m'}"
        
        if os.path.exists(f"{model_path}.zip"):
            model = PPO.load(model_path)
            action, _ = model.predict(request.state, deterministic=True)
            return {"action": int(action), "confidence": 0.95}
        else:
            # Random action if model not found
            import random
            return {"action": random.randint(0, 5), "confidence": 0.5}
    except Exception as e:
        import random
        return {"action": random.randint(0, 5), "confidence": 0.5}