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
    def update_single_object(cls, object_to_be_updated: T, user_id: Optional[str] = None) -> T:
        """
        :param object_to_be_updated:
        :param user_id:
        :return:

        updates the object with same ID in database and returns the updated object
        """

        # cls.create_archive_entry(object_to_be_updated, user_id=user_id)

        if hasattr(object_to_be_updated, "updated_at"):
            current_time: datetime = datetime.now()
            setattr(object_to_be_updated, "updated_at", current_time)

        return query_manager.update_single_object(type(object_to_be_updated), object_to_be_updated)

    @classmethod
    def insert_single_object(
        cls,
        object_to_be_inserted: T,
        user_id: Optional[str] = None,
        without_upsert_call: bool = False,
    ) -> T:
        """
        :param object_to_be_inserted:
        :return:

        """
        try:
            existing_object = cls.get_object_by_id(
                model=type(object_to_be_inserted), object_id=object_to_be_inserted.id  # type: ignore
            )
            logger.info(f"Found existing object: {existing_object.id}")

            if existing_object is not None and not without_upsert_call:
                cls.update_single_object(object_to_be_inserted, user_id=user_id)

        except ValueError:  # object does not exist already
            # add new object to database
            query_manager.insert_single_object(object_to_be_inserted)

            # create entry for archive table
            # cls.create_archive_entry_for_insert(object_to_be_inserted, user_id=user_id)

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
