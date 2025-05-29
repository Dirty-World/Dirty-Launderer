import os
import pytest
from unittest.mock import patch, MagicMock
from bot.main import send_alert, delete_cloud_functions, pause_scheduler_jobs

@patch("main.requests.post")
def test_send_alert_success(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.raise_for_status = MagicMock()
    os.environ["TELEGRAM_TOKEN"] = "dummy_token"
    os.environ["ALERT_CHAT_ID"] = "dummy_chat_id"

    send_alert("Test message")
    mock_post.assert_called_once_with(
        "https://api.telegram.org/botdummy_token/sendMessage",
        data={"chat_id": "dummy_chat_id", "text": "⚠️ [Budget Alert] Test message"},
        timeout=10
    )

@patch("main.requests.post")
def test_send_alert_failure(mock_post):
    mock_post.side_effect = Exception("Network error")
    os.environ["TELEGRAM_TOKEN"] = "dummy_token"
    os.environ["ALERT_CHAT_ID"] = "dummy_chat_id"

    send_alert("Test message")
    mock_post.assert_called_once()

@patch("main.requests.post")
def test_send_alert_missing_env_vars(mock_post):
    if "TELEGRAM_TOKEN" in os.environ:
        del os.environ["TELEGRAM_TOKEN"]
    if "ALERT_CHAT_ID" in os.environ:
        del os.environ["ALERT_CHAT_ID"]

    with pytest.raises(KeyError):
        send_alert("Test message")
    mock_post.assert_not_called()

@patch("main.build")
@patch("main.send_alert")
def test_delete_cloud_functions(mock_send_alert, mock_build):
    mock_functions = MagicMock()
    mock_build.return_value = mock_functions
    mock_functions.projects().locations().functions().delete().execute.return_value = {}

    credentials = MagicMock()
    project_id = "test_project"
    region = "us-central1"
    function_names = ["test_function"]

    delete_cloud_functions(credentials, project_id, region, function_names)
    mock_functions.projects().locations().functions().delete.assert_called_once_with(
        name="projects/test_project/locations/us-central1/functions/test_function"
    )
    mock_send_alert.assert_any_call("✅ Deleted Cloud Function: test_function")

@patch("main.build")
@patch("main.send_alert")
def test_delete_cloud_functions_no_functions(mock_send_alert, mock_build):
    mock_functions = MagicMock()
    mock_build.return_value = mock_functions
    mock_functions.projects().locations().functions().delete().execute.return_value = {}

    credentials = MagicMock()
    project_id = "test_project"
    region = "us-central1"
    function_names = []  # No functions to delete

    delete_cloud_functions(credentials, project_id, region, function_names)
    mock_functions.projects().locations().functions().delete.assert_not_called()
    mock_send_alert.assert_not_called()

@patch("main.build")
@patch("main.send_alert")
def test_delete_cloud_functions_api_error(mock_send_alert, mock_build):
    mock_functions = MagicMock()
    mock_build.return_value = mock_functions
    mock_functions.projects().locations().functions().delete().execute.side_effect = Exception("API error")

    credentials = MagicMock()
    project_id = "test_project"
    region = "us-central1"
    function_names = ["test_function"]

    delete_cloud_functions(credentials, project_id, region, function_names)
    mock_functions.projects().locations().functions().delete.assert_called_once_with(
        name="projects/test_project/locations/us-central1/functions/test_function"
    )
    mock_send_alert.assert_any_call("❌ Failed to delete Cloud Function: test_function")

@patch("main.build")
@patch("main.send_alert")
def test_delete_cloud_functions_partial_failure(mock_send_alert, mock_build):
    mock_functions = MagicMock()
    mock_build.return_value = mock_functions
    mock_functions.projects().locations().functions().delete().execute.side_effect = [
        {},  # First function succeeds
        Exception("API error")  # Second function fails
    ]

    credentials = MagicMock()
    project_id = "test_project"
    region = "us-central1"
    function_names = ["function1", "function2"]

    delete_cloud_functions(credentials, project_id, region, function_names)
    mock_functions.projects().locations().functions().delete.assert_any_call(
        name="projects/test_project/locations/us-central1/functions/function1"
    )
    mock_functions.projects().locations().functions().delete.assert_any_call(
        name="projects/test_project/locations/us-central1/functions/function2"
    )
    mock_send_alert.assert_any_call("✅ Deleted Cloud Function: function1")
    mock_send_alert.assert_any_call("❌ Failed to delete Cloud Function: function2")

@patch("main.build")
@patch("main.send_alert")
def test_delete_cloud_functions_invalid_api_response(mock_send_alert, mock_build):
    mock_functions = MagicMock()
    mock_build.return_value = mock_functions
    mock_functions.projects().locations().functions().delete().execute.return_value = None  # Invalid response

    credentials = MagicMock()
    project_id = "test_project"
    region = "us-central1"
    function_names = ["test_function"]

    with pytest.raises(TypeError):  # Adjust based on how your code handles this
        delete_cloud_functions(credentials, project_id, region, function_names)
    mock_send_alert.assert_not_called()

@patch("main.build")
@patch("main.send_alert")
def test_delete_cloud_functions_empty_function_names(mock_send_alert, mock_build):
    """Test delete_cloud_functions with None as function_names."""
    mock_functions = MagicMock()
    mock_build.return_value = mock_functions

    credentials = MagicMock()
    project_id = "test_project"
    region = "us-central1"
    function_names = None  # Explicitly test for None

    delete_cloud_functions(credentials, project_id, region, function_names)
    mock_functions.projects().locations().functions().delete.assert_not_called()
    mock_send_alert.assert_not_called()

@patch("main.build")
@patch("main.send_alert")
def test_delete_cloud_functions_large_input(mock_send_alert, mock_build):
    """Test delete_cloud_functions with a large number of functions."""
    mock_functions = MagicMock()
    mock_build.return_value = mock_functions
    mock_functions.projects().locations().functions().delete().execute.return_value = {}

    credentials = MagicMock()
    project_id = "test_project"
    region = "us-central1"
    function_names = [f"function_{i}" for i in range(1000)]  # Large input

    delete_cloud_functions(credentials, project_id, region, function_names)
    assert mock_functions.projects().locations().functions().delete.call_count == 1000
    assert mock_send_alert.call_count == 1000

@patch("main.build")
@patch("main.send_alert")
def test_pause_scheduler_jobs(mock_send_alert, mock_build):
    mock_scheduler = MagicMock()
    mock_build.return_value = mock_scheduler
    mock_scheduler.projects().locations().jobs().list.return_value.execute.return_value = {
        "jobs": [{"name": "test_job"}]
    }

    credentials = MagicMock()
    project_id = "test_project"
    region = "us-central1"

    pause_scheduler_jobs(credentials, project_id, region)
    mock_scheduler.projects().locations().jobs().pause.assert_called_once_with(name="test_job")
    mock_send_alert.assert_any_call("⏸️ Paused Scheduler job: test_job")

@patch("main.build")
@patch("main.send_alert")
def test_pause_scheduler_jobs_no_jobs(mock_send_alert, mock_build):
    mock_scheduler = MagicMock()
    mock_build.return_value = mock_scheduler
    mock_scheduler.projects().locations().jobs().list.return_value.execute.return_value = {
        "jobs": []  # No jobs to pause
    }

    credentials = MagicMock()
    project_id = "test_project"
    region = "us-central1"

    pause_scheduler_jobs(credentials, project_id, region)
    mock_scheduler.projects().locations().jobs().pause.assert_not_called()
    mock_send_alert.assert_not_called()

@patch("main.build")
@patch("main.send_alert")
def test_pause_scheduler_jobs_api_error(mock_send_alert, mock_build):
    mock_scheduler = MagicMock()
    mock_build.return_value = mock_scheduler
    mock_scheduler.projects().locations().jobs().list.return_value.execute.return_value = {
        "jobs": [{"name": "test_job"}]
    }
    mock_scheduler.projects().locations().jobs().pause.side_effect = Exception("API error")

    credentials = MagicMock()
    project_id = "test_project"
    region = "us-central1"

    pause_scheduler_jobs(credentials, project_id, region)
    mock_scheduler.projects().locations().jobs().pause.assert_called_once_with(name="test_job")
    mock_send_alert.assert_any_call("❌ Failed to pause Scheduler job: test_job")

@patch("main.build")
@patch("main.send_alert")
def test_pause_scheduler_jobs_multiple_jobs(mock_send_alert, mock_build):
    mock_scheduler = MagicMock()
    mock_build.return_value = mock_scheduler
    mock_scheduler.projects().locations().jobs().list.return_value.execute.return_value = {
        "jobs": [{"name": "job1"}, {"name": "job2"}]
    }

    credentials = MagicMock()
    project_id = "test_project"
    region = "us-central1"

    pause_scheduler_jobs(credentials, project_id, region)
    mock_scheduler.projects().locations().jobs().pause.assert_any_call(name="job1")
    mock_scheduler.projects().locations().jobs().pause.assert_any_call(name="job2")
    mock_send_alert.assert_any_call("⏸️ Paused Scheduler job: job1")
    mock_send_alert.assert_any_call("⏸️ Paused Scheduler job: job2")

@patch("main.build")
@patch("main.send_alert")
def test_pause_scheduler_jobs_invalid_response(mock_send_alert, mock_build):
    """Test pause_scheduler_jobs with an invalid API response."""
    mock_scheduler = MagicMock()
    mock_build.return_value = mock_scheduler
    mock_scheduler.projects().locations().jobs().list.return_value.execute.return_value = None  # Invalid response

    credentials = MagicMock()
    project_id = "test_project"
    region = "us-central1"

    with pytest.raises(TypeError):  # Adjust based on how your code handles this
        pause_scheduler_jobs(credentials, project_id, region)
    mock_scheduler.projects().locations().jobs().pause.assert_not_called()
    mock_send_alert.assert_not_called()

@patch("main.build")
@patch("main.send_alert")
def test_pause_scheduler_jobs_large_input(mock_send_alert, mock_build):
    """Test pause_scheduler_jobs with a large number of jobs."""
    mock_scheduler = MagicMock()
    mock_build.return_value = mock_scheduler
    mock_scheduler.projects().locations().jobs().list.return_value.execute.return_value = {
        "jobs": [{"name": f"job_{i}"} for i in range(1000)]  # Large input
    }

    credentials = MagicMock()
    project_id = "test_project"
    region = "us-central1"

    pause_scheduler_jobs(credentials, project_id, region)
    assert mock_scheduler.projects().locations().jobs().pause.call_count == 1000
    assert mock_send_alert.call_count == 1000