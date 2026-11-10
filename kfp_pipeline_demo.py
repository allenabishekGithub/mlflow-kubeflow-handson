import argparse  # Read command-line options for compilation and local execution.
from kfp import dsl, compiler, local  # Import Kubeflow Pipelines APIs for defining, compiling, and running pipelines.
from kfp.dsl import Dataset, Model, Input, Output  # Import artifact and annotation types used by component interfaces.

# Turn this Python function into a reusable pipeline component.
@dsl.component(
    base_image="python:3.11-slim",  # Use a small Python container to run this component.
    packages_to_install=["scikit-learn==1.5.2", "joblib==1.4.2"],  # Install pinned dependencies in the component container.
)
def generate_data(dataset: Output[Dataset]):
    """Generate a reproducible synthetic dataset and write it as a pipeline artifact."""
    import joblib  # Serialize the feature matrix and labels to the component output file.
    from sklearn.datasets import make_classification  # Generate labeled data for a classification task.

    # Create 600 examples with 10 features; 6 features carry signal and 2 are redundant.
    X, y = make_classification(
        n_samples=600,
        n_features=10,
        n_informative=6,
        n_redundant=2,
        random_state=42,  # Make data generation repeatable across runs.
    )
    joblib.dump((X, y), dataset.path)  # Write both arrays to the Dataset artifact for downstream components.


# Build an isolated containerized component that trains and saves a model.
@dsl.component(
    base_image="python:3.11-slim",  # Run training in the same lightweight Python image.
    packages_to_install=["scikit-learn==1.5.2", "joblib==1.4.2"],  # Install the pinned training dependencies.
)
def train_model(dataset: Input[Dataset], model: Output[Model], c: float):
    """Train logistic regression on the first 480 examples and save the fitted estimator."""
    import joblib  # Read the input artifact and serialize the trained model.
    from sklearn.linear_model import LogisticRegression  # Import the classification algorithm.

    X, y = joblib.load(dataset.path)  # Load the feature matrix and labels from the upstream component.
    estimator = LogisticRegression(C=c, max_iter=1000)  # Configure regularization and the solver iteration limit.
    estimator.fit(X[:480], y[:480])  # Fit using the first 480 examples; the remaining examples are held out.
    joblib.dump(estimator, model.path)  # Write the trained estimator to the Model output artifact.


# Build a component that loads the trained model and measures its held-out accuracy.
@dsl.component(
    base_image="python:3.11-slim",  # Run evaluation in a lightweight Python container.
    packages_to_install=["scikit-learn==1.5.2", "joblib==1.4.2"],  # Install dependencies needed to load and evaluate the model.
)
def evaluate_model(dataset: Input[Dataset], model: Input[Model]) -> float:
    """Return accuracy on the 120 examples not used for training."""
    import joblib  # Deserialize the dataset and trained estimator.
    from sklearn.metrics import accuracy_score  # Calculate the fraction of correct predictions.

    X, y = joblib.load(dataset.path)  # Load all examples and their true labels.
    estimator = joblib.load(model.path)  # Load the model produced by the training component.
    accuracy = accuracy_score(y[480:], estimator.predict(X[480:]))  # Compare predictions on examples 480-599 with their labels.
    print(f"Model Evaluation accuracy: {accuracy:.4f}")  # Show the score in the component's logs.
    return float(accuracy)  # Return a plain Python float as this component's scalar output.


# Define how the data-generation, training, and evaluation components are connected.
@dsl.pipeline(name="synthetic-ml-training-pipeline")
def training_pipeline(c: float = 1.0) -> float:
    generated = generate_data()  # Run the data component; KFP exposes its Dataset output to later tasks.
    trained = train_model(
        dataset=generated.outputs["dataset"],  # Pass the generated data artifact to training.
        c=c,  # Pass the pipeline's regularization setting to the trainer.
    )
    evaluated = evaluate_model(
        dataset=generated.outputs["dataset"],  # Evaluate against the same dataset, using its held-out portion.
        model=trained.outputs["model"],  # Pass the trained model artifact to evaluation.
    )
    return evaluated.output  # Expose the accuracy as the pipeline's result.


# Compile the pipeline definition and then execute it with KFP's local runner when run as a script.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile and optionally run the example KFP pipeline locally.")
    parser.add_argument(
        "--compile-only",
        action="store_true",
        help="Write synthetic-pipeline.yaml without starting a local pipeline run.",
    )
    args = parser.parse_args()
    compiler.Compiler().compile(
        training_pipeline,  # Convert the pipeline into a YAML specification.
        package_path="synthetic-pipeline.yaml",  # Save the compiled pipeline beside this script.
    )
    print("Compiled pipeline to synthetic-pipeline.yaml", flush=True)
    if args.compile_only:
        raise SystemExit(0)

    print(
        "Starting local run. KFP creates temporary environments and installs component packages; "
        "the first run may pause before task logs appear.",
        flush=True,
    )
    local.init(runner=local.SubprocessRunner())  # Configure local execution to run each component in a subprocess.
    result = training_pipeline(c=0.5)  # Execute locally with C=0.5 instead of the pipeline's default of 1.0.
    print(f"Local run completed: accuracy={result.output:.4f}")  # Show the pipeline's scalar result.
