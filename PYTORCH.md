# PyTorch circles demo: run notes

`pytorch_dl_demo.py` trains a small neural network to classify points in two noisy concentric circles. It sends its training history and saved model to the same local MLflow server used by the logistic-regression demo. Run the server from `mlflow-data` as shown in [README.md](README.md), then run this script from the project root:

```bash
cd /home/allen/mlflow-kubeflow-handson
source .venv/bin/activate
python3 pytorch_dl_demo.py
```

This uses Python 3 from `.venv`; installing Python 2 is unrelated to this script.

## What the script does

1. `make_circles` generates 1,200 labeled points. The script keeps 960 for training and 240 for testing.
2. `StandardScaler` learns scaling values from the training features only, then applies the same transformation to training and test features.
3. `CircleNet` takes two coordinates, passes them through two 16-unit hidden layers with ReLU activations, and outputs two class scores. Adam updates the weights for 50 epochs using cross-entropy loss.
4. At every epoch, the script sends `training_loss` and `test_accuracy` to MLflow. It prints progress every 10 epochs. After training, it saves the network as a logged model.

An **epoch** is one pass through the training examples. `training_loss` measures how far the model's training predictions are from the labels; lower is better for this loss. `test_accuracy` is the fraction of the 240 held-out examples predicted correctly. A falling training loss and rising test accuracy show that this run learned the circle pattern, although a single test split cannot establish performance on all future data.

## First attempt: training succeeded, model logging failed

The run on **2026-11-09 at 13:31 UTC** created the `synthetic-circles-pytorch` experiment and recorded 50 epochs of metrics. The reported checkpoints were:

| Epoch | Training loss | Test accuracy | Approximate correct test predictions |
| ---: | ---: | ---: | ---: |
| 10 | 0.6081 | 0.8167 | 196 of 240 |
| 20 | 0.4152 | 0.9792 | 235 of 240 |
| 30 | 0.1725 | 0.9875 | 237 of 240 |
| 40 | 0.0647 | 0.9958 | 239 of 240 |
| 50 | 0.0362 | 0.9958 | 239 of 240 |

The accuracy values in the terminal are rounded to four decimals, so the counts above are inferred from the 240-example test set. MLflow recorded the final unrounded `test_accuracy` as about `0.995833` and the final `training_loss` as about `0.036206`.

After epoch 50, `mlflow.pytorch.log_model` raised an exception because this MLflow installation defaults to PyTorch's `pt2` serialization format. `pt2` traces the network by calling `forward` with an example input, and the original script did not provide `input_example`. The run is marked **FAILED** in MLflow even though training and metric logging finished. Its metrics remain available; the model was not successfully saved in that attempt. The run link printed before the traceback points to this failed run.

## Fix and successful rerun

The script now passes a two-row, `float32` input example from the scaled training data to `mlflow.pytorch.log_model`. It also records a signature describing two input features and two output scores, and selects `serialization_format="pt2"` explicitly. The two-row example lets the exporter represent the batch size as variable.

The rerun on **2026-11-09 at 13:42 UTC** created a separate run in the same experiment. It did not overwrite the failed attempt. The new run (`d1266fb33d5d4156b24dea95f85e8972`) is **FINISHED**. The local MLflow database contains 50 `training_loss` values and 50 `test_accuracy` values, at steps 0 through 49. Its final values are `training_loss=0.036205749958753586` and `test_accuracy=0.9958333373069763` (239 of 240 correct). These match the first attempt's training results.

The server returned `200 OK` for creating the run, logging the metrics, uploading `data/model.pt2`, and updating the run. The saved model directory also contains `MLmodel`, `input_example.json`, `serving_input_example.json`, and environment files. This verifies that model export and upload succeeded. The model has not yet been loaded back for an inference check.

### Reading the successful server log

| Log entry from the rerun | What it confirms |
| --- | --- |
| `GET .../experiments/get-by-name` → `200 OK` | The existing `synthetic-circles-pytorch` experiment was found. |
| `POST .../runs/create` → `200 OK` | A new run was created. |
| Repeated `POST .../runs/log-metric` → `200 OK` | The loss and accuracy values were recorded during training. The database has 50 values of each metric. |
| `POST .../logged-models` and `POST .../runs/outputs` → `200 OK` | MLflow created a logged-model record and linked it to this run. |
| `PUT .../data/model.pt2` → `200 OK` | The exported PyTorch model file was uploaded. The example inputs, signature metadata, and environment files were uploaded too. |
| `PATCH .../logged-models` and `POST .../runs/update` → `200 OK` | MLflow updated the model and run after the upload. The run's stored status is `FINISHED`. |

The terminal returned to the shell prompt without a traceback, which is consistent with the stored `FINISHED` status. The run link in that output opens the successful run: <http://localhost:5000/#/experiments/2/runs/d1266fb33d5d4156b24dea95f85e8972>.

Open **Experiments → synthetic-circles-pytorch** in the MLflow UI. You should see both the older **FAILED** run, whose metrics were saved before model logging failed, and the newer **FINISHED** run with the `circle_net` model.

## MLOps meaning

The server recorded a useful partial result even when model saving failed: you can inspect the hyperparameters and metric history for that attempt. A complete tracked run also stores the model so it can be loaded later. This exercise logs experiments; it does not deploy the neural network. The script evaluates the same test set after every epoch; if those scores guide epoch selection or tuning, that set becomes validation data. A larger project would reserve a separate final test set.

See [MLflow's PyTorch model API](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.pytorch.html) for the `pt2` input example requirement.
