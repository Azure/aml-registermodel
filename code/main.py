import os
import json

from azureml.core import Workspace, Experiment, Run, Model
from azureml.core.authentication import ServicePrincipalAuthentication
from azureml.core.resource_configuration import ResourceConfiguration
from azureml.exceptions import AuthenticationException, ProjectSystemException, UserErrorException, ModelPathNotFoundException, WebserviceException
from adal.adal_error import AdalError
from msrest.exceptions import AuthenticationError
from json import JSONDecodeError
from utils import AMLConfigurationException, get_model_framework, get_dataset, get_best_run, compare_metrics, mask_parameter, validate_json, splitall
from schemas import azure_credentials_schema, parameters_schema


def main():
    # Loading input values
    print("::debug::Loading input values")
    experiment_name = os.environ.get("INPUT_EXPERIMENT_NAME", default=None)
    run_id = os.environ.get("INPUT_RUN_ID", default=None)

    # Loading azure credentials
    print("::debug::Loading azure credentials")
    azure_credentials = os.environ.get("INPUT_AZURE_CREDENTIALS", default="{}")
    try:
        azure_credentials = json.loads(azure_credentials)
    except JSONDecodeError:
        print("::error::Please paste output of `az ad sp create-for-rbac --name <your-sp-name> --role contributor --scopes /subscriptions/<your-subscriptionId>/resourceGroups/<your-rg> --sdk-auth` as value of secret variable: AZURE_CREDENTIALS")
        raise AMLConfigurationException("Incorrect or poorly formed output from azure credentials saved in AZURE_CREDENTIALS secret. See setup in https://github.com/Azure/aml-workspace/blob/master/README.md")

    # Checking provided parameters
    print("::debug::Checking provided parameters")
    validate_json(
        data=azure_credentials,
        schema=azure_credentials_schema,
        input_name="AZURE_CREDENTIALS"
    )

    # Mask values
    print("::debug::Masking parameters")
    mask_parameter(parameter=azure_credentials.get("tenantId", ""))
    mask_parameter(parameter=azure_credentials.get("clientId", ""))
    mask_parameter(parameter=azure_credentials.get("clientSecret", ""))
    mask_parameter(parameter=azure_credentials.get("subscriptionId", ""))

    # Loading parameters file
    print("::debug::Loading parameters file")
    parameters_file = os.environ.get("INPUT_PARAMETERS_FILE", default="registermodel.json")
    parameters_file_path = os.path.join(".cloud", ".azure", parameters_file)
    try:
        with open(parameters_file_path) as f:
            parameters = json.load(f)
    except FileNotFoundError:
        print(f"::debug::Could not find parameter file in {parameters_file_path}. Please provide a parameter file in your repository if you do not want to use default settings (e.g. .cloud/.azure/registermodel.json).")
        parameters = {}

    # Checking provided parameters
    print("::debug::Checking provided parameters")
    validate_json(
        data=parameters,
        schema=parameters_schema,
        input_name="PARAMETERS_FILE"
    )

    # Loading Workspace
    print("::debug::Loading AML Workspace")
    config_file_path = os.environ.get("GITHUB_WORKSPACE", default=".cloud/.azure")
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

    # Define default model name
    repository_name = os.environ.get("GITHUB_REPOSITORY").split("/")[-1]
    branch_name = os.environ.get("GITHUB_REF").split("/")[-1]
    default_model_name = f"{repository_name}-{branch_name}"
    default_tags = {}
    print(f"::debug::experiment_name: '{experiment_name}' and run_id: '{run_id}'")
    if not experiment_name or not run_id:
        # Registering model from local GitHub workspace
        print("::debug::Registering model from local GitHub workspace")
        default_tags = {
            "GITHUB_ACTOR": os.environ.get("GITHUB_ACTOR"),
            "GITHUB_REPOSITORY": os.environ.get("GITHUB_REPOSITORY"),
            "GITHUB_SHA": os.environ.get("GITHUB_SHA"),
            "GITHUB_REF": os.environ.get("GITHUB_REF"),
            "IS_LOCAL": True,
        }

        local_model = True

        # Defining model path
        print("::debug::Defining model path")
        model_file_name = parameters.get("model_file_name", "model.pkl")
        if len(splitall(model_file_name)) > 1:
            model_path = model_file_name
        else:
            directory = config_file_path = os.environ.get("GITHUB_WORKSPACE", default=None)
            model_paths = []
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    if filename == model_file_name:
                        path = os.path.join(root, filename)
                        model_paths.append(path)
            model_path = model_paths[0]
    else:
        # Registering model from AML run
        print("::debug::Registering model from AML run")
        local_model = False

        # Loading experiment
        print("::debug::Loading experiment")
        try:
            experiment = Experiment(
                workspace=ws,
                name=experiment_name
            )
        except UserErrorException as exception:
            print(f"::error::Loading experiment failed: {exception}")
            raise AMLConfigurationException("Could not load experiment. Please your experiment name as input parameter.")

        # Loading run by run id
        print("::debug::Loading run by run id")
        try:
            run = Run(
                experiment=experiment,
                run_id=run_id
            )
        except KeyError as exception:
            print(f"::error::Loading run failed: {exception}")
            raise AMLConfigurationException("Could not load run. Please add your run id as input parameter.")

        # Loading best run
        print("::debug::Loading best run")
        best_run = get_best_run(
            experiment=experiment,
            run=run,
            pipeline_child_run_name=parameters.get("pipeline_child_run_name", "model_training")
        )

        # Comparing metrics of runs
        print("::debug::Comparing metrics of runs")
        # Default model name
        if not parameters.get("force_registration", False):
            compare_metrics(
                workspace=ws,
                run=best_run,
                model_name=parameters.get("model_name", default_model_name)[:32],
                metrics_max=parameters.get("metrics_max", []),
                metrics_min=parameters.get("metrics_min", [])
            )
        default_tags = best_run.get_tags()

        # Defining model path
        print("::debug::Defining model path")
        model_file_name = parameters.get("model_file_name", "model.pkl")
        if len(splitall(model_file_name)) > 1:
            model_path = model_file_name
        else:
            model_path = [file_name for file_name in best_run.get_file_names() if model_file_name in os.path.split(file_name)[-1]][0]

    # Defining model framework
    print("::debug::Defining model framework")
    model_framework = get_model_framework(
        name=parameters.get("model_framework", None)
    )

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
    cpu = parameters.get("cpu_cores", None)
    memory = parameters.get("memory_gb", None)
    resource_configuration = ResourceConfiguration(cpu=cpu, memory_in_gb=memory) if (cpu is not None and memory is not None) else None

    if local_model:
        try:
            model = Model.register(
                workspace=ws,
                model_path=model_path,
                model_name=parameters.get("model_name", default_model_name)[:32],
                tags=dict(parameters.get("model_tags", {}), **default_tags),
                properties=parameters.get("model_properties", None),
                description=parameters.get("model_description", None),
                datasets=datasets,
                model_framework=model_framework,
                model_framework_version=parameters.get("model_framework_version", None),
                child_paths=[],
                sample_input_dataset=input_dataset,
                sample_output_dataset=output_dataset,
                resource_configuration=resource_configuration
            )
        except TypeError as exception:
            print(f"::error::Model could not be registered: {exception}")
            raise AMLConfigurationException("Model could not be registered")
        except WebserviceException as exception:
            print(f"::error::Model could not be registered: {exception}")
            raise AMLConfigurationException("Model could not be registered")
    else:
        try:
            model = best_run.register_model(
                model_name=parameters.get("model_name", default_model_name)[:32],
                model_path=model_path,
                tags=dict(parameters.get("model_tags", {}), **default_tags),
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
            raise AMLConfigurationException("Model name not found in outputs folder. Please provide the correct model file name and make sure that the model was saved by the run.")
        except WebserviceException as exception:
            print(f"::error::Model could not be registered: {exception}")
            raise AMLConfigurationException("Model could not be registered")

    # Create outputs
    print("::debug::Creating outputs")
    print(f"::set-output name=model_name::{model.name.split(':')[0]}")
    print(f"::set-output name=model_version::{model.version}")
    print(f"::set-output name=model_id::{model.id}")
    print("::debug::Successfully completed Azure Machine Learning Register Model Action")


if __name__ == "__main__":
    main()
