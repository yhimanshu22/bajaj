import re
from typing import List, Dict, Any

def extract_information(ocr_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract line items and totals from OCR text using Regex and Heuristics.
    Returns data in the format required by the new schema.
    """
    pagewise_items = []
    total_items_count = 0
    grand_total = 0.0
    
    amount_pattern = r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'

    for result in ocr_results:
        page_text = result["text"]
        page_no = str(result["page"])
        lines = page_text.split('\n')
        
        bill_items = []
        
        for line in lines:
            if not line.strip():
                continue
                
            # Extract all numbers
            matches = re.findall(amount_pattern, line)
            numbers = []
            for m in matches:
                try:
                    val = float(m.replace(',', ''))
                    numbers.append(val)
                except ValueError:
                    pass
            
            # Logic: Look for Rate * Qty = Amount relationship
            found_item = False
            
            # Logic: Look for Rate * Qty = Amount relationship
            found_item = False
            
            # Strategy 0: Check last 3 non-zero numbers (Standard Case)
            # This is most reliable for clean OCR like Sample 2
            non_zero_numbers = [n for n in numbers if n > 0]
            if len(non_zero_numbers) >= 3:
                c = non_zero_numbers[-1] # Amount
                b = non_zero_numbers[-2] # Rate
                a = non_zero_numbers[-3] # Qty
                
                if abs(a * b - c) < 1.0 or abs(b * a - c) < 1.0:
                    bill_items.append(create_item(line, matches, a, b, c))
                    found_item = True
                    grand_total = max(grand_total, c)
            
            # Strategy 1: Find exact A * B = C match in any 3 numbers (preserving order)
            # Only if Strategy 0 failed
            if not found_item:
                n = len(numbers)
                if n >= 3:
                    for i in range(n-2):
                        for j in range(i+1, n-1):
                            for k in range(j+1, n):
                                a = numbers[i]
                                b = numbers[j]
                                c = numbers[k]
                                
                                # Check A * B = C
                                # Constraint: C should be reasonably large (avoid 2*2=4 in dates)
                                # Constraint: A (Qty) is usually integer-ish or small
                                if abs(a * b - c) < 1.0:
                                    # Heuristic to avoid false positives in dates (e.g. 20/11/2025)
                                    if c > 2000 and c < 2030: continue # Likely a year
                                    
                                    bill_items.append(create_item(line, matches, a, b, c))
                                    found_item = True
                                    grand_total = max(grand_total, c)
                                    break
                            if found_item: break
                        if found_item: break
            
            # Strategy 2: If Qty=1, look for A = B (Rate = Amount)
            if not found_item and n >= 2:
                for i in range(n-1):
                    for j in range(i+1, n):
                        a = numbers[i]
                        b = numbers[j]
                        
                        # Case: Qty=1, Rate=A, Amount=B -> A=B
                        # But wait, usually Qty is explicit 1.00
                        # If we see 1.00, A, B... and A=B?
                        # Or just 1.00, A... and A is Amount?
                        
                        # Sub-case: Explicit Qty=1
                        if abs(a - 1.0) < 0.1:
                            # Qty is 1. Assume B is Amount (and Rate).
                            # We accept this if B is the last number or looks like an amount
                            # To be safe, let's require B to be > 0
                            if b > 0:
                                bill_items.append(create_item(line, matches, 1.0, b, b))
                                found_item = True
                                grand_total = max(grand_total, b)
                                break
                        
                        # Sub-case: Implicit Qty=1 (Rate = Amount)
                        # Two identical numbers (e.g. 3300 ... 3300)
                        if abs(a - b) < 1.0 and a > 0:
                             # Assume Qty=1
                            bill_items.append(create_item(line, matches, 1.0, a, b))
                            found_item = True
                            grand_total = max(grand_total, b)
                            break
                    if found_item: break

            # Strategy 3: Handle "Garbage Amount" (e.g. 1.00, 90.00, 90100)
            # If we have 1.00 and X, and X is reasonable, but no match found.
            if not found_item and n >= 2:
                if abs(numbers[0] - 1.0) < 0.1:
                     # Qty = 1. Take the next number as Rate/Amount
                     # This fixes "cr 1.00 90.00 ... 90100"
                     qty = 1.0
                     rate = numbers[1]
                     amount = rate
                     bill_items.append(create_item(line, matches, qty, rate, amount))
                     found_item = True
                     grand_total = max(grand_total, amount)

            # Fallback: If line has "Total" and a number, update grand_total
            if not found_item and ("total" in line.lower() or "amount" in line.lower()) and numbers:
                grand_total = max(grand_total, max(numbers))
        
        if bill_items:
            pagewise_items.append({
                "page_no": page_no,
                "bill_items": bill_items
            })
            total_items_count += len(bill_items)
            
    # Reconcile total
    if total_items_count > 0:
        calculated_total = sum(item['item_amount'] for page in pagewise_items for item in page['bill_items'])
        # Trust calculated total if it's > 0, as OCR total might be wrong
        grand_total = calculated_total

    return {
        "pagewise_line_items": pagewise_items,
        "total_item_count": total_items_count,
        "reconciled_amount": grand_total
    }

def create_item(line, matches, qty, rate, amount):
    # Description cleanup
    desc = line
    for num_str in matches:
        desc = desc.replace(num_str, "")
    desc = re.sub(r'\s+', ' ', desc).strip()
    
    return {
        "item_name": desc,
        "item_amount": amount,
        "item_rate": rate,
        "item_quantity": qty
    }
