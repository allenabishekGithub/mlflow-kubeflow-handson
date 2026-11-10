import mlflow  # Provides APIs for recording model experiments and their results.
import mlflow.pytorch  # Provides MLflow support for logging and managing PyTorch models.
from mlflow.models import infer_signature  # Describes the model's input and output tensor shapes.
import torch  # Imports PyTorch for tensors and neural-network training.
from torch import nn  # Imports PyTorch's neural-network layers and base Module class.
from sklearn.datasets import make_circles  # Imports a helper to generate a two-class circular dataset.
from sklearn.model_selection import train_test_split  # Imports a helper to split data into training and test sets.
from sklearn.preprocessing import StandardScaler  # Imports a tool to standardize feature values.

torch.manual_seed(42)  # Fixes PyTorch's random seed to make model initialization reproducible.
# Generate 1,200 two-dimensional examples arranged in noisy concentric circles.
X, y = make_circles(n_samples=1200, noise=0.12, factor=0.45, random_state=42)
# Split features and labels into training and test sets, keeping class proportions balanced.
X_train, X_test, y_train, y_test = train_test_split(
    X,  # Feature coordinates for all generated examples.
    y,  # Class label for each example.
    test_size=0.2,  # Reserve 20% of the examples for testing.
    stratify=y,  # Preserve the label proportions in both subsets.
    random_state=42,  # Make the split reproducible.
)
# Fit normalization statistics using only the training features to avoid test-data leakage.
scaler = StandardScaler().fit(X_train)
# Normalize training features and convert them to 32-bit floating-point PyTorch values.
X_train = torch.tensor(scaler.transform(X_train), dtype=torch.float32)
# Apply the training-fitted normalization to test features and convert them to tensors.
X_test = torch.tensor(scaler.transform(X_test), dtype=torch.float32)
# Convert training labels to integer tensors, as expected by common classification losses.
y_train = torch.tensor(y_train, dtype=torch.long)
# Convert test labels to integer tensors for evaluation.
y_test = torch.tensor(y_test, dtype=torch.long)

# Define a fully connected neural network for classifying the two-dimensional points.
class CircleNet(nn.Module):
    # Initialize the network's layers.
    def __init__(self):
        super().__init__()  # Initialize the parent PyTorch Module.
        # Chain two hidden layers with ReLU activations and a two-value output layer.
        self.layers = nn.Sequential(
            nn.Linear(2, 16),  # Map the two input features to 16 hidden units.
            nn.ReLU(),  # Apply a nonlinear activation to the first hidden layer.
            nn.Linear(16, 16),  # Map the first hidden representation to 16 more units.
            nn.ReLU(),  # Apply a nonlinear activation to the second hidden layer.
            nn.Linear(16, 2),  # Produce one output score for each of the two classes.
        )

    # Define how input feature batches pass through the network.
    def forward(self, inputs):
        return self.layers(inputs)  # Return the two output scores produced for each input.

mlflow.set_tracking_uri("http://localhost:5000")  # Send MLflow tracking data to the local server.

mlflow.set_experiment("synthetic-circles-pytorch")
net = CircleNet()  # Create an instance of the CircleNet model.
optimizer = torch.optim.Adam(net.parameters(), lr=0.01)  # Use Adam to update the model's weights.
criterion = nn.CrossEntropyLoss()  # Use cross-entropy loss for the two-class classification task.

with mlflow.start_run(run_name="circles-mlp-50-epochs"):
    mlflow.log_params({"epochs": 50, "learning_rate": 0.01, "hidden_units": 16, "dataset": "circles"})  # Record the training hyperparameters.

    for epoch in range(50):
        net.train()  # Put the model in training mode (enables dropout, batch norm, etc.).
        optimizer.zero_grad()  # Clear any previously computed gradients.
        logits = net(X_train)  # Compute the model's output scores for the training features.
        loss = criterion(logits, y_train)  # Compute the loss between predicted scores and true labels.
        loss.backward()  # Compute gradients of the loss with respect to model parameters.
        optimizer.step()  # Update the model's parameters using the computed gradients.

        net.eval()  # Put the model in evaluation mode (disables dropout, batch norm, etc.).
        with torch.no_grad():  # Disable gradient computation for evaluation.
            test_logits = net(X_test)
            accuracy = (test_logits.argmax(1) == y_test).float().mean().item()  # Compute the accuracy on the test set.
        mlflow.log_metric("training_loss", float(loss.item()), step=epoch)  # Log the training loss for this epoch.
        mlflow.log_metric("test_accuracy", accuracy, step=epoch)  # Log the test accuracy for this epoch.
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch + 1}: loss={loss.item():.4f}, test_accuracy={accuracy:.4f}")  # Print progress every 10 epochs.
    # MLflow's pt2 format traces the network with a real input batch; use two rows so
    # the exported model can accept batches of different sizes later.
    input_example = X_train[:2].numpy()
    with torch.no_grad():
        output_example = net(X_train[:2]).numpy()
    signature = infer_signature(input_example, output_example)
    mlflow.pytorch.log_model(
        net,
        name="circle_net",
        input_example=input_example,
        signature=signature,
        serialization_format="pt2",
    )  # Save the trained model and its input/output contract to MLflow.
