"""
Dataflow Pipeline for ATI Data Ingestion
GCS (JSON Lines) → BigQuery (hand_summary)
"""
import json
import logging
from typing import Dict, Any, Iterator
from datetime import datetime

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions
from apache_beam.io.gcp.bigquery import WriteToBigQuery, BigQueryDisposition

from .config import Config


logger = logging.getLogger(__name__)


class ParseATIJson(beam.DoFn):
    """
    Parse ATI JSON Lines and transform to BigQuery schema

    Input: JSON string (one line from JSONL file)
    Output: Transformed dict matching BigQuery schema
    """

    def __init__(self):
        self.parse_errors = beam.metrics.Metrics.counter(
            'ati_ingestion', 'parse_errors'
        )
        self.successful_parses = beam.metrics.Metrics.counter(
            'ati_ingestion', 'successful_parses'
        )

    def process(self, line: str) -> Iterator[Dict[str, Any]]:
        """Process a single JSON line"""
        try:
            # Parse JSON
            data = json.loads(line)

            # Transform camelCase to snake_case and validate
            transformed = {
                'hand_id': str(data['handId']),
                'event_id': str(data.get('eventId', '')),
                'tournament_day': int(data.get('tournamentDay', 0)) if data.get('tournamentDay') else None,
                'hand_number': int(data.get('handNumber', 0)),
                'table_number': int(data.get('tableNumber', 0)),
                'timestamp_start_utc': self._parse_timestamp(data.get('timestampStartUTC')),
                'timestamp_end_utc': self._parse_timestamp(data.get('timestampEndUTC')),
                'duration_seconds': int(data.get('durationSeconds', 0)),
                'players': data.get('players', []),
                'pot_size_usd': float(data.get('potSizeUSD', 0.0)),
                'winner_player_name': str(data.get('winnerPlayerName', '')),
                'hand_description': str(data.get('handDescription', '')),
                'ingested_at': datetime.utcnow().isoformat(),
            }

            # Validate required fields
            if not transformed['hand_id']:
                raise ValueError("hand_id is required")

            self.successful_parses.inc()
            yield transformed

        except KeyError as e:
            self.parse_errors.inc()
            logger.error(
                f"Missing required field: {e}, line: {line[:100]}...",
                extra={'line_preview': line[:100]}
            )
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            self.parse_errors.inc()
            logger.error(
                f"Parse error: {e}, line: {line[:100]}...",
                extra={'error_type': type(e).__name__, 'line_preview': line[:100]}
            )
        except Exception as e:
            self.parse_errors.inc()
            logger.error(
                f"Unexpected error: {e}, line: {line[:100]}...",
                exc_info=True
            )

    def _parse_timestamp(self, timestamp_str: Any) -> str:
        """Parse timestamp string to ISO format"""
        if not timestamp_str:
            return None

        try:
            # If already in ISO format, return as is
            if isinstance(timestamp_str, str):
                # Validate it's parseable
                datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                return timestamp_str
            return str(timestamp_str)
        except (ValueError, AttributeError):
            logger.warning(f"Invalid timestamp format: {timestamp_str}")
            return None


class DeduplicateByHandId(beam.DoFn):
    """
    Remove duplicate hands based on hand_id
    Keeps the first occurrence
    """

    def __init__(self):
        self.seen_hand_ids = set()
        self.duplicates_removed = beam.metrics.Metrics.counter(
            'ati_ingestion', 'duplicates_removed'
        )
        self.unique_hands = beam.metrics.Metrics.counter(
            'ati_ingestion', 'unique_hands'
        )

    def process(self, element: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Process element and filter duplicates"""
        hand_id = element.get('hand_id')

        if hand_id in self.seen_hand_ids:
            self.duplicates_removed.inc()
            logger.debug(f"Duplicate hand_id removed: {hand_id}")
            return

        self.seen_hand_ids.add(hand_id)
        self.unique_hands.inc()
        yield element


def get_bigquery_schema() -> Dict[str, Any]:
    """
    Define BigQuery table schema

    Returns:
        Schema definition dict for WriteToBigQuery
    """
    return {
        'fields': [
            {'name': 'hand_id', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'event_id', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'tournament_day', 'type': 'INT64', 'mode': 'NULLABLE'},
            {'name': 'hand_number', 'type': 'INT64', 'mode': 'NULLABLE'},
            {'name': 'table_number', 'type': 'INT64', 'mode': 'NULLABLE'},
            {'name': 'timestamp_start_utc', 'type': 'TIMESTAMP', 'mode': 'NULLABLE'},
            {'name': 'timestamp_end_utc', 'type': 'TIMESTAMP', 'mode': 'NULLABLE'},
            {'name': 'duration_seconds', 'type': 'INT64', 'mode': 'NULLABLE'},
            {'name': 'players', 'type': 'STRING', 'mode': 'REPEATED'},
            {'name': 'pot_size_usd', 'type': 'NUMERIC', 'mode': 'NULLABLE'},
            {'name': 'winner_player_name', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'hand_description', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'ingested_at', 'type': 'TIMESTAMP', 'mode': 'NULLABLE'},
        ]
    }


def create_pipeline_options(
    project_id: str,
    region: str,
    temp_location: str,
    staging_location: str,
    runner: str = "DataflowRunner",
    job_name: str = None,
    max_workers: int = 10
) -> PipelineOptions:
    """
    Create Dataflow pipeline options

    Args:
        project_id: GCP project ID
        region: GCP region
        temp_location: GCS temp location
        staging_location: GCS staging location
        runner: Pipeline runner (DataflowRunner or DirectRunner)
        job_name: Dataflow job name
        max_workers: Maximum number of workers

    Returns:
        PipelineOptions object
    """
    options = PipelineOptions()

    # Google Cloud options
    google_cloud_options = options.view_as(GoogleCloudOptions)
    google_cloud_options.project = project_id
    google_cloud_options.region = region
    google_cloud_options.temp_location = temp_location
    google_cloud_options.staging_location = staging_location

    if job_name:
        google_cloud_options.job_name = job_name

    # Standard options
    standard_options = options.view_as(StandardOptions)
    standard_options.runner = runner

    # Additional options
    options.view_as(beam.options.pipeline_options.WorkerOptions).max_num_workers = max_workers

    return options


def run_pipeline(
    gcs_path: str,
    project_id: str = None,
    dataset: str = None,
    table: str = None,
    runner: str = None,
    job_name: str = None
) -> str:
    """
    Run the ATI data ingestion pipeline

    Args:
        gcs_path: GCS path to JSONL file (e.g., gs://bucket/path/file.jsonl)
        project_id: GCP project ID (default: from Config)
        dataset: BigQuery dataset (default: from Config)
        table: BigQuery table (default: from Config)
        runner: Pipeline runner (default: from Config)
        job_name: Dataflow job name (auto-generated if None)

    Returns:
        Dataflow job ID

    Raises:
        ValueError: If gcs_path is invalid
        RuntimeError: If pipeline execution fails
    """
    # Validate GCS path
    if not gcs_path or not gcs_path.startswith('gs://'):
        raise ValueError(f"Invalid GCS path: {gcs_path}")

    # Use config defaults if not provided
    config = Config()
    project_id = project_id or config.PROJECT_ID
    dataset = dataset or config.DATASET
    table = table or config.TABLE
    runner = runner or config.DATAFLOW_RUNNER

    # Generate job name if not provided
    if not job_name:
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        job_name = f"ati-ingestion-{timestamp}"

    # Create pipeline options
    pipeline_options = create_pipeline_options(
        project_id=project_id,
        region=config.REGION,
        temp_location=config.TEMP_LOCATION,
        staging_location=config.STAGING_LOCATION,
        runner=runner,
        job_name=job_name,
        max_workers=config.MAX_WORKERS
    )

    # BigQuery table path
    bq_table = f"{project_id}:{dataset}.{table}"

    logger.info(
        f"Starting pipeline: {job_name}",
        extra={
            'gcs_path': gcs_path,
            'bq_table': bq_table,
            'runner': runner
        }
    )

    # Create and run pipeline
    with beam.Pipeline(options=pipeline_options) as pipeline:
        (
            pipeline
            | 'Read JSONL from GCS' >> beam.io.ReadFromText(gcs_path)
            | 'Parse JSON' >> beam.ParDo(ParseATIJson())
            | 'Remove Duplicates' >> beam.ParDo(DeduplicateByHandId())
            | 'Write to BigQuery' >> WriteToBigQuery(
                table=bq_table,
                schema=get_bigquery_schema(),
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )

    logger.info(f"Pipeline completed: {job_name}")
    return job_name


if __name__ == "__main__":
    # Example usage for local testing
    logging.basicConfig(level=logging.INFO)

    # Test with sample GCS path
    test_gcs_path = "gs://gg-poker-ati/sample.jsonl"

    try:
        job_id = run_pipeline(
            gcs_path=test_gcs_path,
            runner="DirectRunner"  # Local runner for testing
        )
        print(f"Pipeline completed: {job_id}")
    except Exception as e:
        print(f"Pipeline failed: {e}")
