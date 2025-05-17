import logging

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select


from database import async_session_maker, engine, cfg_token
from server.models import Company, CompanyStatus, User, UserRole, UserStatus
from server.utils.user.password_and_hash import get_hashed_password


logger = logging.getLogger(__name__)
company_name = cfg_token()['company']
admin_id = cfg_token()['admin_id']
admin_user = cfg_token()['admin_user']
admin_email = cfg_token()['admin_email']
admin_phone = cfg_token()['admin_phone']
admin_pass = cfg_token()['admin_password']
hash_admin_pass = get_hashed_password(admin_pass)


async def create_update_user(session, user = None, company_id: int = None):

    if user is None:
        user = User(
            telegram_id=admin_id,
            username=admin_user,
            phone_number=admin_phone,
            company_id=company_id,
            password_hash=hash_admin_pass,
            email=admin_email,
            is_active=True,
            role=UserRole.super_admin,
            status=UserStatus.company,
        )
        session.add(user)
        await session.commit()
        logger.warning("Superman user created")
        return user
    else:
        user.telegram_id = admin_id
        user.username = admin_user
        user.phone_number = admin_phone
        user.company_id = company_id
        user.password_hash = hash_admin_pass
        user.email = admin_email
        user.is_active = True
        user.role = UserRole.super_admin
        user.status = UserStatus.company
        session.add(user)
        await session.commit()
        logger.warning("Superman user updated")
        return user


async def create_update_company(session, company = None):

    if company is None:
        company = Company(
            name=company_name,
            address=company_name,
            email=admin_email,
            phone_number=admin_phone,
            status=CompanyStatus.pro,
        )
        session.add(company)
        await session.flush()
        company_id = company.id
        await session.commit()
        logger.warning("Zigzag company created")
        return company_id
    else:
        company.name = company_name
        company.address = company_name
        company.email = admin_email
        company.phone_number = admin_phone
        company.status = CompanyStatus.pro
        session.add(company)
        await session.flush()
        company_id = company.id
        await session.commit()
        logger.warning("Zigzag company updated")
        return company_id


async def check_admin_data():
    try:

        async with async_session_maker() as session:
            try:

                # Verificăm existența companiei "zigzag" în tabelul "companies"
                company_query = select(Company).where(Company.name == company_name)
                result_company = await session.execute(company_query)
                company = result_company.scalars().first()

                # Verificăm existența utilizatorului "superman" în tabelul "users"
                user_query = select(User).where(User.username == admin_user, User.telegram_id == admin_id)
                result_user = await session.execute(user_query)
                superman = result_user.scalars().first()


                if not company:
                    company_id = await create_update_company(session=session)
                else:
                    company_id = await create_update_company(session=session, company=company)

                if not superman:
                    await create_update_user(session=session, company_id=company_id)
                else:
                    await create_update_user(session=session, user=superman, company_id=company_id)

            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemyError in check_admin_data() function: {str(e)}")
                raise e

    except ImportError as e:
        logger.error(f"async_session_maker nu este importat corect sau modulul care conține async_session_maker nu este disponibil: {e}")
        return
    except Exception as e:
        logger.error(f"A intervenit exceptia: {e}")
        return


async def startup():
    logger.warning("Start checking supercompany and superuser ...")

    async with engine.connect() as conn:
        try:
            have_user_table = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table('users'))
            have_company_table = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table('companies'))
        except SQLAlchemyError as e:
            logger.error(f"Error in startup() function: {str(e)}")
            raise e

    if have_user_table and have_company_table:
        await check_admin_data()
    else:
        raise RuntimeError("In baza de date nu exsita tabelele Users si Companies.")



