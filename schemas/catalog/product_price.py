# schemas/catalog/product_price.py
from datetime import datetime
from typing import Optional, List, Dict
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


from models import PriceType
from models import UserStatus


class ProductPriceBase(BaseModel):
    """Schema de bază pentru prețuri."""
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="MDL", pattern=r'^[A-Z]{3}$')


class ProductPriceCreate(ProductPriceBase):
    """Schema pentru setare preț individual."""
    product_id: int = Field(..., gt=0)
    price_type: PriceType


class ProductPriceBulkCreate(BaseModel):
    """Schema pentru setare toate prețurile unui produs."""
    product_id: int = Field(..., gt=0)
    anonim: Decimal = Field(..., gt=0, decimal_places=2)
    user: Decimal = Field(..., gt=0, decimal_places=2)
    instalator: Decimal = Field(..., gt=0, decimal_places=2)
    pro: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="MDL", pattern=r'^[A-Z]{3}$')

    @model_validator(mode='after')
    def validate_price_hierarchy(self):
        """Validează că prețurile sunt în ordine descrescătoare."""
        if not (self.anonim >= self.user >= self.instalator >= self.pro):
            raise ValueError('Prețurile trebuie să fie: anonim >= user >= instalator >= pro')
        return self


class ProductPriceUpdate(BaseModel):
    """Schema pentru actualizare preț."""
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)


class ProductPriceResponse(ProductPriceBase):
    """Schema pentru răspuns preț."""
    id: int
    product_id: int
    price_type: PriceType
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class ProductPricesForUser(BaseModel):
    """Schema pentru prețuri vizibile unui user specific."""
    product_id: int
    user_status: UserStatus
    current_price: Decimal
    current_price_type: PriceType
    visible_prices: Dict[str, Decimal]
    currency: str = "MDL"

    @model_validator(mode='after')
    def validate_visible_prices(self):
        """Verifică că sunt afișate doar prețurile permise."""
        allowed_prices = {
            UserStatus.ANONIM: ['anonim'],
            UserStatus.USER: ['anonim', 'user'],
            UserStatus.INSTALATOR: ['anonim', 'user', 'instalator'],
            UserStatus.PRO: ['anonim', 'user', 'instalator', 'pro']
        }

        expected_keys = set(allowed_prices.get(self.user_status, ['anonim']))
        actual_keys = set(self.visible_prices.keys())

        if expected_keys != actual_keys:
            raise ValueError(f'Prețuri incorecte pentru status {self.user_status.value}')

        return self


class ProductWithPrices(BaseModel):
    """Schema pentru produs cu toate prețurile sale."""
    product_id: int
    product_name: str
    sku: str
    prices: Dict[str, Decimal]
    currency: str = "MDL"

    model_config = ConfigDict(from_attributes=True)