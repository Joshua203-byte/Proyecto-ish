"""
Tests for Jobs API endpoints.
"""
import pytest
from tests.conftest import create_test_job


class TestListJobs:
    """Tests for GET /api/v1/jobs/"""
    
    def test_list_jobs_empty(self, auth_client, test_user):
        """Test listing jobs when none exist."""
        response = auth_client.get("/api/v1/jobs/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_jobs_with_jobs(self, auth_client, test_user, db):
        """Test listing jobs returns user's jobs."""
        # Create test jobs
        job1 = create_test_job(db, test_user, script_name="train1.py")
        job2 = create_test_job(db, test_user, script_name="train2.py")
        
        response = auth_client.get("/api/v1/jobs/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_list_jobs_filter_by_status(self, auth_client, test_user, db):
        """Test filtering jobs by status."""
        create_test_job(db, test_user, status="pending")
        create_test_job(db, test_user, status="running")
        create_test_job(db, test_user, status="completed")
        
        response = auth_client.get("/api/v1/jobs/?status=running")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "running"
    
    def test_list_jobs_unauthorized(self, client):
        """Test jobs list requires authentication."""
        response = client.get("/api/v1/jobs/")
        
        assert response.status_code == 401


class TestGetJob:
    """Tests for GET /api/v1/jobs/{job_id}"""
    
    def test_get_job_success(self, auth_client, test_user, db):
        """Test getting a specific job."""
        job = create_test_job(db, test_user, script_name="mymodel.py")
        
        response = auth_client.get(f"/api/v1/jobs/{job.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(job.id)
        assert data["script_name"] == "mymodel.py"
    
    def test_get_job_not_found(self, auth_client, test_user):
        """Test getting non-existent job."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = auth_client.get(f"/api/v1/jobs/{fake_id}")
        
        assert response.status_code == 404
    
    def test_get_job_other_user(self, auth_client, test_user, admin_user, db):
        """Test cannot access other user's job."""
        # Create job for admin user
        admin_job = create_test_job(db, admin_user, script_name="admin.py")
        
        # Try to access as regular user
        response = auth_client.get(f"/api/v1/jobs/{admin_job.id}")
        
        assert response.status_code == 404


class TestCancelJob:
    """Tests for POST /api/v1/jobs/{job_id}/cancel"""
    
    def test_cancel_pending_job(self, auth_client, test_user, db):
        """Test cancelling a pending job."""
        job = create_test_job(db, test_user, status="pending")
        
        response = auth_client.post(f"/api/v1/jobs/{job.id}/cancel")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
    
    def test_cancel_completed_job(self, auth_client, test_user, db):
        """Test cannot cancel completed job."""
        job = create_test_job(db, test_user, status="completed")
        
        response = auth_client.post(f"/api/v1/jobs/{job.id}/cancel")
        
        # Should fail - job already completed
        assert response.status_code == 400


class TestGetJobLogs:
    """Tests for GET /api/v1/jobs/{job_id}/logs"""
    
    def test_get_logs_success(self, auth_client, test_user, db):
        """Test getting job logs."""
        job = create_test_job(db, test_user)
        job.logs = "Epoch 1/10\nLoss: 0.5\nEpoch 2/10\nLoss: 0.3"
        db.commit()
        
        response = auth_client.get(f"/api/v1/jobs/{job.id}/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "Epoch 1/10" in data["logs"]
    
    def test_get_logs_empty(self, auth_client, test_user, db):
        """Test getting logs from job with no logs."""
        job = create_test_job(db, test_user)
        
        response = auth_client.get(f"/api/v1/jobs/{job.id}/logs")
        
        assert response.status_code == 200
