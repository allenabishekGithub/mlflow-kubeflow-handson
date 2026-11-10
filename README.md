# MLOps quickstart: track a classification experiment with MLflow

This folder is a small, local experiment-tracking exercise. `mlflow_ml_demo.py` creates a synthetic binary-classification dataset, trains three logistic-regression models, and sends their parameters, evaluation metrics, and model files to an MLflow tracking server. You run the commands; this guide explains what each step does and what to inspect.

## What is in this folder

| Path | Purpose |
| --- | --- |
| `mlflow_ml_demo.py` | Generates data, trains and evaluates models, and logs three MLflow runs. |
| `requirements.txt` | Exact versions of the third-party packages installed in this project's `.venv`. |
| `start_mlflow_server.sh` | Starts the local MLflow server with this project's existing database and artifacts. |
| `pytorch_dl_demo.py` | Trains a neural network on synthetic circles and logs its training history and model. |
| [`PYTORCH.md`](PYTORCH.md) | Explains the PyTorch run, its first logging error, and how to check the corrected run. |
| `visualize_datasets.py` | Recreates both datasets and saves a three-panel learning plot. |
| [`DATASETS.md`](DATASETS.md) | Explains the plots and how the data connects to each demo. |
| [`K3S_SETUP.md`](K3S_SETUP.md) | K3s installation and group permissions for direct `kubectl` access. |
| [`KFP_PIPELINE.md`](KFP_PIPELINE.md) | Pipeline stages, local execution, and the first interrupted attempt. |
| [`KFP_CLUSTER_RUN.md`](KFP_CLUSTER_RUN.md) | Commands to install standalone KFP on K3s and upload the pipeline YAML. |
| `kfp_pipeline_demo.py` | Defines and compiles the three-step Kubeflow Pipelines example. |
| `synthetic-pipeline.yaml` | Compiled KFP pipeline package produced by the Python script. |
| `.venv/` | Local Python environment; excluded from Git because it is large and machine-specific. Recreate it from `requirements.txt`. |
| `mlflow-data/mlflow.db` | SQLite backend containing experiment and run metadata. |
| `mlflow-data/mlartifacts/` | Files saved by MLflow, including logged models. |
| `local_outputs/` | Artifacts from the completed local KFP run. |

The database, MLflow artifacts, and local KFP outputs were copied from the original quickstart so the recorded results remain available. The `.venv` in this local checkout is a link to the original project's environment; it is ignored by Git. A fresh clone will not contain that link, so create a new `.venv` using the commands below. Keep the database and MLflow artifacts together if you want to retain your experiment history.

For the neural-network exercise, see [PyTorch demo notes](PYTORCH.md). To see the data used by both examples, use the [dataset visualization guide](DATASETS.md). For Kubernetes and the pipeline exercise, use the [K3s setup guide](K3S_SETUP.md), [KFP pipeline notes](KFP_PIPELINE.md), and [KFP cluster run guide](KFP_CLUSTER_RUN.md). The steps below describe the logistic-regression exercise.

## 1. Prepare Python

From this folder, activate an existing environment if you have one:

```bash
cd /home/allen/mlflow-kubeflow-handson
source .venv/bin/activate
```

If you are recreating the exercise in a fresh copy, first create an environment and install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` is a full snapshot of the packages currently installed in `.venv`, including MLflow, PyTorch, KFP, plotting libraries, and their dependencies. It was captured on Ubuntu 22.04 (`x86_64`) with Python 3.10.12. The PyTorch CUDA dependencies make this a large install and may not fit or resolve unchanged on another operating system or CPU architecture. KFP's local subprocess runner still creates temporary component environments when you run its pipeline; this file recreates the project's main `.venv`.

## 2. Start the tracking server

In terminal **A**, run the helper script from the project root:

```bash
cd /home/allen/mlflow-kubeflow-handson
./start_mlflow_server.sh
```

The script uses this project's `.venv` and starts the server in the foreground. Keep the terminal open while you use MLflow, and press **Ctrl+C** to stop it. The command below is the equivalent manual setup used in the recorded exercise:

```bash
cd /home/allen/mlflow-kubeflow-handson/mlflow-data
source ../.venv/bin/activate
mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlflow.db
```

The server provides both the web UI and the API used by the script. Because the command runs **inside `mlflow-data`**, `sqlite:///mlflow.db` points to `mlflow-data/mlflow.db`. Model files go under `mlflow-data/mlartifacts/`. The existing experiment uses MLflow's artifact proxy (`mlflow-artifacts:/`), so starting the server from this same directory keeps the database and artifact paths aligned. Open <http://localhost:5000> in your browser.

## 3. Run the experiment

In terminal **B**, run the script from the project root:

```bash
cd /home/allen/mlflow-kubeflow-handson
source .venv/bin/activate
python mlflow_ml_demo.py
```

The script connects to `http://localhost:5000`, so the server must be running on port 5000. It prints one line for each `C` value: `0.01`, `0.1`, and `1.0`. Each execution adds **three new runs** to the `synthetic-classification-ml` experiment. It does not overwrite earlier runs. If you have already run the script and only want to inspect its results, start the server and skip this step.

## 4. Inspect and explain the results

In the MLflow UI, open **Experiments → synthetic-classification-ml**. Compare the three runs named `logreg-C-0.01`, `logreg-C-0.1`, and `logreg-C-1.0`:

1. **Parameters:** `C` is the logistic-regression regularization setting. A smaller `C` means stronger regularization. `n_samples` should be `1000` for every run.
2. **Metrics:** `accuracy` is the share of test predictions that are correct. `f1_score` combines precision and recall; a higher value is better for this binary-classification task.
3. **Model:** Open a run's logged `classifier` model to see the model files and environment information. The trained model is an artifact, while scores and settings are run metadata.

The existing database contains these three completed runs, recorded on **2026-11-09 (UTC)**. The scores below match the script's output:

| `C` | Accuracy | F1 score | Correct test predictions | Observation |
| ---: | ---: | ---: | ---: | --- |
| 0.01 | 0.710 | 0.7040816326530612 | 142 of 200 | Tied for highest accuracy. |
| 0.1 | 0.710 | 0.7070707070707071 | 142 of 200 | Highest F1 score; tied for highest accuracy. |
| 1.0 | 0.705 | 0.700507614213198 | 141 of 200 | Lower on both recorded metrics. |

### What `C`, accuracy, and F1 mean

**`C` controls regularization.** Logistic regression learns weights for the input features. Regularization discourages the model from relying on very large weights, which can help it avoid fitting noise in the training data. `C` is the *inverse* of regularization strength: `0.01` applies the strongest regularization here, `0.1` is in the middle, and `1.0` applies the weakest. `C` is a setting chosen **before** training, not a score; a larger value is not automatically better.

**Accuracy counts all correct predictions.** It is `(correct predictions) / (all test examples)`. For this 200-example test set, accuracy `0.710` means `142 / 200` were correct and 58 were wrong. Accuracy `0.705` means `141 / 200` were correct.

**F1 describes how well the model finds class `1`.** Precision asks, “Of the examples predicted as class `1`, how many really were `1`?” Recall asks, “Of the actual class `1` examples, how many did the model find?” F1 combines the two as `2 × precision × recall / (precision + recall)`. It ranges from `0` (worst) to `1` (best). An F1 of `0.707` does **not** mean 70.7% of all predictions were correct; accuracy answers that question. Models can have equal accuracy but different F1 scores when their mistakes are distributed differently between the classes.

**Interpretation:** `C=0.1` has the highest F1 in these runs and ties `C=0.01` on accuracy. The differences are small: `C=1.0` gets only one fewer test example correct. This shows performance on this particular split, not a guarantee that `C=0.1` will always win on new data.

### What the terminal output confirms

- `Experiment ... does not exist. Creating a new experiment` and the server's initial `404 Not Found` are normal for the first run. The next request created `synthetic-classification-ml` successfully (`200 OK`).
- Three `C=...` lines and three run links mean the script completed one run for each regularization setting. The run links open the individual records in the UI.
- `POST .../log-parameter`, `POST .../log-metric`, and `PUT .../model.skops` with `200 OK` show that the settings, scores, and model files reached the server. The final run updates also returned `200 OK`.
- The `StarletteDeprecationWarning` concerns a library used by the MLflow server. It did not stop this run: the server started and the logging requests succeeded.

## How the script works

1. `make_classification` generates 1,000 labeled examples with 12 features. `random_state=42` makes the generated data repeatable.
2. `train_test_split` reserves 20% (200 examples) for evaluation and uses stratification to preserve the class balance. The remaining 800 examples train each model.
3. The loop fits one `LogisticRegression` model per `C` value. Each `with mlflow.start_run(...)` block creates one run and closes it when the block ends.
4. `mlflow.log_param` records inputs to the experiment; `mlflow.log_metric` records evaluation scores; `mlflow.sklearn.log_model` saves the fitted model.

### What happened when you ran the two commands

1. **The `mlflow server` command started a local service.** It opened a web UI and API at `http://127.0.0.1:5000`, initialized `mlflow-data/mlflow.db` on its first start, and used `mlflow-data/mlartifacts/` for model files. The server waited for requests; it did not train a model.
2. **The Python script prepared data in memory.** It generated 1,000 synthetic examples, then split them into 800 training examples and 200 test examples. It did not download a dataset or save the generated dataset to a file.
3. **The script connected to the server.** `mlflow.set_tracking_uri("http://localhost:5000")` directed its MLflow calls to that local service. `mlflow.set_experiment("synthetic-classification-ml")` asked for the experiment. Because it did not exist yet, MLflow created it; that explains the initial `404` followed by a successful create request.
4. **The script trained and recorded three models.** It trained logistic regression separately with `C=0.01`, `0.1`, and `1.0`. Each model used the same training and test split. For each run, it sent `C`, `n_samples`, accuracy, and F1 to the server, then uploaded the fitted model and its environment files. The server returned `200 OK` for these writes.
5. **The results remained available after the script exited.** MLflow closed each run as finished. The database holds the experiment, run names, parameters, and metrics; `mlartifacts/` holds the model files. The terminal printed the scores and links, and the UI reads the same saved results. You can stop and restart the server using the same directory and database to view them again.

The data flow was: **Python script → MLflow API on port 5000 → SQLite metadata and model artifacts → MLflow UI**.

This is **experiment tracking**, one part of MLOps. The script does not deploy a model or monitor predictions in production. Also, choosing `C` using the same test set makes that set part of model selection; a larger project would use a separate validation set and keep the test set for a final unbiased evaluation.

## If something goes wrong

| Symptom | Check |
| --- | --- |
| Connection refused at `localhost:5000` | Start the server in terminal A and leave it running while the script runs. |
| `ModuleNotFoundError` | Activate `.venv` in the terminal running the command, or install the dependencies above. |
| UI shows no expected experiment | Start the server from `mlflow-data` with the backend URI above, then run the script from the project root. A plain `mlflow server` in another directory can open a different database. |
| Port 5000 is already in use | Stop the other process using it, or change both the server's `--port` and the URL in `mlflow_ml_demo.py` to the same new port. |

## References

- [MLflow Tracking Quickstart](https://mlflow.org/docs/latest/ml/getting-started/quickstart/)
- [MLflow Tracking Server](https://mlflow.org/docs/latest/self-hosting/architecture/tracking-server/)
- [scikit-learn `LogisticRegression` (`C`)](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html)
- [scikit-learn accuracy score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html)
- [scikit-learn F1 score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html)
