from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.inference_service import InferenceService
from app.services.patient_service import PatientService
from app.services.vital_service import VitalService


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def patient_repo():
    return AsyncMock()


@pytest.fixture
def vital_repo():
    return AsyncMock()


@pytest.fixture
def patient_service(mock_session, patient_repo):
    service = PatientService(mock_session)
    service.repo = patient_repo
    return service


@pytest.fixture
def vital_service(mock_session, patient_repo, vital_repo):
    service = VitalService(mock_session)
    service.vital_repo = vital_repo
    service.patient_repo = patient_repo
    return service


@pytest.fixture
def inference_service(mock_session, patient_repo, vital_repo):
    service = InferenceService(mock_session)
    service.vital_repo = vital_repo
    service.patient_repo = patient_repo
    return service
