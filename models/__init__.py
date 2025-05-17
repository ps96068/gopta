import logging
from typing import List, Dict, Union, Any

logger = logging.getLogger(__name__)

from .blog import *
from .catalog import *
from .marketing import *
from .sale import *
from .user import *



# models/__init__.py


class ListenerRegistrationError(Exception):

    def __init__(self, failed_modules: List[str]):
        self.failed_modules = failed_modules
        message = f"Inregistrarea listener-ilor a esuat pentru: {', '.join(failed_modules)}"
        super().__init__(message)


def register_all_model_listeners(raise_on_error: bool = True) -> Union[bool, Dict[str, Any]]:
    """
    Register all listeners for the models.
    """
    print("<register_all_model_listeners>")

    from .blog.signals import register_all_blog_listeners, get_blog_listeners_status
    from .catalog.signals import register_all_catalog_listeners
    from .marketing.signals import register_all_marketing_listeners
    from .sale.signals import register_all_sale_listeners
    from .user.signals import register_all_user_listeners

    results: Dict[str, bool] = {}
    failed_modules: List[str] = []

    # Register "blog" listeners
    try:
        results['blog'] = register_all_blog_listeners()
        print(f"BLOG = {results['blog']}")
        if not results['blog']:
            failed_modules.append('blog')
            logger.error("Failed to register blog listeners.")
    except Exception as e:
        failed_modules.append('blog')
        results['blog'] = False
        logger.error(f"Exception occurred while registering blog listeners: {e}")

    # Register "catalog" listeners
    try:
        results['catalog'] = register_all_catalog_listeners()
        print(f"CATALOG = {results['catalog']}")
        if not results['catalog']:
            failed_modules.append('catalog')
            logger.error("Failed to register catalog listeners.")
    except Exception as e:
        failed_modules.append('catalog')
        results['catalog'] = False
        logger.error(f"Exception occurred while registering catalog listeners: {e}")

    # Register "marketing" listeners
    try:
        results['marketing'] = register_all_marketing_listeners()
        print(f"MARKETING = {results['marketing']}")
        if not results['marketing']:
            failed_modules.append('marketing')
            logger.error("Failed to register marketing listeners.")
    except Exception as e:
        failed_modules.append('marketing')
        results['marketing'] = False
        logger.error(f"Exception occurred while registering marketing listeners: {e}")

    # Register "sale" listeners
    try:
        results['sale'] = register_all_sale_listeners()
        print(f"SALE = {results['sale']}")
        if not results['sale']:
            failed_modules.append('sale')
            logger.error("Failed to register sale listeners.")
    except Exception as e:
        failed_modules.append('sale')
        results['sale'] = False
        logger.error(f"Exception occurred while registering sale listeners: {e}")

    # Register "user" listeners
    try:
        results['user'] = register_all_user_listeners()
        print(f"USER = {results['user']}")
        if not results['user']:
            failed_modules.append('user')
            logger.error("Failed to register user listeners.")
    except Exception as e:
        failed_modules.append('user')
        results['user'] = False
        logger.error(f"Exception occurred while registering user listeners: {e}")




    results['success'] = len(failed_modules) == 0

    if results['success']:
        logger.info("All model listeners registered successfully.")
    else:
        logger.error(f"Some model listeners failed to register: {', '.join(failed_modules)}")


    if not results['success'] and raise_on_error:
        raise ListenerRegistrationError(failed_modules)

    return True if (raise_on_error and results['success']) else results


__all__ = [
    'Post',
    'PostImage',
    'PostEditHistory',
    'Category',
    'Product',
    'ProductImage',
    'ProductPrice',
    'ProductPriceHistory',
    'PriceType',
    'UserRequest',
    "RequestTypeEnum",
    "UserActivity",
    "UserInteraction",
    'InteractionAction',
    'InteractionTargetType',
    'Order',
    'OrderStatus',
    'OrderItem',
    'OrderStatusHistory',
    'Client',
    'ClientStatus',
    'Staff',
    'StaffRole',
    # 'register_all_model_listeners',
    # 'ListenerRegistrationError',
]