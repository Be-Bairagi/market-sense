from .prophet_predictor import predict_prophet

PREDICTORS = {
    "prophet": predict_prophet,
    # "xgboost": predict_xgboost,
    # "lstm": predict_lstm,
}


def get_predictor(model_name: str):
    model_name = model_name.lower()
    predictor = PREDICTORS.get(model_name)
    if not predictor:
        raise ValueError(f"Predictor for model '{model_name}' not found.")
    return predictor
