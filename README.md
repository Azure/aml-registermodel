![Integration Test](https://github.com/Azure/aml-registermodel/workflows/Integration%20Test/badge.svg)
![Lint](https://github.com/Azure/aml-registermodel/workflows/Lint/badge.svg)

# Azure Machine Learning Register Model Action

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

| Parameter               | Required | Allowed Values       | Default               | Description |
| ----------------------- | -------- | -------------------- | --------------------- | ----------- |
| model_name              |          | str                  | REPO_NAME-BRANCH_NAME |
| model_file_name         | x        | str                  |                       |
| model_framework         |          | str: `"scikitlearn"`, `"onnx"`, `"tensorflow"`, `"keras"`, `"custom"` | `"custom"` | 
| model_framework_version |          | str
| model_tags              |          | dict
| model_properties        |          | dict
| model_description       |          | str
| datasets                |          | list
| sample_input_dataset    |          | str
| sample_output_dataset   |          | str
| cpu                     |          | float
| memory                  |          | float
| pipeline_child_run_name |          | str
| metrics_max             |          | list
| metrics_min             |          | list
| force_registration      |          | bool

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


# Todo

- support different dataset versions