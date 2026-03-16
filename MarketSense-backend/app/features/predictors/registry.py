from .lstm_predictor import predict_lstm
from .prophet_predictor import predict_prophet
from .xgboost_predictor import predict_xgboost

PREDICTORS = {
    "prophet": predict_prophet,
    "xgboost": predict_xgboost,
    "lstm": predict_lstm,
    "pytorch": predict_lstm,
}


def get_predictor(model_name: str):
    model_name = model_name.lower()
    predictor = PREDICTORS.get(model_name)
    if not predictor:
        raise ValueError(f"Predictor for model '{model_name}' not found.")
    return predictor
