# Docker Setup for YouTube Migrator

This guide explains how to use Docker with the YouTube Migrator project.

## 🐳 Quick Start

### Prerequisites
- Docker installed on your system
- Docker Compose (optional, but recommended)
- Your Google Takeout data files
- `client_secret.json` from Google Cloud Console

### Option 1: Using Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cysec-wht24/youtube-migrator.git
   cd youtube-migrator
   ```

2. **Place your files in the `data/` folder:**
   ```bash
   mkdir -p data
   # Copy your client_secret.json and Takeout files to data/
   ```

3. **Run with Docker Compose:**
   ```bash
   docker-compose up
   ```

4. **To run interactively:**
   ```bash
   docker-compose run --rm youtube-migrator
   ```

### Option 2: Using Docker Commands

1. **Build the Docker image:**
   ```bash
   docker build -t youtube-migrator .
   ```

2. **Run the container:**
   ```bash
   docker run -it --rm \
     -v $(pwd)/data:/app/data \
     youtube-migrator
   ```

### Option 3: Using Pre-built Image from GitHub Container Registry

Once the GitHub Actions workflow has run, you can pull the pre-built image:

```bash
# Pull the latest image
docker pull ghcr.io/cysec-wht24/youtube-migrator:latest

# Run the container
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  ghcr.io/cysec-wht24/youtube-migrator:latest
```

## 📁 Volume Mounts

The Docker container uses a volume mount for the `data/` directory. This is where you should place:

- `client_secret.json` - Your Google API credentials
- `MyActivity.html` - Your YouTube Takeout HTML file
- `subscriptions.csv` - Your subscriptions CSV
- `music library songs.csv` - Your music library CSV

All generated files (progress.json, parsed_activity.json, token.json) will also be saved here.

## 🔧 Customization

### Environment Variables

You can pass environment variables to customize the behavior:

```bash
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -e MAX_SUBSCRIPTIONS_PER_RUN=100 \
  -e MAX_LIKES_PER_RUN=200 \
  youtube-migrator
```

### Using Different Base Images

If you need a different Python version, edit the Dockerfile:

```dockerfile
FROM python:3.10-slim  # or python:3.12-slim
```

## 🚀 GitHub Actions Workflow

The repository includes a GitHub Actions workflow that automatically:

1. **Builds a Docker image** whenever you push to `main` or `develop` branches
2. **Pushes the image** to GitHub Container Registry (ghcr.io)
3. **Tags the image** with:
   - Branch name (e.g., `main`, `develop`)
   - Git SHA (e.g., `main-abc1234`)
   - Semantic version tags (for releases)
   - `latest` tag for the main branch

### Setting Up GitHub Actions

1. **The workflow is already configured** in `.github/workflows/docker-build.yml`

2. **Copy the workflow file to your repository:**
   ```bash
   mkdir -p .github/workflows
   cp docker-build.yml .github/workflows/
   ```

3. **Commit and push:**
   ```bash
   git add .github/workflows/docker-build.yml
   git commit -m "Add Docker build workflow"
   git push
   ```

4. **The workflow will run automatically** on push to main/develop branches

5. **Access your images** at `https://github.com/cysec-wht24/youtube-migrator/pkgs/container/youtube-migrator`

### Workflow Triggers

The workflow runs on:
- Push to `main` or `develop` branches
- Pull requests to `main`
- Release publications
- Manual trigger (workflow_dispatch)

It will skip builds if only documentation files (*.md, LICENSE) are changed.

## 🛠️ Development

### Building Locally

```bash
# Build with a specific tag
docker build -t youtube-migrator:dev .

# Build with no cache
docker build --no-cache -t youtube-migrator .
```

### Debugging

Run the container with a shell to debug:

```bash
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  --entrypoint /bin/bash \
  youtube-migrator
```

### Viewing Logs

```bash
# If running with docker-compose
docker-compose logs -f

# If running with docker run, logs appear in stdout
```

## 📊 Resource Management

The Docker container is lightweight:
- Base image: ~150MB
- With dependencies: ~200MB
- Runtime memory: ~50-100MB

## 🔒 Security Notes

1. **Never commit `client_secret.json`** - It's already in .gitignore and .dockerignore
2. **Use volume mounts** - Don't copy sensitive files into the image
3. **GitHub Container Registry** - Images are public by default. Make them private in package settings if needed.

## 🐛 Troubleshooting

### Issue: Permission Denied

```bash
# Fix permissions on Linux
sudo chown -R $USER:$USER data/
```

### Issue: Container Exits Immediately

The script is interactive, so you need the `-it` flags:

```bash
docker run -it --rm -v $(pwd)/data:/app/data youtube-migrator
```

### Issue: Cannot Access GitHub Container Registry

Authenticate with GitHub:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

## 📝 Additional Commands

### Clean up Docker resources

```bash
# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove all unused volumes
docker volume prune
```

### View running containers

```bash
docker ps
```

### Stop a running container

```bash
docker stop youtube-migrator
```

## 🤝 Contributing

When contributing Docker-related changes:

1. Test builds locally first
2. Update this documentation if you change the Dockerfile
3. Ensure the GitHub Actions workflow still passes

## 📚 Resources

- [Docker Documentation](https://docs.docker.com/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
