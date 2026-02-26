from app.services.model_service import ModelService
from fastapi import APIRouter

router = APIRouter()


@router.get("/models")
def list_models():
    """
    Returns all available trained models stored locally.
    """
    models = ModelService.get_local_models()

    return {"count": len(models), "models": models}
