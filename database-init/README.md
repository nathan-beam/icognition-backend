# Rebuild the containers
docker-compose up --build --force-recreate -d

Options:
    -d, --detach        Detached mode: Run containers in the background,
                        print new container names. Incompatible with
                        --abort-on-container-exit.
    --no-deps           Don't start linked services.
    --force-recreate    Recreate containers even if their configuration
                        and image haven't changed.
    --build             Build images before starting containers.


# Find postgres IP
1. Find container ID ->  docker ps
2. Find IP -> docker inspect 87c13e1f865a | grep IPAddress
