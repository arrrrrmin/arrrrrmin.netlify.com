import boto3
from moto import mock_transcribe


@mock_transcribe
def test_s3_bucket_exists():
    region_name = "eu-central-1"
    client = boto3.client("transcribe", region_name=region_name)
    job_name = "validate_get_transcription_job_response_all_states"
    args = {
        "TranscriptionJobName": job_name,
        "LanguageCode": "en-US",
        "Media": {"MediaFileUri": "s3://my-bucket/my-media-file.wav",},
    }
    client.start_transcription_job(**args)
    response = client.get_transcription_job(TranscriptionJobName=job_name)

    job = response.TranscriptionJob
    assert job["TranscriptionJobName"] == job_name
    assert job["LanguageCode"] == "en-US"
    assert job["Media"] is not None
    assert job["Media"]["MediaFileUri"] is not None
    assert job["Media"]["MediaFileUri"].uri == "s3://my-bucket/my-media-file.wav"
    assert job.TranscriptionJobStatus == "QUEUED"
    assert job.Settings.VocabularyName is None
    assert job.Settings.ChannelIdentification is False
    assert job.Settings.ShowSpeakerLabels is False
    assert job.Settings.ShowAlternatives is False

    response = client.get_transcription_job(TranscriptionJobName=job_name)
    job = response.TranscriptionJob
    assert job.TranscriptionJobStatus == "IN_PROGRESS"

    response = client.get_transcription_job(TranscriptionJobName=job_name)
    job = response.TranscriptionJob
    assert job.TranscriptionJobStatus == "COMPLETED"
    assert job.TranscriptUri.TranscriptFileUri is not None
    assert (
        "https://s3.eu-central-1.amazonaws.com/aws-transcribe-eu-central-1-prod/"
        in job.TranscriptUri.TranscriptFileUri
    )