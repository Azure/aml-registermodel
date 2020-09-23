![Integration Test](https://github.com/Azure/aml-registermodel/workflows/Integration%20Test/badge.svg?branch=master&event=push)
![Lint and Test](https://github.com/Azure/aml-registermodel/workflows/Lint%20and%20Test/badge.svg?branch=master&event=push)

# GitHub Action for Registering a Machine Learning Model in Azure

## Usage

The Register Machine Learning Models with Azure action will deploy your model on [Azure Machine Learning](https://azure.microsoft.com/en-us/services/machine-learning/) using GitHub Actions.

Get started today with a [free Azure account](https://azure.com/free/open-source)!

This repository contains a GitHub Action for registering Machine Learning Models with Azure Machine Learning model registry for use in deployment and testing. This action is designed to register models that may or may not have been trained using Azure Machine Learning. If they are not trained using Azure Machine Learning, we expect the model to be present in your GitHub Repository.

Additionally, this action also supports model comparison, if the model has been created by an Azure Machine Learning (pipeline) run and is not stored in your repository. This GitHub Action allows you to define metrics that will be compared with the latest model that is registered under the same name and the newly trained model will only be registered, if it performs better for all specified metrics. For more details look in the `parameters_file` section below.


## Dependencies on other GitHub Actions
* [Checkout](https://github.com/actions/checkout) Checkout your Git repository content into GitHub Actions agent.
* [aml-workspace](https://github.com/Azure/aml-workspace) This action requires an Azure Machine Learning workspace to be present. You can either create a new one or re-use an existing one using the action. 


## Utilize GitHub Actions and Azure Machine Learning to train and deploy a machine learning model

This action is one in a series of actions that can be used to setup an ML Ops process. **We suggest getting started with one of our template repositories**, which will allow you to create an ML Ops process in less than 5 minutes.

1. **Simple template repository: [ml-template-azure](https://github.com/machine-learning-apps/ml-template-azure)**

    Go to this template and follow the getting started guide to setup an ML Ops process within minutes and learn how to use the Azure Machine Learning GitHub Actions in combination. This template demonstrates a very simple process for training and deploying machine learning models.

2. **Advanced template repository: [mlops-enterprise-template](https://github.com/Azure-Samples/mlops-enterprise-template)**

    This template demonstrates how the actions can be extended to include the normal pull request approval process and how training and deployment workflows can be split. More enhancements will be added to this template in the future to make it more enterprise ready.

## Example workflow for registering a Machine Learning Model in Azure


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
| experiment_name |  | - | Experiment name to which the run belongs to. This input is required, if you want to register a model that is stored in the outputs of an AML (pipeline) run. This is not required, if the model is stored in your repository. |
| run_id |  | - | ID of the run or pipeline run for which a model is to be registered. This input is required, if you want to register a model that is stored in the outputs of an AML (pipeline) run. This is not required, if the model is stored in your repository. |
| parameters_file |  | `"registermodel.json"` | We expect a JSON file in the `.cloud/.azure` folder in root of your repository specifying your Azure Machine Learning model registration details. If you have want to provide these details in a file other than "registermodel.json" you need to provide this input in the action. |

#### azure_credential (Azure Credentials)

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

#### experiment_name (Experiment Name)

This action input defines the experiment name to which the run with the ID `run_id` belongs to. This run must have created a model file with the name `model_file_name` (defined in the input file). The model file will be registered in the model registry in Azure Machine Learning by this action.
If this input is not defined, the action will try to find a model file with the name `model_file_name` (defined in the parameters file) in your GitHub repository. If the model file is available in your repository, it will be registered in the Azure Machine Learning model registry.

#### run_id (Run ID)

This action input defines the run, which created a model file with the name `model_file_name` (defined in the parameters file). The model file will be registered in the model registry in Azure Machine Learning by this action.
If this input is not defined, the action will try to find a model file with the name `model_file_name` (defined in the parameters file) in your GitHub repository. If the model file is available in your repository, it will be registered in the Azure Machine Learning model registry.

#### parameters_file (Parameters File)

The action tries to load a JSON file in the `.cloud/.azure` folder in your repository, which specifies details for the model registration to your Azure Machine Learning Workspace. By default, the action is looking for a file with the name `registermodel.json`. If your JSON file has a different name, you can specify it with this parameter. Note that none of these values are required and in the absence, defaults will be used.

A sample file can be found in this repository in the folder `.cloud/.azure`. The JSON file can include the following parameters:

| Parameter               | Required | Allowed Values | Default    | Description |
| ----------------------- | -------- | -------------- | ---------- | ----------- |
| model_file_name         |          | str            | `"model.pkl"` | The file name of the model asset that is stored in the outputs of the specified run (action input) in Azure Machine Learning or present in your GitHub repository. You only have to specify the name of the model file (e.g. (`"model.pkl"`)) and not the path (e.g. `"outputs/model.pkl"`). The action can take care of the path that was used to store the file. You can also specify the path, if you want to. If you want to register an entire folder, then just specify the folder with this parameter. |
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
