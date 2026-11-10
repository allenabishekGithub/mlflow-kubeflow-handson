import mlflow  # Provides MLflow tracking APIs for experiments, runs, parameters, and metrics.
import mlflow.sklearn  # Provides MLflow helpers for logging scikit-learn models.
from sklearn.datasets import make_classification  # Imports a helper that generates a synthetic classification dataset.
from sklearn.linear_model import LogisticRegression  # Imports a linear model suitable for classification problems.
from sklearn.metrics import accuracy_score, f1_score  # Imports functions that measure prediction performance.
from sklearn.model_selection import train_test_split  # Imports a helper to split data into training and test sets.

mlflow.set_tracking_uri("http://localhost:5000")  # Sends MLflow tracking data to the local server at this address.
mlflow.set_experiment("synthetic-classification-ml")  # Groups this script's runs under the named experiment.

# Create 1,000 synthetic examples with 12 input features and binary classification labels.
X, y = make_classification(
    n_samples=1000,  # Number of examples to generate.
    n_features=12,  # Number of input values (columns) in each example.
    n_informative=8,  # Number of features that contribute useful information about the label.
    n_redundant=2,  # Number of features that are derived from informative features.
    random_state=42,  # Fixes the random seed so the same dataset is generated each time.
)
# Split features and labels into training and test sets; 20% is reserved for testing.
X_train, X_test, y_train, y_test = train_test_split(
    X,  # Full feature matrix.
    y,  # Labels corresponding to the rows in X.
    test_size=0.2,  # Use 20% of the examples for evaluation and 80% for training.
    stratify=y,  # Preserve the label proportions in both splits.
    random_state=42,  # Make the split reproducible.
)

# Train and evaluate one model for each listed regularization strength.
for c in [0.01, 0.1, 1.0]:
    # Start a separate MLflow run; its context automatically ends when this block exits.
    with mlflow.start_run(run_name=f"logreg-C-{c}"):
        model = LogisticRegression(C=c, max_iter=1000)  # Configure logistic regression with this C and iteration limit.
        model.fit(X_train, y_train)  # Learn model parameters from the training features and labels.
        predicted = model.predict(X_test)  # Predict labels for the held-out test features.
        mlflow.log_param("C", c)  # Record the regularization strength used for this run.
        mlflow.log_param("n_samples", len(X))  # Record the total number of generated examples.
        # Calculate accuracy (fraction correct) and record it as a metric for this run.
        mlflow.log_metric(
            "accuracy",  # Name under which the metric is stored.
            accuracy_score(y_test, predicted),  # Compare predicted labels with the true test labels.
        )
        # Calculate the F1 score (balance of precision and recall) and record it for this run.
        mlflow.log_metric(
            "f1_score",  # Name under which the metric is stored.
            f1_score(y_test, predicted),  # Calculate F1 from the true and predicted test labels.
        )
        mlflow.sklearn.log_model(model, name="classifier")  # Save the trained model as an artifact in this run.
        # Print the settings and scores so they are also visible in the terminal.
        print(
            f"C={c}, accuracy={accuracy_score(y_test, predicted):.3f}, "
            f"f1_score={f1_score(y_test, predicted)}"
        )