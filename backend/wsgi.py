import os

from app import app, bootstrap_application


bootstrap_application(
    run_scheduler=os.getenv("RUN_SCHEDULER", "false").strip().lower() not in {"0", "false", "no"},
    run_startup_retrain=os.getenv("RUN_STARTUP_RETRAIN", "false").strip().lower() in {"1", "true", "yes"},
)
