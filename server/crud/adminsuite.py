import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import Staff
from database import async_session_maker


logger = logging.getLogger(__name__)


class AdminSuiteCRUD:
    model = Staff

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        print("find_one_or_none")

        print(f"find_one_or_none => **filter_by => {filter_by}")

        try:

            async with async_session_maker() as session:
                query = select(cls.model).filter_by(**filter_by)
                print(f"find_one_or_none => query => {query}")
                response = await session.execute(query)
                print(f"find_one_or_none => response => {response.__dict__}")
                # try:
                #     result = response.scalars().first()
                # except Exception as e:
                #     logger.error(f"Error getting first row: {e}")
                #     result = None
                #
                # if result is not None:
                #     print(f"Utilizatorul găsit: {result}")
                # else:
                #     print("Utilizatorul nu a fost găsit.")


                # for row in response:
                #     print(f"find_one_or_none => row => {row}")

                result = response.scalar_one_or_none()
                # print(f"AdminSuiteCRUD - resulte = {result}")
                return result

        except SQLAlchemyError as e:
            logger.error(f"Error fetching data: {e}")
        except Exception as e:
            logger.error(f"Error in find_one_or_none() function: {str(e)}")
            raise e

