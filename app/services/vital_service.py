import logging
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import AppException, ConflictException, NotFoundException, ServerException
from app.dtos.patient.patients_vitals import VitalResponse
from app.dtos.vital.vitals import VitalUpsertRequest, VitalUpsertResponse
from app.models.vital import VitalType
from app.repositories.patient_repository import PatientRepository
from app.repositories.vital_repository import VitalRepository


class VitalService:
    def __init__(self, session: AsyncSession) -> None:
        self.vital_repo = VitalRepository(session)
        self.patient_repo = PatientRepository(session)

    async def get_patient_vitals(
        self,
        patient_external_id: str,
        time_from: datetime,
        time_to: datetime,
        vital_type: VitalType | None = None,
    ) -> VitalResponse:
        """환자 Vital 데이터 조회"""
        try:
            # 환자 존재 검증
            patient = await self.patient_repo.find_one_by_external_id(patient_external_id)
            if not patient:
                raise NotFoundException(message=f"Patient {patient_external_id} not found")

            # 외부 patient_id로 JOIN 조회
            vitals = await self.vital_repo.find_by_patient_and_time_range(
                patient_external_id, time_from, time_to, vital_type
            )

            return VitalResponse.from_entity(patient, vitals, vital_type)
        except AppException:
            raise
        except Exception as e:
            logging.exception(f"Failed to get patient vitals: {patient_external_id} - {str(e)}")
            raise ServerException(message="Failed to get patient vitals")

    async def upsert_vital(self, request: VitalUpsertRequest) -> tuple[VitalUpsertResponse, bool]:
        """
        Vital UPSERT

        Returns:
            tuple[VitalUpsertResponse, bool]: (응답, 신규 생성 여부)
        """
        try:
            # 등록된 환자만 Vital 입력 가능
            patient = await self.patient_repo.find_one_by_external_id(request.patient_external_id)
            if not patient:
                raise NotFoundException(message=f"Patient {request.patient_external_id} not found")

            # 외부 patient_id로 복합키 조회
            existing = await self.vital_repo.find_one_by_composite_key(
                request.patient_external_id, request.recorded_at, request.vital_type
            )

            if existing:
                # Optimistic lock
                if existing.version != request.version:
                    raise ConflictException(
                        message=f"Version conflict: expected {existing.version}, got {request.version}"
                    )
                request.update_entity(existing)
                existing.version += 1
                vital = await self.vital_repo.update(existing)
                created = False
            else:
                # INSERT — 내부 PK로 엔티티 생성
                vital = request.to_entity(patient.id)
                vital = await self.vital_repo.create(vital)
                created = True

            return VitalUpsertResponse.from_entity(vital, patient), created
        except AppException:
            raise
        except Exception as e:
            logging.exception(f"Failed to upsert vital: {request.patient_external_id} - {str(e)}")
            raise ServerException(message="Failed to upsert vital")
