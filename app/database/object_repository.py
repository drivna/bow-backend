from datetime import datetime
from typing import TypeVar, Type, Optional, List, Any
from loguru import logger
from sqlalchemy import and_

from app.utils.string_util import StringUtils

# from tests.test_utils.string_utils import StringUtils

from ..database import query_manager


class ObjectRepository:
    """
    contains functions that are common across all models
    """

    T = TypeVar("T")

    @classmethod
    def get_updation_id(cls) -> str:
        suffix: str = StringUtils.generate_random_string(length=6)
        current_date: int = int(datetime.now().timestamp())

        identifier: str = str(suffix) + str(current_date)

        return f"updation_{StringUtils.calculate_sha256_hash_first_ten(identifier)}"

    @classmethod
    def create_archive_entry_for_insert(
        cls,
        object_to_be_inserted: T,
        company_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        if not hasattr(object_to_be_inserted, "archive_table"):
            return

        try:
            object_attributes = query_manager.get_attributes_of_object(object_to_be_inserted)

            if company_id is None:
                try:
                    company_id = object_to_be_inserted.company_id  # type: ignore
                    if company_id is None:
                        logger.info(
                            f"No company found for object ID = {object_to_be_inserted.id} for creating archive entry"  # type: ignore
                        )

                        return

                except Exception as e:
                    logger.error(e.args[0])

            updation_id: str = cls.get_updation_id()
            for attribute in object_attributes:
                if hasattr(object_to_be_inserted, attribute) and attribute not in [
                    "updated_at",
                    "metadata",
                    "registry",
                ]:
                    archive_object = object_to_be_inserted.archive_table(
                        reference=object_to_be_inserted.id,  # type: ignore
                        old_value=None,
                        new_value=str(getattr(object_to_be_inserted, attribute)),
                        field_name=str(attribute),
                        company_id=company_id,
                        is_insertion=True,
                        updation_id=updation_id,
                        updated_by=user_id,
                    )

                    query_manager.insert_single_object(archive_object)
        except Exception as e:
            logger.info(
                f"Unable to create archive entry for id = {object_to_be_inserted.id}, model = {type(object_to_be_inserted)}, {e.args[0]}"  # type: ignore
            )

    @classmethod
    def create_archive_entry(cls, updated_object: T, company_id: Optional[str] = None, user_id: Optional[str] = None):  # type: ignore
        try:
            current_object = cls.get_object_by_id(type(updated_object), updated_object.id)  # type: ignore

            if company_id is None:
                try:
                    company_id = updated_object.company_id  # type: ignore
                    if company_id is None:
                        logger.info(
                            f"No company found for object ID = {updated_object.id} for creating archive entry"  # type: ignore
                        )
                        return
                except Exception as e:
                    logger.error(e.args[0])

            object_attributes = query_manager.get_attributes_of_object(updated_object)
            updation_id: str = cls.get_updation_id()

            for attribute in object_attributes:
                if (
                    hasattr(updated_object, attribute)
                    and hasattr(current_object, attribute)
                    and attribute != "updated_at"
                ):
                    if getattr(updated_object, attribute) != getattr(current_object, attribute):
                        archive_object = updated_object.archive_table(  # type: ignore
                            reference=updated_object.id,  # type: ignore
                            old_value=str(getattr(current_object, attribute)),
                            new_value=str(getattr(updated_object, attribute)),
                            field_name=str(attribute),
                            company_id=company_id,
                            updation_id=updation_id,
                            updated_by=user_id,
                        )

                        query_manager.insert_single_object(archive_object)
        except Exception as e:
            logger.info(
                f"Unable to create archive entry for id = {updated_object.id}, model = {type(updated_object)}, {e.args[0]}"  # type: ignore
            )

    @classmethod
    def update_single_object(cls, object_to_be_updated: T, user_id: Optional[str] = None) -> T:
        """
        :param object_to_be_updated:
        :param user_id:
        :return:

        updates the object with same ID in database and returns the updated object
        """

        cls.create_archive_entry(object_to_be_updated, user_id=user_id)

        if hasattr(object_to_be_updated, "updated_at"):
            current_time: datetime = datetime.now()
            setattr(object_to_be_updated, "updated_at", current_time)

        return query_manager.update_single_object(type(object_to_be_updated), object_to_be_updated)

    @classmethod
    def insert_single_object(cls, object_to_be_inserted: T, user_id: Optional[str] = None) -> T:
        """
        :param object_to_be_inserted:
        :return:

        """
        try:
            existing_object = cls.get_object_by_id(
                model=type(object_to_be_inserted), object_id=object_to_be_inserted.id  # type: ignore
            )

            if existing_object is not None:
                cls.update_single_object(object_to_be_inserted, user_id=user_id)

        except ValueError:  # object does not exist already
            # add new object to database
            query_manager.insert_single_object(object_to_be_inserted)

            # create entry for archive table
            cls.create_archive_entry_for_insert(object_to_be_inserted, user_id=user_id)

        return cls.get_object_by_id(
            model=type(object_to_be_inserted), object_id=object_to_be_inserted.id  # type: ignore
        )

    @classmethod
    def get_object_by_id(cls, model: Type[T], object_id: str) -> T:
        return query_manager.query_by_id(model=model, object_id=object_id)

    @classmethod
    def get_objects_by_ids(cls, model: Type[T], object_ids: List[str]) -> List[T]:
        objects: List[Any] = query_manager.query_with_filter(
            model=model, filters=and_(getattr(model, "id").in_(object_ids))
        )

        if len(objects) != len(object_ids):
            raise RuntimeError("Failed to fetch objects, found invalid object ids in the list")

        return objects

    @classmethod
    def delete_object_by_id(cls, model: Type[T], object_id: str) -> int:
        return query_manager.delete_object_by_id(model=model, object_id=object_id)
