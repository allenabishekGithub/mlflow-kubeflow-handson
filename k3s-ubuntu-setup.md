# Install K3s on Ubuntu and configure kubectl access

These steps install K3s `v1.36.5+k3s1` on an Ubuntu server and allow the current user to use `kubectl` through the `k3s-admin` group.

> **Security:** The K3s kubeconfig grants administrative access to the cluster. Only add trusted users to `k3s-admin`.

## 1. Add your user to the K3s admin group

Create the group if it does not already exist, then add your current user:

```bash
getent group k3s-admin >/dev/null || sudo groupadd --system k3s-admin
sudo usermod -aG k3s-admin "$USER"
```

## 2. Install K3s

```bash
set -o pipefail
curl -sfL https://get.k3s.io | sudo env \
  INSTALL_K3S_VERSION='v1.36.5+k3s1' \
  sh -
```

The install script enables and starts the `k3s` systemd service.

## 3. Configure kubeconfig permissions

Create the K3s server configuration:

```bash
sudo tee /etc/rancher/k3s/config.yaml >/dev/null <<'EOF'
write-kubeconfig-group: k3s-admin
write-kubeconfig-mode: "0640"
EOF
```

Restart K3s and ensure the existing kubeconfig has the intended group and mode:

```bash
sudo systemctl restart k3s
sudo chgrp k3s-admin /etc/rancher/k3s/k3s.yaml
sudo chmod 0640 /etc/rancher/k3s/k3s.yaml
```

## 4. Set the kubeconfig path for Bash (optional)

This makes the K3s kubeconfig path explicit for `kubectl` in Bash sessions:

```bash
grep -qxF 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' ~/.bashrc \
  || echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.bashrc
source ~/.bashrc
```

## 5. Refresh group membership and verify

Log out and back in so the new group membership applies. Alternatively, start a shell with the group:

```bash
newgrp k3s-admin
```

Then check the group and node status:

```bash
id -nG
kubectl get nodes
```

The group list should include `k3s-admin`, and the node should report `Ready`.
