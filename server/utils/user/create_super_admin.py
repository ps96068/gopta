import logging

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select


from database import async_session_maker, engine, cfg_token
from models import Staff, StaffRole
from server.utils.user.password_and_hash import get_hashed_password


logger = logging.getLogger(__name__)


# admin_phone = cfg_token()['admin_phone']
# admin_email = cfg_token()['admin_email']

# admin_id = cfg_token()['admin_id']
# admin_user = cfg_token()['admin_user']





# admin_pass = cfg_token()['admin_password']
# hash_admin_pass = get_hashed_password(admin_pass)


# company_name = cfg_token()['company']


staffs_data = [
    {
        'telegram_id': cfg_token()['admin_tg_id'],
        'username': cfg_token()['admin_user'],
        'phone_number': cfg_token()['admin_phone'],
        'password': get_hashed_password(cfg_token()['admin_password']),
        'email': cfg_token()['admin_email'],
        'is_active': True,
        'role': StaffRole.super_admin,
    },
    {
        'telegram_id': cfg_token()['manager_tg_id'],
        'username': cfg_token()['manager_user'],
        'phone_number': cfg_token()['manager_phone'],
        'password': get_hashed_password(cfg_token()['manager_password']),
        'email': cfg_token()['manager_email'],
        'is_active': True,
        'role': StaffRole.manager,
    },
    {
        'telegram_id': cfg_token()['supervisor_tg_id'],
        'username': cfg_token()['supervisor_user'],
        'phone_number': cfg_token()['supervisor_phone'],
        'password': get_hashed_password(cfg_token()['supervisor_password']),
        'email': cfg_token()['supervisor_email'],
        'is_active': True,
        'role': StaffRole.supervisor,
    },
]


async def create_update_admin(session, admin_data, user = None):

    try:

        if user is None:
            user = Staff(
                telegram_id=admin_data['telegram_id'],
                username=admin_data['username'],
                phone_number=admin_data['phone_number'],
                password_hash=admin_data['password'],
                email=admin_data['email'],
                is_active=True,
                role=admin_data['role']
            )
            session.add(user)
            await session.commit()
            logger.info(f"Superuser {user.username} user created")
        else:
            user.telegram_id = admin_data['telegram_id']
            user.username = admin_data['username']
            user.phone_number = admin_data['phone_number']
            user.password_hash = admin_data['password']
            user.email = admin_data['email']
            user.is_active = True
            user.role = admin_data['role']
            await session.commit()
            logger.info(f"Superuser {user.username} updated")
            # return user

    except SQLAlchemyError as e:
        logger.error(f"Eroare SQLAlchemy în funcția create_update_admin(): {str(e)}")
        await session.rollback()
        raise
    return user



#
# async def create_update_company(session, company = None):
#
#     if company is None:
#         company = Company(
#             name=company_name,
#             address=company_name,
#             email=admins_data[0]['email'],
#             phone_number=admins_data[0]['phone_number'],
#             status=CompanyStatus.pro,
#         )
#         session.add(company)
#         await session.commit()
#         logger.warning("Zigzag company created")
#         return company.id
#     else:
#         company.name = company_name
#         company.address = company_name
#         company.email = admins_data[0]['email']
#         company.phone_number = admins_data[0]['phone_number']
#         company.status = CompanyStatus.pro
#         await session.commit()
#         logger.warning("Zigzag company updated")
#         return company.id


async def check_admin_data():
    try:
        async with async_session_maker() as session:

            existing_users = await session.execute(
                select(Staff).filter(Staff.username.in_([user['username'] for user in staffs_data]))
            )
            existing_users = {user.username: user for user in existing_users.scalars()}

            for staff_data in staffs_data:
                staff = existing_users.get(staff_data['username'])
                await create_update_admin(session=session, admin_data=staff_data, user=staff)





            # # Procesăm fiecare utilizator din lista staffs_data
            # for staff_data in staffs_data:
            #     # Verificăm existența utilizatorului în tabelul "users"
            #     staff_query = select(Staff).where(
            #         Staff.username == staff_data['username'],
            #         Staff.telegram_id == staff_data['telegram_id']
            #     )
            #     result_staff = await session.execute(staff_query)
            #     staff = result_staff.scalars().first()
            #
            #     if not staff:
            #         await create_update_admin(session=session, admin_data=staff_data)
            #     else:
            #         await create_update_admin(session=session, admin_data=staff_data, user=staff)


    except SQLAlchemyError as e:
        logger.error(f"Eroare SQLAlchemy în funcția check_admin_data(): {str(e)}")
        raise
    except Exception as e:
        logger.error(f"A intervenit o excepție: {e}")
        raise



async def startup():
    logger.info("Se verifică existența a utilizatorului super-administrator...")

    try:
        async with engine.connect() as conn:
            try:
                have_user_table = await conn.run_sync(
                    lambda sync_conn: inspect(sync_conn).has_table('staff')
                )
            except SQLAlchemyError as e:
                logger.error(f"Eroare în funcția startup(): {str(e)}")
                raise
    except Exception as e:
        logger.error(f"A intervenit o eroare în timpul conectării la baza de date: {e}")
        raise

    if have_user_table:
        await check_admin_data()
    else:
        raise RuntimeError("În baza de date nu există tabelele 'users' și 'companies'.")
