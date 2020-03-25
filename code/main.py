import os
import json

from azureml.core import Workspace, Experiment, Run
from azureml.core.authentication import ServicePrincipalAuthentication
from azureml.core.resource_configuration import ResourceConfiguration
from azureml.exceptions import AuthenticationException, ProjectSystemException, UserErrorException, ModelPathNotFoundException, WebserviceException
from adal.adal_error import AdalError
from msrest.exceptions import AuthenticationError
from json import JSONDecodeError
from utils import AMLConfigurationException, required_parameters_provided, get_model_framework, get_dataset, get_best_run, compare_metrics


def main():
    # Loading input values
    print("::debug::Loading input values")
    parameters_file = os.environ.get("INPUT_PARAMETERSFILE", default="run.json")
    azure_credentials = os.environ.get("INPUT_AZURECREDENTIALS", default="{}")
    experiment_name = os.environ.get("INPUT_EXPERIMENTNAME", default=None)
    run_id = os.environ.get("INPUT_RUNID", default=None)
    try:
        azure_credentials = json.loads(azure_credentials)
    except JSONDecodeError:
        print("::error::Please paste output of `az ad sp create-for-rbac --name <your-sp-name> --role contributor --scopes /subscriptions/<your-subscriptionId>/resourceGroups/<your-rg> --sdk-auth` as value of secret variable: AZURE_CREDENTIALS")
        raise AMLConfigurationException(f"Incorrect or poorly formed output from azure credentials saved in AZURE_CREDENTIALS secret. See setup in https://github.com/Azure/aml-workspace/blob/master/README.md")

    # Checking provided parameters
    print("::debug::Checking provided parameters")
    required_parameters_provided(
        parameters=azure_credentials,
        keys=["tenantId", "clientId", "clientSecret"],
        message="Required parameter(s) not found in your azure credentials saved in AZURE_CREDENTIALS secret for logging in to the workspace. Please provide a value for the following key(s): "
    )

    # Loading parameters file
    print("::debug::Loading parameters file")
    parameters_file_path = os.path.join(".ml", ".azure", parameters_file)
    try:
        with open(parameters_file_path) as f:
            parameters = json.load(f)
    except FileNotFoundError:
        print(f"::error::Could not find parameter file in {parameters_file_path}. Please provide a parameter file in your repository (e.g. .ml/.azure/workspace.json).")
        raise AMLConfigurationException(f"Could not find parameter file in {parameters_file_path}. Please provide a parameter file in your repository (e.g. .ml/.azure/workspace.json).")

    # Loading Workspace
    print("::debug::Loading AML Workspace")
    config_file_path = os.environ.get("GITHUB_WORKSPACE", default=".ml/.azure")
    config_file_name = "aml_arm_config.json"
    sp_auth = ServicePrincipalAuthentication(
        tenant_id=azure_credentials.get("tenantId", ""),
        service_principal_id=azure_credentials.get("clientId", ""),
        service_principal_password=azure_credentials.get("clientSecret", "")
    )
    try:
        ws = Workspace.from_config(
            path=config_file_path,
            _file_name=config_file_name,
            auth=sp_auth
        )
    except AuthenticationException as exception:
        print(f"::error::Could not retrieve user token. Please paste output of `az ad sp create-for-rbac --name <your-sp-name> --role contributor --scopes /subscriptions/<your-subscriptionId>/resourceGroups/<your-rg> --sdk-auth` as value of secret variable: AZURE_CREDENTIALS: {exception}")
        raise AuthenticationException
    except AuthenticationError as exception:
        print(f"::error::Microsoft REST Authentication Error: {exception}")
        raise AuthenticationError
    except AdalError as exception:
        print(f"::error::Active Directory Authentication Library Error: {exception}")
        raise AdalError
    except ProjectSystemException as exception:
        print(f"::error::Workspace authorization failed: {exception}")
        raise ProjectSystemException

    # Loading experiment
    print("::debug::Loading experiment")
    try:
        experiment = Experiment(
            workspace=ws,
            name=experiment_name
        )
    except UserErrorException as exception:
        print(f"::error::Loading experiment failed: {exception}")
        raise AMLConfigurationException(f"Could not load experiment. Please your experiment name as input parameter.")

    # Loading run by run id
    print("::debug::Loading run by run id")
    try:
        run = Run(
            experiment=experiment,
            run_id=run_id
        )
    except KeyError as exception:
        print(f"::error::Loading run failed: {exception}")
        raise AMLConfigurationException(f"Could not load run. Please your run id as input parameter.")

    # Loading best run
    print("::debug::Loading best run")
    best_run = get_best_run(
        experiment=experiment,
        run=run,
        pipeline_child_run_name=parameters.get("pipeline_child_run_name", None)
    )

    # Comparing metrics of runs
    print("::debug::Comparing metrics of runs")
    compare_metrics(
        workspace=ws,
        run=best_run,
        model_name=parameters.get("model_name", None),
        metrics_max=parameters.get("metrics_max", []),
        metrics_min=parameters.get("metrics_min", [])
    )

    # Checking provided parameters
    print("::debug::Checking provided parameters")
    required_parameters_provided(
        parameters=parameters,
        keys=["model_name", "model_file_name"],
        message="Required parameter(s) not found in your parameters file for registering the model. Please provide a value for the following key(s): "
    )

    # Defining model framework
    print("::debug::Defining model framework")
    model_framework = get_model_framework(
        name=parameters.get("model_framework", None)
    )

    # Defining model path
    print("::debug::Defining model path")
    model_file_name = parameters.get("model_file_name", None)
    model_path = [file_name for file_name in best_run.get_file_names() if model_file_name in os.path.split(file_name)[-1]][0]

    # Defining datasets
    print("::debug::Defining datasets")
    datasets = []
    for dataset_name in parameters.get("datasets", []):
        dataset = get_dataset(
            workspace=ws,
            name=dataset_name
        )
        if dataset is not None:
            datasets.append((f"{dataset_name}", dataset))
    input_dataset = get_dataset(
        workspace=ws,
        name=parameters.get("sample_input_dataset", None)
    )
    output_dataset = get_dataset(
        workspace=ws,
        name=parameters.get("sample_output_dataset", None)
    )

    # Defining resource configuration
    print("::debug::Defining resource configuration")
    cpu = parameters.get("cpu", None)
    memory = parameters.get("memory", None)
    resource_configuration = ResourceConfiguration(cpu=cpu, memory_in_gb=memory) if (cpu is not None and memory is not None) else None

    try:
        model = best_run.register_model(
            model_name=parameters.get("model_name", None),
            model_path=model_path,
            tags=parameters.get("model_tags", None),
            properties=parameters.get("model_properties", None),
            model_framework=model_framework,
            model_framework_version=parameters.get("model_framework_version", None),
            description=parameters.get("model_description", None),
            datasets=datasets,
            sample_input_dataset=input_dataset,
            sample_output_dataset=output_dataset,
            resource_configuration=resource_configuration
        )
    except ModelPathNotFoundException as exception:
        print(f"::error::Model name not found in outputs folder. Please provide the correct model file name and make sure that the model was saved by the run: {exception}")
        raise AMLConfigurationException(f"Model name not found in outputs folder. Please provide the correct model file name and make sure that the model was saved by the run.")
    except WebserviceException as exception:
        print(f"::error::Model could not be registered: {exception}")
        raise AMLConfigurationException("Model could not be registered")

    # Create outputs
    print("::debug::Creating outputs")
    print(f"::set-output name=modelName::{model.name}")
    print(f"::set-output name=modelVersion::{model.version}")
    print(f"::set-output name=modelId::{model.id}")
    print("::debug::Successfully completed Azure Machine Learning Register Model Action")


if __name__ == "__main__":
    main()
