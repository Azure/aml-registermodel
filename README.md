![Integration Test](https://github.com/Azure/aml-registermodel/workflows/Integration%20Test/badge.svg)
![Lint](https://github.com/Azure/aml-registermodel/workflows/Lint/badge.svg)

# Azure Machine Learning Register Model Action

## Usage

The Azure Machine Learning Register Model action will register your model in the Azure Machine Learning model registry for use in deployment and testing. This action is designed to only register the model, if the run has produced better metrics than the latest model that is registered under the same name. The metrics comparison can be controlled with the `metrics_max` and `metrics_min` parameters. These parameters define the names of the metrics that should be used for a comparison. Only if the model performs better for all metrics, the actions completes successfully and registers the model.

This behavior can be overruled by passing the `force_registration` as true. You will need to have azure credentials that allow you to connect to the Azure MAchine Learning workspace.

This action requires an AML workspace to be created or attached to via the [aml-workspace](https://github.com/Azure/aml-workspace) action as well as a run that produces a model that can be either be created via the [aml-run](https://github.com/Azure/aml-run) action or supplied directly via the `experiment_name` and `run_id` input parameters.

## Template repositories

This action is one in a series of actions that can be used to setup an ML Ops process. Examples of these can be found at
1. Simple example: [ml-template-azure](https://github.com/machine-learning-apps/ml-template-azure) and
2. Comprehensive example: [aml-template](https://github.com/Azure/aml-template).

### Example workflow

```yaml
name: My Workflow
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    # Checks-out your repository under $GITHUB_WORKSPACE, so your job can access it
    - name: Check Out Repository
      id: checkout_repository
      uses: actions/checkout@v2

    # AML Workspace Action
    - uses: Azure/aml-workspace
      id: aml_workspace
      with:
        azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
    
    # AML Run Action
    - uses: Azure/aml-run@v1
      id: aml_run
      with:
        azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}

    # AML Register Model Action
    - uses: Azure/aml-registermodel@v1
      id: aml_registermodel
      with:
        # required inputs
        azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
        run_id:  ${{ steps.aml_run.outputs.run_id }}
        experiment_name: ${{ steps.aml_run.outputs.experiment_name }}
        # optional inputs
        parameters_file: "registermodel.json"
```

### Inputs

| Input | Required | Default | Description |
| ----- | -------- | ------- | ----------- |
| azure_credentials | x | - | Output of `az ad sp create-for-rbac --name <your-sp-name> --role contributor --scopes /subscriptions/<your-subscriptionId>/resourceGroups/<your-rg> --sdk-auth`. This should be stored in your secrets. |
| experiment_name | x | - | Experiment name to which the run belongs to. |
| run_id | x | - | ID of the run or pipeline run for which a model is to be registered. |
| parameters_file |  | `"registermodel.json"` | JSON file in the `.cloud/.azure` folder specifying your Azure Machine Learning model registration details. |

#### Azure Credentials

Azure credentials are required to connect to your Azure Machine Learning Workspace. These may have been created for an action you are already using in your repository, if so, you can skip the steps below.

Install the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest) on your computer or use the Cloud CLI and execute the following command to generate the required credentials:

```sh
# Replace {service-principal-name}, {subscription-id} and {resource-group} with your Azure subscription id and resource group name and any name for your service principle
az ad sp create-for-rbac --name {service-principal-name} \
                         --role contributor \
                         --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} \
                         --sdk-auth
```

This will generate the following JSON output:

```sh
{
  "clientId": "<GUID>",
  "clientSecret": "<GUID>",
  "subscriptionId": "<GUID>",
  "tenantId": "<GUID>",
  (...)
}
```

Add this JSON output as [a secret](https://help.github.com/en/actions/configuring-and-managing-workflows/creating-and-storing-encrypted-secrets#creating-encrypted-secrets) with the name `AZURE_CREDENTIALS` in your GitHub repository.

#### Parameters File

The action tries to load a JSON file in the `.cloud/.azure` folder in your repository, which specifies details for the model registration to your Azure Machine Learning Workspace. By default, the action is looking for a file with the name `registermodel.json`. If your JSON file has a different name, you can specify it with this parameter. Note that none of these values are required and in the absence, defaults will be used.

A sample file can be found in this repository in the folder `.cloud/.azure`. The JSON file can include the following parameters:

| Parameter               | Required | Allowed Values | Default    | Description |
| ----------------------- | -------- | -------------- | ---------- | ----------- |
| model_file_name         |          | str            | `"model.pkl"` | The file name for the model asset. You only have to specify the name of the model file (e.g. (`"model.pkl"`)) and not the path (e.g. `"outputs/model.pkl"`). The action can take care of the path that was used to store the file. You can also specify the path, if you want to. |
| model_name              |          | str            | <REPO_NAME>-<BRANCH_NAME> |The name to register the model with. It must only consist of letters, numbers, dashes, periods, or underscores, start with a letter or number, and be between 1 and 32 characters long. |
| model_framework         |          | str: `"scikitlearn"`, `"onnx"`, `"tensorflow"`, `"keras"`, `"custom"` | `"custom"` | The framework of the registered model. | 
| model_framework_version |          | str      | null     | The framework version of the registered model. |
| model_tags              |          | dict: {"<your-run-tag-key>": "<your-run-tag-value>", ...}  | null | An optional dictionary of key value tags to assign to the model. |
| model_properties        |          | dict: {"<your-run-property-key>": "<your-run-property-value>", ...}  | null | An optional dictionary of key value properties to assign to the model. These properties can't be changed after model creation, however new key value pairs can be added. |
| model_description       |          | str   | null | A text description of the model. |
| datasets                |          | list  | null | A list of dataset names that are registered in your workspace that should be assigned to the registered model. |
| sample_input_dataset    |          | str   | null | Name of a sample input dataset that is regstered in your workspace for the registered model. |
| sample_output_dataset   |          | str   | null | Name of a sample output dataset that is regstered in your workspace for the registered model. |
| pipeline_child_run_name |  | str   | `"model_training"` | If you provided a run ID of a pipeline to this GitHub Action, you have to specify the name of the step that produced the model. Without providing the name of the step that produced the model, the Action does not know where to look for the model file. The step in the pipeline with the provided name can be of any type (HyperDriveStep, PythonScriptStep, etc.). There are no limitations on the step type. |
| cpu_cores               |          | float: ]0.0, inf[ | null | The number of CPU cores to allocate for this resource. Can be a decimal. You have to specify `cpu` and `memory` to register the model with a resource configuration. If you do not specify both parameters the model will be registered without a resource configuration. |
| memory_gb               |          | float: ]0.0, inf[ | null | The amount of memory (in GB) to allocate for this resource. Can be a decimal. You have to specify `cpu` and `memory` to register the model with a resource configuration. If you do not specify both parameters the model will be registered without a resource configuration. |
| metrics_max             |          | list  | null | List of metrics names that must be maximized. The action compares the metrics of the provided run with the linked run of the latest model with the same name that is registered in the model registry. The action fails if any of the specified metrics are lower than the metrics of the latest model in your model registry. If a model with the same name cannot be found or if the latest model in your model registry is not linked to a run in Azure Machine Learning, it will register the model without comparing any metrics. |
| metrics_min             |          | list  | null | List of metrics names that must be minimized. The action compares the metrics of the provided run with the linked run of the latest model with the same name that is registered in the model registry. The action fails if any of the specified metrics are higher than the metrics of the latest model in your model registry. If a model with the same name cannot be found or if the latest model in your model registry is not linked to a run in Azure Machine Learning, it will register the model without comparing any metrics. |
| force_registration      |          | bool  | false | Boolean value that determines whether or not to force the registration of the model regardless of the provided metrics. |

Please visit [this website](https://docs.microsoft.com/en-us/python/api/azureml-core/azureml.core.model(class)?view=azure-ml-py#register-workspace--model-path--model-name--tags-none--properties-none--description-none--datasets-none--model-framework-none--model-framework-version-none--child-paths-none--sample-input-dataset-none--sample-output-dataset-none--resource-configuration-none-) for more details.

### Outputs

| Output        | Description                     |
| ------------- | ------------------------------- |
| model_name    | Name of the registered model    |
| model_version | Version of the registered model |
| model_id      | ID of the registered model      |

### Other Azure Machine Learning Actions

- [aml-workspace](https://github.com/Azure/aml-workspace) - Connects to or creates a new workspace
- [aml-compute](https://github.com/Azure/aml-compute) - Connects to or creates a new compute target in Azure Machine Learning
- [aml-run](https://github.com/Azure/aml-run) - Submits a ScriptRun, an Estimator or a Pipeline to Azure Machine Learning
- [aml-registermodel](https://github.com/Azure/aml-registermodel) - Registers a model to Azure Machine Learning
- [aml-deploy](https://github.com/Azure/aml-deploy) - Deploys a model and creates an endpoint for the model

### Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
