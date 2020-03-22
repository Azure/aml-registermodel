from azureml.core import Model, Dataset
from azureml.train.hyperdrive import HyperDriveRun
from azureml.pipeline.core import PipelineRun
from azureml.exceptions import WebserviceException


class AMLConfigurationException(Exception):
    pass


class AMLModelPerformanceException(Exception):
    pass


def required_parameters_provided(parameters, keys, message="Required parameter not found in your parameters file. Please provide a value for the following key(s): "):
    missing_keys = []
    for key in keys:
        if key not in parameters:
            err_msg = f"{message} {key}"
            print(f"::error::{err_msg}")
            missing_keys.append(key)
    if len(missing_keys) > 0:
        raise AMLConfigurationException(f"{message} {missing_keys}")


def get_best_run(experiment, run, pipeline_child_run_name=None):
    # Handle pipeline run
    print("::debug::Handling pipeline run")
    if run.type == "azureml.PipelineRun":
        # Loading pipeline run
        run = PipelineRun(
            experiment=experiment,
            run_id=run.id
        )

        # Loading pipeline step by name
        run = run.find_step_run(name=pipeline_child_run_name)
        if len(run) < 1:
            print(f"::error::Found no step in the pipeline with the name '{pipeline_child_run_name}'")
            raise AMLConfigurationException(f"Found more than one step in the pipeline with the name '{pipeline_child_run_name}'")
        elif len(run) > 1:
            print(f"::error::Found more than one step in the pipeline with the name '{pipeline_child_run_name}'. All step names should be unique in the pipeline.")
            raise AMLConfigurationException(f"Found more than one step in the pipeline with the name '{pipeline_child_run_name}'. All step names should be unique in the pipeline.")
        else:
            run = run[0]

        # Checking if run has childs and therefore is a hyperparameter run
        if len(list(run.get_children())) > 0:
            run = list(run.get_children())[0]

    # Handle hyperdrive run
    print("::debug::Handling hyperdrive run")
    if run.type == "hyperdrive":
        run = HyperDriveRun(
            experiment=experiment,
            run_id=run.id
        )
        best_run = run.get_best_run_by_primary_metric()
    else:
        best_run = run
    return best_run


def get_dataset(workspace, name):
    try:
        dataset = Dataset.get_by_name(
            workspace=workspace,
            name=name,
            version="latest"
        )
    except Exception:
        dataset = None
    return dataset


def get_model_framework(name):
    if name.lower() == "scikitlearn":
        model_framework = Model.Framework.SCIKITLEARN
    elif name.lower() == "onnx":
        model_framework = Model.Framework.ONNX
    elif name.lower() == "tensorflow":
        model_framework = Model.Framework.TENSORFLOW
    elif name.lower() == "keras":
        model_framework = Model.Framework.TFKERAS
    else:
        model_framework = Model.Framework.CUSTOM
    return model_framework


def compare_metrics(workspace, run, model_name, metrics_max, metrics_min):
    # Loading production model
    print("::debug::Loading production model")
    try:
        production_model = Model(
            workspace=workspace,
            name=model_name
        )
    except WebserviceException as exception:
        print(f"::debug::Model with same name not found. Assuming that it is the first model that is registered: {exception}")
        return

    # Loading run of production model
    print("::debug::Loading run of production model")
    production_model_run = production_model.run
    if run is None:
        print("::debug::Previous model was not registered from run object")
        return

    # Loading metrics of runs
    production_model_metrics = production_model_run.get_metrics()
    run_metrics = run.get_metrics()

    # Comparing metrics to maximize
    print("::debug::Comparing metrics to maximize")
    for metric_max in metrics_max:
        try:
            if run_metrics.get(metric_max) < production_model_metrics.get(metric_max):
                print(f"::error::New model does not perform better than production model for metric '{metric_max}'")
                raise AMLModelPerformanceException(f"New model does not perform better than production model for metric '{metric_max}'")
        except TypeError as exception:
            print(f"::error::Metric comparison failed for metric name '{metric_max}': {exception}")
            raise AMLConfigurationException(f"::error::Metric comparison failed for metric name '{metric_max}'")

    # Comparing metrics to minimize
    print("::debug::Comparing metrics to minimize")
    for metric_min in metrics_min:
        try:
            if run_metrics.get(metric_min) < production_model_metrics.get(metric_min):
                print(f"::error::New model does not perform better than production model for metric '{metric_min}'")
                raise AMLModelPerformanceException(f"New model does not perform better than production model for metric '{metric_min}'")
        except TypeError as exception:
            print(f"::error::Metric comparison failed for metric name '{metric_min}': {exception}")
            raise AMLConfigurationException(f"::error::Metric comparison failed for metric name '{metric_min}'")
