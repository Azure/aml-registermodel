azure_credentials_schema = {
    "$id": "http://azure-ml.com/schemas/azure_credentials.json",
    "$schema": "http://json-schema.org/schema",
    "title": "azure_credentials",
    "description": "JSON specification for your azure credentials",
    "type": "object",
    "required": ["clientId", "clientSecret", "subscriptionId", "tenantId"],
    "properties": {
        "clientId": {
            "type": "string",
            "description": "The client ID of the service principal."
        },
        "clientSecret": {
            "type": "string",
            "description": "The client secret of the service principal."
        },
        "subscriptionId": {
            "type": "string",
            "description": "The subscription ID that should be used."
        },
        "tenantId": {
            "type": "string",
            "description": "The tenant ID of the service principal."
        }
    }
}

parameters_schema = {
    "$id": "http://azure-ml.com/schemas/registermodel.json",
    "$schema": "http://json-schema.org/schema",
    "title": "aml-registermodel",
    "description": "JSON specification for your registermodel details",
    "type": "object",
    "properties": {
        "model_file_name": {
            "type": "string",
            "description": "The file name for the model asset."
        },
        "model_name": {
            "type": "string",
            "description": "The name to register the model with.",
            "minLength": 1,
            "maxLength": 32
        },
        "model_framework": {
            "type": "string",
            "description": "The framework of the registered model.",
            "pattern": "scikitlearn|onnx|tensorflow|keras|custom"
        },
        "model_framework_version": {
            "type": "string",
            "description": "The framework version of the registered model."
        },
        "model_tags": {
            "type": "object",
            "description": "An optional dictionary of key value tags to assign to the model."
        },
        "model_properties": {
            "type": "object",
            "description": "An optional dictionary of key value properties to assign to the model. These properties can't be changed after model creation."
        },
        "model_description": {
            "type": "string",
            "description": "A text description of the model."
        },
        "datasets": {
            "type": "array",
            "description": "A list of dataset names that are registered in your workspace that should be assigned to the registered model."
        },
        "sample_input_dataset": {
            "type": "string",
            "description": "Name of a sample input dataset that is regstered in your workspace for the registered model."
        },
        "sample_output_dataset": {
            "type": "string",
            "description": "Name of a sample output dataset that is regstered in your workspace for the registered model."
        },
        "pipeline_child_run_name": {
            "type": "string",
            "description": "If you provided a run ID of a pipeline to this GitHub Action, you have to specify the name of the step that produced the model."
        },
        "cpu_cores": {
            "type": "number",
            "description": "The number of CPU cores to allocate for this resource.",
            "exclusiveMinimum": 0.0
        },
        "memory_gb": {
            "type": "number",
            "description": "The amount of memory (in GB) to allocate for this resource.",
            "exclusiveMinimum": 0.0
        },
        "metrics_max": {
            "type": "array",
            "description": "List of metrics names that must be maximized. The action compares the metrics of the provided run with the linked run of the latest model with the same name that is registered in the model registry."
        },
        "metrics_min": {
            "type": "array",
            "description": "List of metrics names that must be minimized. The action compares the metrics of the provided run with the linked run of the latest model with the same name that is registered in the model registry."
        },
        "force_registration": {
            "type": "boolean",
            "description": "Boolean value that determines whether or not to force the registration of the model regardless of the provided metrics."
        }
    }
}
