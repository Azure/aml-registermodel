import os
import sys
import pytest

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(myPath, "..", "code"))

from utils import validate_json, AMLConfigurationException
from schemas import parameters_schema


def test_validate_json_valid_inputs():
    """
    Unit test to check the validate_json function with valid inputs
    """
    json_object = {
        "model_name": "model-name",
        "model_file_name": "model-file-name",
        "model_framework": "onnx"
    }
    validate_json(
        data=json_object,
        schema=parameters_schema,
        input_name="PARAMETERS_FILE"
    )


def test_validate_json_invalid_json():
    """
    Unit test to check the validate_json function with invalid json_object inputs
    """
    json_object = {
        "cpu": "0.1"
    }
    with pytest.raises(AMLConfigurationException):
        assert validate_json(
            data=json_object,
            schema=parameters_schema,
            input_name="PARAMETERS_FILE"
        )


def test_validate_json_invalid_schema():
    """
    Unit test to check the validate_json function with invalid schema inputs
    """
    json_object = {}
    schema_object = {}
    with pytest.raises(Exception):
        assert validate_json(
            data=json_object,
            schema=schema_object,
            input_name="PARAMETERS_FILE"
        )
