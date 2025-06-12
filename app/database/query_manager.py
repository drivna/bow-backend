from typing import List, Dict, Sequence, TypeVar, Type, Any, Optional, Union, Tuple
from loguru import logger
import sqlalchemy.exc
from sqlalchemy import func, update, and_, Subquery
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.expression import ColumnElement, BinaryExpression, UnaryExpression, CTE
from app.database.database_engine import DatabaseEngine
from app.database.models.base import Base

database_engine = DatabaseEngine.create_mysql_db_engine()
from .models.user import UserModel  # noqa: F401

Base.metadata.create_all(database_engine)

T = TypeVar("T")


def insert_single_object(db_object: Any) -> None:
    with Session(database_engine) as session:
        try:
            session.merge(db_object)
            session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            logger.error(f"Error in inserting object to database. {e.args}")
            raise e


def query_by_id(model: Type[T], object_id: str) -> T:
    with Session(database_engine) as session:
        try:
            result = session.query(model).filter(model.id == object_id).one_or_none()  # type: ignore[attr-defined]
            value = result

            session.expunge_all()
            session.commit()

        except Exception as e:
            raise RuntimeError(f"error in fetching object for id = {object_id}. Error = {e.args}")

    if value is None:
        raise ValueError(f"No {model._sa_class_manager.class_.__name__} found for id = {object_id}")  # type: ignore[attr-defined]

    return value


def query_with_filter(
    filters: Union[ColumnElement[bool], BinaryExpression[bool]],
    model: Type[T],
    order_by: Optional[UnaryExpression[Any]] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    is_dict_response: bool = False,
) -> List[T]:
    values = []
    with Session(database_engine) as session:
        try:
            query = session.query(model).filter(filters).order_by(order_by)

            if limit:
                query = query.limit(limit)

            if offset:
                query = query.offset(offset)

            results = query.all()

            for result_row in results:
                if is_dict_response is True:
                    values.append(result_row._asdict())  # type: ignore[attr-defined]
                else:
                    values.append(result_row)

        except Exception as e:
            logger.error(f"Error in reading objects from database. {e.args}")
            raise e

    return values


def update_single_object(model: Type[T], updated_object: T) -> T:
    with Session(database_engine) as session:
        try:
            database_object = session.query(model).filter(and_(model.id == updated_object.id)).one_or_none()  # type: ignore[attr-defined]

            if database_object is None:
                raise ValueError(f"No object found for model = {model} with id = {updated_object.id}")  # type: ignore[attr-defined]

            object_attributes = get_attributes_of_object(updated_object)

            for attribute in object_attributes:
                if hasattr(updated_object, attribute):
                    setattr(database_object, attribute, getattr(updated_object, attribute))

            session.commit()
        except Exception as e:
            logger.error(f"Error in updating object in database. {e.args}")
            raise e

    return query_by_id(model=model, object_id=updated_object.id)  # type: ignore[attr-defined]


def query_one_with_filter(
    filters: Union[ColumnElement[bool], BinaryExpression[bool]], model: Type[T]
) -> Optional[T]:
    with Session(database_engine) as session:
        try:
            result = session.query(model).filter(filters).one_or_none()
            value = result

            session.expunge_all()
            session.commit()

        except Exception as e:
            logger.error(
                f"No object found in database for model={model} and filter={filter}. Error = {e.args}"
            )

            return None

    return value


def query_all_in_model(
    model: Type[T],
) -> List[T]:
    values = []
    with Session(database_engine) as session:
        try:
            query = session.query(model)
            results = query.all()

            for result_row in results:
                values.append(result_row)

        except Exception as e:
            logger.error(f"Error in reading objects from database. {e.args}")
            raise e

    return values


def get_attributes_of_object(obj: T) -> List[str]:
    attributes: List[str] = [
        attr for attr in dir(obj) if not callable(getattr(obj, attr)) and not attr.startswith("_")
    ]
    return attributes


def handle_version_mismatch_during_update(database_object: T, updated_object: T) -> None:
    # logger.error(
    #     f" Version mismatch: object_id = {updated_object.id},"  # type: ignore
    #     f" version_from_database = {database_object.version}"
    #     f", current_version = {updated_object.version}",
    #     exc_info=True,
    # )
    pass


def query_count_with_filter(
    filters: Union[ColumnElement[bool], BinaryExpression[bool]],
    model: Type[T],
    order_by: Optional[UnaryExpression[Any]] = None,
) -> int:
    count: int = 0
    with Session(database_engine) as session:
        try:
            query = session.query(model).filter(filters).order_by(order_by)

            count = query.count()
        except Exception as e:
            logger.error(f"Error in counting objects from database. {e.args}")
            raise e

    return count


def query_with_filter_and_order(
    filters: Union[ColumnElement[bool], BinaryExpression[bool]],
    model: Type[T],
    order_by: Optional[UnaryExpression[Any]] = None,
    limit: Optional[int] = None,
) -> List[T]:
    values = []
    with Session(database_engine) as session:
        try:
            # if environment == "PROD": #TODO: Later
            #     session.execute(text("SET sort_buffer_size = 2 * 1024 * 1024;"))
            results = session.query(model).order_by(order_by).filter(filters).limit(limit).all()
            for result_row in results:
                values.append(result_row)

            session.expunge_all()
            session.commit()

        except Exception as e:
            logger.error(f"Error in reading objects from database. {e.args}")
            raise e

    return values


def query_with_filter_and_group_by(
    filters: Union[ColumnElement[bool], BinaryExpression[bool]],
    model: Any,
    group_by: Optional[Tuple[Optional[InstrumentedAttribute[Any]], ...]] = None,
    order_by: Optional[UnaryExpression[Any]] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Dict[Any, Any]]:
    values = []
    with Session(database_engine) as session:
        try:
            results = session.query(*model).filter(filters)

            if group_by is not None:
                results = results.group_by(*group_by)

            if limit:
                results = results.limit(limit)

            if offset:
                results = results.offset(offset)

            if order_by is not None:
                results = results.order_by(order_by)

            for result_row in results:
                values.append(result_row._asdict())

            session.expunge_all()
            session.commit()

        except Exception as e:
            logger.error(f"Error in reading objects from database. {e.args}")
            raise e

    return values


def query_count_with_filter_and_group_by(
    filters: Union[ColumnElement[bool], BinaryExpression[bool]],
    model: Any,
    group_by: Optional[Tuple[Optional[InstrumentedAttribute[Any]], ...]] = None,
) -> int:
    count: int = 0
    with Session(database_engine) as session:
        try:
            results = session.query(*model).filter(filters)

            if group_by is not None:
                results = results.group_by(*group_by)

            count = results.count()

            session.expunge_all()
            session.commit()

        except Exception as e:
            logger.error(f"Error in reading objects from database. {e.args}")
            raise e

    return count


# PSA - Apparently a decision has been taken to deprecate this method
# Beware - PR may get rejected if this method is used in your code
# Check with reviewer before using
def execute_statement(statement: Any) -> None:
    logger.info("executing statement")
    with Session(database_engine) as session:
        try:
            session.execute(statement)
            session.commit()
            logger.info("executed statement")
        except Exception as e:
            logger.error(f"Error in executing statement = {statement}. Error = {e.args}")
            raise e


def execute_statements(statements: List[Any]) -> None:
    with Session(database_engine) as session:
        try:
            for statement in statements:
                session.execute(statement)

            session.commit()
        except Exception as e:
            logger.error(f"Error in executing statement = {statement}. Error = {e.args}")
            raise e


def get_first_row_by_partition_and_order(
    model: Any,
    filters: Union[ColumnElement[bool], BinaryExpression[bool]],
    partition_by: Any,
    order_by: Optional[UnaryExpression[Any]] = None,
) -> List[Dict[Any, Any]]:
    values = []
    with Session(database_engine) as session:
        try:
            subquery = (
                session.query(
                    *model,
                    func.row_number()
                    .over(partition_by=(partition_by), order_by=order_by)  # type: ignore[no-untyped-call]
                    .label("row_num"),
                )
                .filter(filters)
                .subquery()
            )

            results = session.query(*subquery.c).filter(subquery.c.row_num == 1).all()

            for result_row in results:
                values.append(result_row._asdict())

            session.expunge_all()
            session.commit()

        except Exception as e:
            logger.error(f"Error in reading objects from database. {e.args}")
            raise e

    return values


def query_count_with_join_filter(
    model: Any,
    join: Any,
    isouter: bool,
    filters: Union[ColumnElement[bool], BinaryExpression[bool]],
    group_by: Optional[Tuple[InstrumentedAttribute[str]]] = None,
    aggregate_filters: Optional[Union[ColumnElement[bool], BinaryExpression[bool]]] = None,
) -> int:
    count: int = 0
    with Session(database_engine) as session:
        try:
            results = session.query(*model).join(*join, isouter=isouter, full=False).filter(filters)

            if group_by is not None:
                results = results.group_by(*group_by)

            if aggregate_filters is not None:
                results = results.having(aggregate_filters)

            count = results.count()

            session.expunge_all()
            session.commit()

        except Exception as e:
            logger.error(f"Error in reading objects from database. {e.args}")
            raise e

    return count


def create_subquery(model: Any, filters: Any) -> Optional[Subquery]:
    subquery: Optional[Subquery] = None
    with Session(database_engine) as session:
        try:
            subquery = session.query(model).filter(filters).subquery()
        except Exception as e:
            logger.error(f"Error in reading objects from database. {e.args}")
            raise e

    return subquery


def create_subquery_with_columns(
    model: Any,
    filters: Optional[Any] = None,
    group_by: Optional[Any] = None,
    limit: Optional[int] = None,
    order_by: Optional[Sequence[UnaryExpression[Any]]] = None,
) -> Optional[Subquery]:
    subquery: Subquery
    with Session(database_engine) as session:
        try:
            # Create the subquery
            result = session.query(*model)

            if filters is not None:
                result = result.filter(filters)

            if group_by is not None:
                if isinstance(group_by, tuple):
                    result = result.group_by(*group_by)
                else:
                    result = result.group_by(group_by)

            if order_by is not None:
                result = result.order_by(*order_by)

            if limit is not None:
                result = result.limit(limit)

            subquery = result.subquery()

        except Exception as e:
            logger.error(f"Error in creating subquery: {e}")
            raise e

    return subquery


# cte = common table expression (i.e. enables WITH mysql clause)
def create_cte_with_columns(
    model: Any,
    join: Optional[Any] = None,
    isouter: Optional[bool] = False,
    filters: Optional[Any] = None,
    group_by: Optional[Any] = None,
    limit: Optional[int] = None,
    order_by: Optional[Sequence[UnaryExpression[Any]]] = None,
    cte_name: Optional[str] = None,
    select_from: Optional[Any] = None,
) -> Optional[CTE]:
    cte: CTE
    with Session(database_engine) as session:
        try:
            # Create the cte
            result = session.query(*model)

            if select_from is not None:
                result = result.select_from(select_from)

            if join is not None and isinstance(join, list):
                for each_join in join:
                    result = result.join(each_join[0], each_join[1])
            elif join is not None:
                result = result.join(*join, isouter=isouter, full=False)

            if filters is not None:
                result = result.filter(filters)

            if group_by is not None:
                result = result.group_by(group_by)

            if order_by is not None:
                result = result.order_by(*order_by)

            if limit is not None:
                result = result.limit(limit)

            cte = result.cte(name=cte_name)

        except Exception as e:
            logger.error(f"Error in creating cte: {e}")
            raise e

    return cte


def query_with_join_and_filter(
    model: Any,
    join: Any,
    isouter: bool,
    filters: Union[ColumnElement[bool], BinaryExpression[bool]],
    group_by: Optional[Tuple[InstrumentedAttribute[str]]] = None,
    aggregate_filters: Optional[Union[ColumnElement[bool], BinaryExpression[bool]]] = None,
    order_by: Optional[Sequence[UnaryExpression[Any]]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    is_dict_response: bool = True,
) -> List[Dict[Any, Any]]:
    values = []
    with Session(database_engine) as session:
        try:
            results = session.query(*model)
            if isinstance(join, list):
                for each_join in join:
                    results = results.join(each_join[0], each_join[1])
            else:
                results = results.join(*join, isouter=isouter, full=False)
            results = results.filter(filters)

            if aggregate_filters is not None:
                results = results.having(aggregate_filters)

            if group_by is not None:
                results = results.group_by(*group_by)

            if order_by is not None:
                results = results.order_by(*order_by)

            if limit is not None:
                results = results.limit(limit)

            if offset is not None:
                results = results.offset(offset)

            results = results.all()

            for result_row in results:
                if is_dict_response:
                    values.append(result_row._asdict())
                else:
                    values.append(result_row)

            session.expunge_all()
            session.commit()

        except Exception as e:
            logger.error(f"Error in reading objects from database. {e.args}")
            raise e

    return values


# mysql specific method
def upsert_data(data: List[T], model: Type[T]) -> Any:
    if len(data) == 0:
        return

    data_dicts = []
    for row in data:
        row_dict = row.__dict__
        del row_dict["_sa_instance_state"]

        data_dicts.append(row_dict)

    query = insert(model).values(data_dicts)
    update_dict = {x.name: x for x in query.inserted}
    upsert_query = query.on_duplicate_key_update(update_dict)

    return execute_statement(upsert_query)


def update_objects(
    model: Type[T],
    filters: Union[ColumnElement[bool], BinaryExpression[bool]],
    updates: Dict[str, Any],
) -> int:
    with Session(database_engine) as session:
        try:
            statement = update(model).where(filters).values(updates)
            result = session.execute(statement)
            session.commit()

            return result.rowcount
        except Exception as e:
            logger.error(f"Error in updating objects in the database. {e.args}")
            raise e


def get_count_of_docs(
    model: Any,
    filters: Union[ColumnElement[bool], BinaryExpression[bool]],
) -> int:
    result = 0
    with Session(database_engine) as session:
        try:
            result = session.query(model).filter(filters).count()
        except Exception as e:
            logger.error(f"Error in reading objects from database. {e.args}")
            raise e

    return result


def delete_object_by_id(model: Type[T], object_id: str) -> int:
    with Session(database_engine) as session:
        try:
            result = session.query(model).filter(model.id == object_id).delete()  # type: ignore[attr-defined]
            session.commit()
        except Exception as e:
            logger.error(f"Error in deleting objects from database. {e.args}")
            raise e

    return result


def increment_column_value(model: Type[T], object_id: str, column_name: str, value: float) -> T:
    with Session(database_engine) as session:
        try:
            database_object = session.query(model).filter_by(id=object_id).with_for_update().one()

            if database_object is None:
                raise ValueError(f"No object found for model = {model} with id = {object_id}")

            # type cast value into whatever the type of column is
            value = type(getattr(database_object, column_name))(value)

            # Increment the value
            setattr(database_object, column_name, getattr(database_object, column_name) + value)

            session.commit()

        except Exception as e:
            # Rollback the transaction in case of an error
            session.rollback()
            raise ValueError(f"Error occurred: {e}")

        finally:
            # Close the session
            session.close()

    return query_by_id(model=model, object_id=object_id)
