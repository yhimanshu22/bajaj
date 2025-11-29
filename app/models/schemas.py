from pydantic import BaseModel, Field
from typing import List, Optional


class BillItem(BaseModel):
    item_name: str = Field(..., description="Name/description of the billed item")
    item_amount: float = Field(..., ge=0, description="Total cost for this item")
    item_rate: float = Field(..., ge=0, description="Rate per unit")
    item_quantity: float = Field(..., ge=0, description="Quantity of the item")


class PageLineItems(BaseModel):
    page_no: str = Field(..., description="Page number as string")
    page_type: str = Field(..., description="Bill Detail | Final Bill | Pharmacy")
    bill_items: List[BillItem] = Field(..., description="List of extracted bill items")



class ExtractionData(BaseModel):
    pagewise_line_items: List[PageLineItems]
    total_item_count: int = Field(..., ge=0)


class BillExtractionResponse(BaseModel):
    is_success: bool
    data: ExtractionData


class BillExtractionRequest(BaseModel):
    document: str = Field(..., description="URL of the document to extract")
