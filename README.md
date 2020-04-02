![Integration Test](https://github.com/Azure/aml-registermodel/workflows/Integration%20Test/badge.svg)
![Lint](https://github.com/Azure/aml-registermodel/workflows/Lint/badge.svg)

# Azure Machine Learning Register Model Action

The Azure Machine Learning Register Model action will register your model on AML for use in deployment and testing. This action is designed to only register the model that corresponds to the run reporting the highest metrics. This can be overruled by passing the `force_registration` as true. You will need to have azure credentials that allow you to connect to a workspace, view experiment or pipeline runs and register a model.

This action requires an AML workspace to be created or attached to via the [aml-workspace](https://github.com/Azure/aml-workspace) action as well as model that can be either trained via the [aml-run](https://github.com/Azure/aml-run) action or supplied directly.

This action is one in a series of actions that are used to make ML Ops systems. Examples of these can be found at [ml-template-azure](https://github.com/machine-learning-apps/ml-template-azure) and [aml-template](https://github.com/Azure/aml-template).

## Usage

Description

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
    - uses: Azure/aml-run
      id: aml_run
      with:
        # required inputs as secrets
        azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
        # optional
        parameters_file: "run.json"

    # AML Register Model Action
    - uses: Azure/aml-registermodel
      id: aml_registermodel
      with:
        # required inputs as secrets
        azure_credentials: ${{ secrets.AZURE_CREDENTIALS }}
        # optional
        parameters_file: "registermodel.json"
```

### Inputs

| Input | Required | Default | Description |
| ----- | -------- | ------- | ----------- |
| azure_credentials | x | - | Output of `az ad sp create-for-rbac --name <your-sp-name> --role contributor --scopes /subscriptions/<your-subscriptionId>/resourceGroups/<your-rg> --sdk-auth`. This should be stored in your secrets |
| parameters_file |  | `"registermodel.json"` | JSON file in the `.ml/.azure` folder specifying your Azure Machine Learning model registration details. |

#### Azure Credentials

Install the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest) and execute the following command to generate the credentials:

```sh
# Replace {service-principal-name}, {subscription-id} and {resource-group} with your Azure subscription id and resource group and any name
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

Add the JSON output as [a secret](https://help.github.com/en/actions/configuring-and-managing-workflows/creating-and-storing-encrypted-secrets#creating-encrypted-secrets) with the name `AZURE_CREDENTIALS` in the GitHub repository.

#### Parameters File

The action expects a JSON file in the `.ml/.azure` folder in your repository, which specifies details for the model registration to your Azure Machine Learning Workspace. By default, the action expects a file with the name `registermodel.json`. If your JSON file has a different name, you can specify it with this parameter.

A sample file can be found in this repository in the folder `.ml/.azure`. The JSON file can include the following parameters:

| Parameter               | Required | Allowed Values | Default    | Description |
| ----------------------- | -------- | -------------- | ---------- | ----------- |
| workspace               |          |                |            |             |
| model_file_name         | x        | str            |            |The file name for the model asset on the local system. 
| model_name              |          | str            | REPO_NAME-BRANCH_NAME |The name to register the model with.|
| model_framework         |          | str: `"scikitlearn"`, `"onnx"`, `"tensorflow"`, `"keras"`, `"custom"` | `"custom"` | The framework of the registered model. Using the system-supported constants from the Framework class allows for simplified deployment for some popular frameworks. | 
| model_framework_version |          | str      |      | The framework version of the registered model. |
| model_tags              |          | dict  | | An optional dictionary of key value tags to assign to the model. |
| model_properties        |          | dict  | | An optional dictionary of key value properties to assign to the model. These properties can't be changed after model creation, however new key value pairs can be added. |
| model_description       |          | str   | | A text description of the model. |
| datasets                |          | list  | | A list of tuples where the first element describes the dataset-model relationship and the second element is the dataset. |
| sample_input_dataset    |          | str   | | Sample input dataset for the registered model. |
| sample_output_dataset   |          | str   | | Sample output dataset for the registered model. |
| cpu                     |          | float | | The cpu requirements for the model |
| memory                  |          | float | | The memory requirements for the model |
| pipeline_child_run_name |          | str   | | Used for fetching the best run  |
| metrics_max             |          | list  | | For comparing metrics |
| metrics_min             |          | list  | | For comparing metrics |
| force_registration      |          | bool  | | Boolean value that determines whether or not to force the registration of the model regardless of the metrics |

# Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.


# TODO

- support different dataset versions
