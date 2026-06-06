## Linux Mint Installation Note for this RAG project.

Linux Mint is Ubuntu-based, so use Docker’s **Ubuntu repository**, but set the Ubuntu codename manually. For most current Linux Mint versions:

| Linux Mint | Ubuntu base  | Codename to use |
| ---------- | ------------ | --------------- |
| Mint 22.x  | Ubuntu 24.04 | `noble`         |
| Mint 21.x  | Ubuntu 22.04 | `jammy`         |
| Mint 20.x  | Ubuntu 20.04 | `focal`         |

Check your Mint version:

```bash
cat /etc/linuxmint/info
```

## 1. Install Docker Engine from Docker’s official repository

For **Linux Mint 22.x**, use `noble`:

```bash
UBUNTU_CODENAME=noble
```

For **Linux Mint 21.x**, use `jammy`:

```bash
UBUNTU_CODENAME=jammy
```

Then run:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${UBUNTU_CODENAME} stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update

sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Docker’s current Linux Compose install path is the Compose v2 plugin, installed as `docker-compose-plugin`, not the old Python `docker-compose` package. ([Docker Documentation][1])

## 2. Enable Docker

```bash
sudo systemctl enable --now docker
```

Verify:

```bash
sudo docker run hello-world
docker compose version
```

## 3. Allow your user to run Docker without `sudo`

```bash
sudo usermod -aG docker "$USER"
```

Then log out and log back in.

After logging back in, test:

```bash
docker run hello-world
docker compose version
```

## 4. Install NVIDIA Container Toolkit

You need this so Ollama can use your GTX 1080 Ti inside Docker.

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit

sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

Test GPU access:

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

You should see your GTX 1080 Ti listed.

## 5. Start the RAG project

From the repository directory:

```bash
docker compose up -d --build
```

Check containers:

```bash
docker compose ps
```

Pull models:

```bash
docker compose exec ollama ollama pull all-minilm
docker compose exec ollama ollama pull qwen2.5:7b-instruct-q4_K_M
```

Then check the API:

```bash
curl http://localhost:8080/health
```

## Important: do not install this package

Avoid:

```bash
sudo apt install docker-compose
```

That is the old Python-based Compose v1 package and is what commonly causes the `No module named 'distutils'` error. Use:

```bash
docker compose
```

with a space, not:

```bash
docker-compose
```

[1]: https://docs.docker.com/compose/install/linux/?utm_source=chatgpt.com "Install the Docker Compose plugin"
