"""
Automated Data Collection Scheduler
Schedules periodic scraping and data updates

Place in: scripts/scheduler.py
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import sys
import os
import logging

sys.path.append('src')

from scrapers.iom_scraper import IOMMigrantsScraper
from scrapers.cbp_scraper import CBPScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def scrape_iom_data():
    """Scheduled task: Scrape IOM data"""
    logger.info("=" * 60)
    logger.info("SCHEDULED TASK: IOM Data Scraping")
    logger.info("=" * 60)
    
    try:
        scraper = IOMMigrantsScraper()
        
        # Check if manual file exists, otherwise download
        manual_file = 'data/raw/iom_missing_migrants_manual.csv'
        if os.path.exists(manual_file):
            logger.info("Using existing manual file...")
            df = scraper.use_manual_file(manual_file)
        else:
            logger.info("Running automated download...")
            df = scraper.run_full_pipeline(region='Americas')
        
        if df is not None:
            logger.info(f"✓ IOM scraping successful: {len(df)} records")
            
            # TODO: Load into database
            # from scripts.load_iom_data import load_iom_data
            # load_iom_data()
            
        else:
            logger.error("✗ IOM scraping failed")
            
    except Exception as e:
        logger.error(f"✗ Error in IOM scraping: {e}")
    
    logger.info("=" * 60)


def scrape_cbp_data():
    """Scheduled task: Scrape CBP data"""
    logger.info("=" * 60)
    logger.info("SCHEDULED TASK: CBP Data Scraping")
    logger.info("=" * 60)
    
    try:
        scraper = CBPScraper()
        results = scraper.run_full_pipeline()
        
        if results:
            logger.info("✓ CBP scraping successful")
            
            # TODO: Load into database
            # from scripts.load_cbp_data import load_cbp_data
            # load_cbp_data()
            
        else:
            logger.error("✗ CBP scraping failed")
            
    except Exception as e:
        logger.error(f"✗ Error in CBP scraping: {e}")
    
    logger.info("=" * 60)


def generate_daily_report():
    """Scheduled task: Generate daily summary report"""
    logger.info("=" * 60)
    logger.info("SCHEDULED TASK: Daily Report Generation")
    logger.info("=" * 60)
    
    try:
        # TODO: Query database and generate report
        logger.info("Generating daily report...")
        
        # Placeholder for now
        logger.info(f"Report generated at: {datetime.now()}")
        
    except Exception as e:
        logger.error(f"✗ Error generating report: {e}")
    
    logger.info("=" * 60)


def setup_scheduler():
    """Configure and start the scheduler"""
    
    logger.info("=" * 60)
    logger.info("STARTING AUTOMATED SCHEDULER")
    logger.info("=" * 60)
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create scheduler
    scheduler = BlockingScheduler()
    
    # Schedule IOM scraping - Weekly on Monday at 2 AM
    scheduler.add_job(
        scrape_iom_data,
        CronTrigger(day_of_week='mon', hour=2, minute=0),
        id='iom_weekly_scrape',
        name='IOM Weekly Data Scraping',
        replace_existing=True
    )
    logger.info("✓ Scheduled: IOM scraping - Every Monday at 2:00 AM")
    
    # Schedule CBP scraping - Monthly on 1st at 3 AM
    scheduler.add_job(
        scrape_cbp_data,
        CronTrigger(day=1, hour=3, minute=0),
        id='cbp_monthly_scrape',
        name='CBP Monthly Data Scraping',
        replace_existing=True
    )
    logger.info("✓ Scheduled: CBP scraping - 1st of each month at 3:00 AM")
    
    # Schedule daily report - Every day at 9 AM
    scheduler.add_job(
        generate_daily_report,
        CronTrigger(hour=9, minute=0),
        id='daily_report',
        name='Daily Summary Report',
        replace_existing=True
    )
    logger.info("✓ Scheduled: Daily report - Every day at 9:00 AM")
    
    # Print all scheduled jobs
    logger.info("\n" + "=" * 60)
    logger.info("SCHEDULED JOBS:")
    logger.info("=" * 60)
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name}")
        logger.info(f"    ID: {job.id}")
        logger.info(f"    Next run: {job.next_run_time}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Scheduler is running. Press Ctrl+C to stop.")
    logger.info("=" * 60)
    
    # Start the scheduler
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("\nScheduler stopped by user")
        scheduler.shutdown()


def run_manual_test():
    """Run all tasks manually for testing"""
    logger.info("=" * 60)
    logger.info("MANUAL TEST MODE - Running All Tasks Once")
    logger.info("=" * 60)
    
    # Run IOM scraping
    logger.info("\nTask 1/3: IOM Data Scraping")
    scrape_iom_data()
    
    # Run CBP scraping
    logger.info("\nTask 2/3: CBP Data Scraping")
    scrape_cbp_data()
    
    # Run report generation
    logger.info("\nTask 3/3: Daily Report")
    generate_daily_report()
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ Manual test complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Data Collection Scheduler')
    parser.add_argument(
        '--mode',
        choices=['schedule', 'test'],
        default='schedule',
        help='Run mode: schedule (start scheduler) or test (run tasks once)'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        # Run all tasks once for testing
        run_manual_test()
    else:
        # Start the scheduler
        setup_scheduler()