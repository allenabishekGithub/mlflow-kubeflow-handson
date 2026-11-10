# Run the compiled pipeline on K3s

The file [`synthetic-pipeline.yaml`](synthetic-pipeline.yaml) is a **Kubeflow Pipelines (KFP) pipeline package**. It describes the three tasks and their inputs and outputs. It is not a Kubernetes Pod or Deployment manifest, so `kubectl apply -f synthetic-pipeline.yaml` will not submit the pipeline. Install the KFP backend on K3s, then upload the YAML to that backend and start a run. The KFP backend creates the Kubernetes workloads.

These are commands for **you to run** on the `allen` machine. The documented local pipeline run did not install KFP on K3s, and a cluster run has not yet been recorded here.

## 1. Check the existing cluster

```bash
kubectl get nodes
kubectl get pods -A
kubectl get service -n kubeflow ml-pipeline-ui
df -h /
free -h
```

The last recorded K3s check showed one `Ready` node, `allen`, but no KFP installation. If `kubectl get service` says namespace or service `NotFound`, that is expected before installing KFP. The machine had about 12 GiB free on `/` and 9 GiB available RAM at the earlier check. KFP will download several images and store data, so check those numbers again before installation.

## 2. Install standalone KFP on K3s

Use KFP **2.18.0**, the version installed in this project's `.venv` and embedded in the compiled components. From a terminal with working `kubectl` access:

```bash
export PIPELINE_VERSION=2.18.0
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
kubectl wait --for=condition=established --timeout=120s crd/applications.app.k8s.io
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic?ref=$PIPELINE_VERSION"
```

The first command creates the `kubeflow` namespace and cluster-wide resources. The second waits for the Application custom resource definition. The final command creates the standalone KFP services, workflow controller, database, and artifact storage. This uses the release's `platform-agnostic` manifest: the official installation guide uses an `env/dev` overlay for first experiments, but that overlay replaces several released images with `master` tags. The `platform-agnostic` overlay keeps the KFP images pinned to the release version. This is a choice based on the [2.18.0 manifests](https://github.com/kubeflow/pipelines/tree/2.18.0/manifests/kustomize), rather than a claim that this exact setup has already been tested on this machine.

Let the workloads start, then inspect them:

```bash
kubectl get deployments -n kubeflow
kubectl get pods -n kubeflow
kubectl get service -n kubeflow ml-pipeline-ui
kubectl rollout status -n kubeflow deployment/ml-pipeline --timeout=600s
kubectl rollout status -n kubeflow deployment/ml-pipeline-ui --timeout=600s
```

Some pods may initially be `Pending` or `ContainerCreating` while K3s downloads images. The two rollout commands wait for the KFP API and UI deployments to become available. If a pod stays unhealthy, inspect it with `kubectl describe pod -n kubeflow POD_NAME` and `kubectl logs -n kubeflow POD_NAME`. Check `df -h /` again if downloads or pods stall. Continue when the API and UI deployments are available.

## 3. Open the KFP UI

Keep this command running in a separate terminal:

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

Open <http://localhost:8080> on the **same machine**. This forwards your local port 8080 to the KFP UI service in K3s; it does not start another local pipeline run. If port 8080 is occupied, use `8081:80` and open <http://localhost:8081>.

## 4. Upload the YAML and start a run

1. In the KFP UI, open **Pipelines** and select **+ Upload pipeline**.
2. Select `/home/allen/mlflow-kubeflow-handson/synthetic-pipeline.yaml`, give it a name, and select **Create**.
3. Open **Runs** and select **+ Create run**. Choose the uploaded pipeline.
4. Set parameter **`c` to `0.5`** if you want to compare with the completed local run. The YAML's default is `1.0`.
5. Select **Start**, then open the run to watch `generate-data`, `train-model`, and `evaluate-model`.

Here, `c` is the logistic-regression **regularization setting** passed to `LogisticRegression(C=c)`. A smaller `c` means stronger regularization; a larger `c` means weaker regularization. It is an input to training, not the accuracy result. The [pipeline guide](KFP_PIPELINE.md#what-c-means) explains it with the local run's numbers.

Uploading registers the pipeline recipe. Selecting **Start** creates a run; only then does KFP schedule its tasks as Kubernetes workloads. In another terminal, you can watch them with:

```bash
kubectl get pods -n kubeflow --watch
```

Press Ctrl+C to stop watching. In the KFP UI, open the run's task logs and outputs to find the evaluation accuracy. Record that cluster result separately from the earlier **local** result of `0.7667` (92 correct out of 120). The same deterministic data and `c=0.5` should make the results comparable, but the cluster run has to finish before its actual value can be documented.

This pipeline does **not** call MLflow, so the MLflow server does not need to be running for the KFP cluster run. KFP's component containers will need access to their base image and Python package downloads on first run.

## References

- [KFP installation guide](https://kubeflow-pipelines.readthedocs.io/en/latest/operator-guides/installation.html)
- [KFP run a pipeline guide](https://kubeflow-pipelines.readthedocs.io/en/latest/user-guides/core-functions/run-a-pipeline.html)
- [KFP 2.18.0 manifests](https://github.com/kubeflow/pipelines/tree/2.18.0/manifests/kustomize)
