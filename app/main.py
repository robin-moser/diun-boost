import os
import sys
from argparse import ArgumentParser

from loguru import logger

from app.docker_client import get_docker_client, get_running_containers
from app.yaml_helper import (compare_yaml_files, create_diun_yaml,
                             create_empty_yaml, write_yaml_to_file)


def setup_logging(level: str) -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green>"
            "<level>{level: <8}</level> {message}"
        ),
        level=level,
        colorize=True,
    )


def run_tasks(output_path: str, m_all: bool, compose_track: bool, swarm_mode: bool) -> None:
    client = get_docker_client()
    containers = get_running_containers(client, m_all, swarm_mode)
    diun_entries = create_diun_yaml(containers, m_all, compose_track)

    if compare_yaml_files(output_path, diun_entries):
        write_yaml_to_file(diun_entries, output_path)


def main():
    parser = ArgumentParser(description="diun-boost")
    parser.add_argument(
        "--first-run", action="store_true",
        help="Indicates this is the first manual run after container start."
    )
    args = parser.parse_args()

    logging_level = os.getenv("LOG_LEVEL", "INFO").upper()
    setup_logging(logging_level)

    monitor_all = os.getenv("WATCHBYDEFAULT", "false").lower() == "true"
    compose_track = os.getenv("DOCKER_COMPOSE_METADATA", "false").lower() == "true"
    output_path = os.getenv("DIUN_YAML_PATH", "/config/config.yml")
    swarm_mode = os.getenv("SWARM_MODE", "false").lower() == "true"

    if monitor_all:
        logger.info("🐳 Monitoring all containers by default...")
    else:
        logger.info(
            "🐳 Monitoring containers with DIUN labels i.e. diun.enable=true")

    if compose_track:
        logger.info("🐳 Tracking Docker Compose metadata...")

    if swarm_mode:
        logger.info(f"🐳 Docker Swarm mode enabled")

    if args.first_run:
        logger.info("✨ Running initial setup...")
        create_empty_yaml(output_path)
    else:
        logger.info("⏰ Running scheduled cron job...")

    run_tasks(output_path, monitor_all, compose_track, swarm_mode)


if __name__ == "__main__":
    main()
