from pydantic import BaseModel
from typing import List, Optional

class BillItem(BaseModel):
    item_name: str
    item_amount: Optional[float] = 0.0
    item_rate: Optional[float] = 0.0
    item_quantity: Optional[float] = 0.0

class PageLineItems(BaseModel):
    page_no: str
    bill_items: List[BillItem]

class ExtractionData(BaseModel):
    pagewise_line_items: List[PageLineItems]
    total_item_count: int
    reconciled_amount: float

class BillExtractionResponse(BaseModel):
    is_success: bool
    data: ExtractionData
    flags: Optional[dict] = {}

class BillExtractionRequest(BaseModel):
    document: str
