# K3s setup for the Kubeflow Pipelines exercise

This is the **single-machine Kubernetes setup** for the next part of the quickstart. The machine checked on 2026-11-09 is Ubuntu 22.04 (`x86_64`, 3 CPUs, 11 GiB RAM). K3s and `kubectl` were initially absent. The installation and direct `kubectl` access were **verified on 2026-11-09**.

## Goal

After setup, `allen` can run `kubectl get nodes` and `kubectl get pods -A` directly, without `sudo`, `k3s kubectl`, or shell aliases. K3s installs a `kubectl` command in the normal system path. A dedicated local group grants access to K3s's admin kubeconfig at `/etc/rancher/k3s/k3s.yaml`.

## 1. Create the local cluster-admin group

Run these once as `allen`:

```bash
sudo groupadd --system k3s-admin
sudo usermod -aG k3s-admin "$USER"
```

The first command creates the group. The second adds your account to it without removing your other groups. Initial system setup requires `sudo`; everyday `kubectl` commands will not. Members of this group receive **full administrator access** to this local Kubernetes cluster, because the kubeconfig contains admin credentials.

## 2. Install K3s with group-readable kubeconfig

This pins a published K3s 1.36 release so the exercise uses a repeatable Kubernetes version. The installer downloads K3s and creates a `systemd` service and a `kubectl` command:

```bash
set -o pipefail
curl -sfL https://get.k3s.io | sudo env \
  INSTALL_K3S_VERSION='v1.36.5+k3s1' \
  K3S_KUBECONFIG_GROUP='k3s-admin' \
  K3S_KUBECONFIG_MODE='0640' \
  sh -
```

The group and mode settings tell K3s to write `/etc/rancher/k3s/k3s.yaml` as readable by `k3s-admin` members. Setting this in K3s's service configuration keeps the permission policy when K3s rewrites the file. `0640` grants access to root and the group, while keeping the admin credentials unreadable by other local users. The installer normally creates `/usr/local/bin/kubectl` as a link to the K3s binary when no `kubectl` command already exists.

### Recorded installation result

The learner created `k3s-admin`, added `allen` to it, and ran the command above. The installer reported that it downloaded and verified **`v1.36.5+k3s1`**, installed `/usr/local/bin/k3s`, created `/usr/local/bin/kubectl -> k3s`, enabled the `k3s` systemd service, and started it. The first attempt to type `set -o pipefail` had a typo (`set -o- pipefail`) and printed a shell usage error; the corrected command was run before installation, so that typo did not affect the install. The learner then ran `newgrp k3s-admin`.

## 3. Activate your new group membership

Group changes do not appear in a shell that was already open. Start a new group shell:

```bash
newgrp k3s-admin
```

Alternatively, log out and log back in. Then check the account, command, and file permissions:

```bash
id -nG
command -v kubectl
ls -l /etc/rancher/k3s/k3s.yaml
```

Expected: `id -nG` includes `k3s-admin`; `kubectl` resolves to a command (normally `/usr/local/bin/kubectl`); and `k3s.yaml` is owned by `root:k3s-admin` with permissions like `-rw-r-----`.

## 4. Check the cluster without `sudo`

```bash
kubectl get nodes
kubectl get pods -A
```

The first command should show this machine as a node, eventually with status `Ready`. The second lists system pods across all namespaces. A plain `kubectl get pods` only checks the current namespace, which may contain no pods yet. You can also inspect the K3s service with `systemctl status k3s`.

### Verified result (2026-11-09)

The commands above were run as `allen` **without `sudo`** in the shell opened by `newgrp k3s-admin`:

```text
$ id -nG
allen adm cdrom sudo dip plugdev lxd k3s-admin docker

$ ls -l /etc/rancher/k3s/k3s.yaml
-rw-r----- 1 root k3s-admin 2949 Nov  9 14:07 /etc/rancher/k3s/k3s.yaml

$ kubectl get nodes
NAME    STATUS   ROLES           AGE    VERSION
allen   Ready    control-plane   9m5s   v1.36.5+k3s1

$ kubectl get pods -A
NAMESPACE     NAME                                      READY   STATUS      RESTARTS        AGE
kube-system   coredns-7cfb7bc9c7-52rjt                  1/1     Running     1 (3m58s ago)   9m5s
kube-system   helm-install-traefik-crd-shps9            0/1     Completed   0               9m5s
kube-system   helm-install-traefik-jg54n                0/1     Completed   2 (7m20s ago)   9m5s
kube-system   local-path-provisioner-77b9867795-xg9pt   1/1     Running     1 (3m57s ago)   9m5s
kube-system   metrics-server-6dc596dfb8-gxnwj           1/1     Running     1 (3m57s ago)   9m5s
kube-system   svclb-traefik-6b590c6c-s8jvz              2/2     Running     2 (3m57s ago)   7m6s
kube-system   traefik-7c8544f77-nhv2r                   1/1     Running     1 (3m57s ago)   7m6s
```

This confirms the user is in `k3s-admin`, the kubeconfig is readable by that group, the single K3s control-plane node is `Ready`, and the listed system pods are running or their installation jobs have completed. The pod names, ages, and restart counts are a snapshot and will change over time.

## If a check fails

| Symptom | Check |
| --- | --- |
| `kubectl: command not found` | Check `ls -l /usr/local/bin/kubectl` and whether `/usr/local/bin` is in `PATH`. K3s's installer normally creates this command when it is not already present. |
| `permission denied` reading `k3s.yaml` | Check `id -nG` and `ls -l /etc/rancher/k3s/k3s.yaml`. Open a new login session if the group has not appeared. |
| `connection refused` or no node yet | Check `systemctl status k3s`; if it failed, inspect `sudo journalctl -u k3s -n 100 --no-pager`. A fresh install can take time to start system pods. |
| The node stays `NotReady` | Check `kubectl get pods -A` and the K3s service logs for the actual startup or networking error before changing firewall settings. |

This step provides the Kubernetes cluster and local admin access. Kubeflow Pipelines itself is a separate installation step; its release and resource needs should be checked before deployment.

## Sources

- [K3s Quick-Start Guide](https://docs.k3s.io/quick-start)
- [K3s server options: kubeconfig group and mode](https://docs.k3s.io/cli/server)
- [K3s cluster access](https://docs.k3s.io/cluster-access)
- [K3s installer environment variables](https://docs.k3s.io/reference/env-variables)
- [K3s 1.36 release notes](https://docs.k3s.io/release-notes/v1.36.X)
