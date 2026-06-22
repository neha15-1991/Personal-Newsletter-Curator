from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database import Session
from models import User
from pipeline import run_curator_for_user


# Create one background scheduler object.
scheduler = BackgroundScheduler(timezone="Asia/Seoul")


def run_daily_curator_job():
    """
    Runs the newsletter curator pipeline for all users.

    This function is used by APScheduler.
    It will:
    1. Get all users from the database.
    2. Run fetch + embed + digest pipeline for each user.
    """

    # Create a new database session.
    db = Session()

    results = []

    try:
        # Get all registered users.
        users = db.query(User).all()

        for user in users:
            try:
                # Run the full curator pipeline for this user.
                result = run_curator_for_user(
                    user=user,
                    db=db
                )

                results.append({
                    "user_id": user.id,
                    "email": user.email,
                    "status": "success",
                    "result": result
                })

            except Exception as error:
                # Roll back this user's failed database work.
                db.rollback()

                results.append({
                    "user_id": user.id,
                    "email": user.email,
                    "status": "failed",
                    "error": str(error)
                })

        print("Daily curator job completed")
        print(results)

        return {
            "message": "Daily curator job completed",
            "results": results
        }

    finally:
        # Always close the database session.
        db.close()


def start_scheduler():
    """
    Starts the APScheduler job.

    The job is scheduled to run every day at 7:00 AM.
    """

    if not scheduler.running:
        scheduler.add_job(
            run_daily_curator_job,
            CronTrigger(hour=7, minute=0, timezone="Asia/Seoul"),
            id="daily_curator_job",
            replace_existing=True
        )

        scheduler.start()

        print("APScheduler started. Daily job set for 7:00 AM.")


def stop_scheduler():
    """
    Stops the scheduler safely.
    """

    if scheduler.running:
        scheduler.shutdown()
        print("APScheduler stopped.")